import sqlite3
import json
import pandas as pd

import plotly
import plotly.graph_objects as go

conn = sqlite3.connect("../flask_app/database.db")

radio_youtube_graphs = []

# The first graph: Does the season influences the artist's popularity? (only for artists
# having more than 9 tracks on top)
radio_audience = pd.read_sql_query('''
                                                SELECT
                                                    Artist,
                                                    Title,
                                                    Aud,
                                                    "Date"
                                                FROM "radio_charts_archive"
                                            ''', conn)

unique_tracks = radio_audience[['Artist', 'Title']].drop_duplicates()
track_counts = unique_tracks['Artist'].value_counts()
valid_artists = track_counts[track_counts >= 10].index
radio_audience = radio_audience[radio_audience['Artist'].isin(valid_artists)]

radio_audience['Date'] = pd.to_datetime(radio_audience['Date'])
radio_audience['Month'] = radio_audience['Date'].dt.month_name()
month_order = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']
radio_audience['Month'] = pd.Categorical(radio_audience['Month'], categories=month_order, ordered=True)

# We cycled through several years - it should be averaged
radio_audience_monthly_averages = (
    radio_audience.groupby(['Artist', 'Month'])['Aud']
    .mean()
    .reset_index()
)

# Filter out artists that were not in top for all 12 months
month_counts = radio_audience_monthly_averages.groupby('Artist')['Month'].nunique()
valid_artists = month_counts[month_counts == 12].index
monthly_avg_full_year = radio_audience_monthly_averages[radio_audience_monthly_averages['Artist'].isin(valid_artists)]

artists = radio_audience_monthly_averages['Artist'].unique()

radio_youtube_graphs.append(go.Figure())

for i, artist in enumerate(artists):
    artist_df = radio_audience_monthly_averages[radio_audience_monthly_averages['Artist'] == artist]
    radio_youtube_graphs[0].add_trace(go.Scatter(
        x=artist_df['Month'],
        y=artist_df['Aud'],
        name=artist,
        visible=(i == 0),
        mode='lines+markers'
    ))

dropdown_buttons = [
    dict(label=artist,
         method="update",
         args=[{"visible": [i == j for j in range(len(artists))]},
               {"title": f"Monthly Average Audience: {artist}"}])
    for i, artist in enumerate(artists)
]

radio_youtube_graphs[0].update_layout(
    updatemenus=[{
        "buttons": dropdown_buttons,
        "direction": "down",
        "showactive": True,
        "x": 0.8,
        "y": 1.15,
        "xanchor": "left",
        "yanchor": "top"
    }],
    title=f"Monthly Average Audience (in millions): {artists[0]}",
    xaxis_title="Month",
    yaxis_title="Average Audience",
    xaxis_tickangle=-45
)

radio_youtube1_json = json.dumps(radio_youtube_graphs[0], cls=plotly.utils.PlotlyJSONEncoder)

with open("../flask_app/static/figures/radio_youtube/radio_youtube1.json", "w") as f:
    f.write(radio_youtube1_json)

# The second graph: YouTube vs. Spotify - comparing the most popular 50 tracks on Spotify and YouTube
spotify_youtube_comparison = pd.read_sql_query('''
                                        SELECT
                                            s.Artist,
                                            s.Title,
                                            s.Total AS spotify_streams,
                                            y.Views AS youtube_views
                                        FROM (
                                            SELECT Artist, Title, Total
                                            FROM spotify_charts_daily
                                            ORDER BY Total DESC
                                            LIMIT 50
                                        ) s
                                        JOIN youtube_clips_overall y
                                            ON s.Artist = y.Artist AND s.Title = y.Title
                                    ''', conn)

# Some artist can have two clips on one popular track, we will choose the more popular one
spotify_youtube_comparison = (
    spotify_youtube_comparison
    .loc[spotify_youtube_comparison.groupby(['Artist', 'Title'])['youtube_views'].idxmax()]
    .reset_index(drop=True)
)

spotify_youtube_comparison['Track'] = spotify_youtube_comparison['Artist'] + ' — ' + spotify_youtube_comparison['Title']

radio_youtube_graphs.append(go.Figure(data=[
    go.Bar(
        name='Spotify Streams',
        x=spotify_youtube_comparison['Track'],
        y=spotify_youtube_comparison['spotify_streams'],
        hovertemplate='<b>Spotify: %{y:,d} streams</b><extra></extra>'
    ),
    go.Bar(
        name='YouTube Views',
        x=spotify_youtube_comparison['Track'],
        y=spotify_youtube_comparison['youtube_views'],
        hovertemplate='<b>YouTube: %{y:,d} views</b><extra></extra>'
    )
]))

radio_youtube_graphs[1].update_layout(
    title='Top Tracks: Spotify Streams vs YouTube Views',
    xaxis_title='Track',
    yaxis_title='Count',
    barmode='group',
    xaxis_tickangle=-45,
    height=600
)

radio_youtube2_json = json.dumps(radio_youtube_graphs[1], cls=plotly.utils.PlotlyJSONEncoder)

with open("../flask_app/static/figures/radio_youtube/radio_youtube2.json", "w") as f:
    f.write(radio_youtube2_json)

# The third graph: How actual some video is (ratio of yesterday views to the overall number of views at a particular
# time period (year))
youtube_overall = pd.read_sql_query('''
                                        SELECT 
                                            Artist,
                                                        Title,
                                                        Yesterday,
                                                        Views,
                                                        "Publication year"
                                                    FROM youtube_clips_overall
                                                ''', conn)

youtube_overall['yesterday_to_total'] = youtube_overall['Yesterday'] / youtube_overall['Views']
years = sorted(youtube_overall['Publication year'].unique())

radio_youtube_graphs.append(go.Figure())

for i, year in enumerate(years):
    year_table = youtube_overall[youtube_overall['Publication year'] == year].copy()
    year_table = year_table.sort_values('Views', ascending=False).head(10)
    year_table['Track'] = year_table['Artist'] + ' — ' + year_table['Title']
    year_table['Track'] = [val[:35] + '...' if isinstance(val, str) and len(val) >= 35
                           else val for val in year_table['Track'].values]

    radio_youtube_graphs[2].add_trace(go.Bar(
        x=year_table['Track'],
        y=year_table['Views'],
        name=f'Total Views {year}',
        marker_color='blue',
        visible=(i == 0),
        hovertemplate='%{x}<br>Total Views: %{y:,}<extra></extra>'
    ))

    radio_youtube_graphs[2].add_trace(go.Scatter(
        x=year_table['Track'],
        y=year_table['Yesterday'],
        name=f'Yesterday Views {year}',
        yaxis='y2',
        mode='lines+markers',
        marker=dict(color='orange'),
        visible=(i == 0),
        hovertemplate='%{x}<br>Yesterday Views: %{y:,}<extra></extra>'
    ))

buttons = []
for i, year in enumerate(years):
    visible = [False] * len(years) * 2
    visible[i*2] = True       # total views bar for year
    visible[i*2 + 1] = True   # yesterday views line for year

    buttons.append(dict(
        label=str(year),
        method='update',
        args=[{'visible': visible},
              {'title': f'Top 10 Videos in {year}'}]
    ))

radio_youtube_graphs[2].update_layout(
    title=f'Top 10 Videos in {years[0]}',
    xaxis_title='Video',
    yaxis=dict(
        title='Total Views',
        rangemode='tozero',
        showgrid=False,
    ),
    yaxis2=dict(
        title='Yesterday Views',
        overlaying='y',
        side='right',
        rangemode='tozero',
        showgrid=False,
    ),
    updatemenus=[dict(
        active=0,
        buttons=buttons,
        x=0.9,
        y=1.15,
        xanchor='left',
        yanchor='top'
    )],
    barmode='group',
    height=600,
    legend=dict(x=0.1, y=1.1, orientation='h'),
)

radio_youtube3_json = json.dumps(radio_youtube_graphs[2], cls=plotly.utils.PlotlyJSONEncoder)

with open("../flask_app/static/figures/radio_youtube/radio_youtube3.json", "w") as f:
    f.write(radio_youtube3_json)
