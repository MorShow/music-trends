import sqlite3
import json
import pandas as pd
import numpy as np
import scipy

import plotly
import plotly.express as px
import plotly.graph_objects as go

conn = sqlite3.connect("../flask_app/database.db")

spotify_graphs = []

# The first graph: The popularity of the artists in different regions
spotify_popularity_daily = pd.read_sql_query('''
                                                SELECT
                                                    t1.Artist,
                                                    t1.Region,
                                                    ROUND(t1.total_artist / t2.region_total, 6) AS popularity
                                                FROM (
                                                    SELECT
                                                        Artist,
                                                        Region,
                                                        ROUND(SUM(Total), 6) AS total_artist
                                                    FROM "spotify_charts_daily"
                                                    GROUP BY Artist, Region
                                                ) t1
                                                JOIN (
                                                    SELECT
                                                        Region,
                                                        ROUND(SUM(Total), 6) AS region_total
                                                    FROM "spotify_charts_daily"
                                                    GROUP BY Region
                                                ) t2 ON t1.Region = t2.Region
                                                ORDER BY t1.Region, popularity DESC
                                            ''', conn)

spotify_popularity_daily['log_popularity'] = np.log1p(spotify_popularity_daily['popularity'])
spotify_popularity_daily['z_score'] = (
    spotify_popularity_daily
    .groupby('Region')['log_popularity']
    .transform(scipy.stats.zscore)
)

x = np.linspace(-5, 25, 500)
y = 1 / (np.sqrt(2 * np.pi)) * np.exp(-0.5 * x**2)

curve = go.Scatter(
    x=x, y=y,
    name='Normal Distribution',
    line=dict(color='gray', dash='dash'),
    hoverinfo='skip'
)

regions = ['Global', 'United States', 'Slovakia']
region_traces = []

for region in regions:
    popularity_region = spotify_popularity_daily[spotify_popularity_daily['Region'] == region]

    scatter = go.Scatter(
        x=popularity_region['z_score'],
        y=[1 / (np.sqrt(2 * np.pi)) * np.exp(-0.5 * z**2) for z in popularity_region['z_score']],
        mode='markers',
        name=region,
        text=popularity_region['Artist'],
        hovertemplate='Artist: %{text}<br>Z-score: %{x:.2f}<extra></extra>',
        marker=dict(size=8),
        visible=(region == 'Global')
    )

    region_traces.append(scatter)

buttons = []
for i, region in enumerate(regions):
    visibility = [True] + [j == i for j in range(len(regions))]
    buttons.append(dict(
        label=region,
        method='update',
        args=[{'visible': visibility},
              {'title': f'Popularity (Z-score) Distribution — {region}'}]
    ))

spotify_graphs.append(go.Figure(data=[curve] + region_traces))

spotify_graphs[0].update_layout(
    title='Popularity (Z-score) Distribution — Global',
    updatemenus=[dict(
        buttons=buttons,
        x=0.9, xanchor='left',
        y=1.15, yanchor='top'
    )],
    xaxis_title='Z-Score',
    yaxis_title='Probability Density',
    template='simple_white',
    height=600
)

spotify1_json = json.dumps(spotify_graphs[0], cls=plotly.utils.PlotlyJSONEncoder)

with open("../flask_app/static/figures/spotify/spotify1.json", "w") as f:
    f.write(spotify1_json)

# The second graph: The share of each artist's track from the total number of streams
spotify_shares_daily = pd.read_sql_query('''
                                                SELECT
                                                    t1.Artist,
                                                    t1.Title,
                                                    total_track,
                                                    total_artist,
                                                    ROUND(CAST(total_track AS REAL) * 100 / total_artist, 6) AS track_artist_ratio
                                                FROM (
                                                    SELECT
                                                        Artist,
                                                        Title,
                                                        SUM(Total) AS total_track
                                                    FROM "spotify_charts_daily"
                                                    WHERE Region = 'Global'
                                                          AND Title <> ''
                                                    GROUP BY Artist, Title
                                                ) t1
                                                JOIN (
                                                    SELECT
                                                        Artist,
                                                        SUM(Total) AS total_artist
                                                    FROM "spotify_charts_daily"
                                                    WHERE Region = 'Global'
                                                    GROUP BY Artist
                                                    HAVING COUNT(Title) >= 10
                                                ) t2 ON t1.Artist = t2.Artist
                                                ORDER BY total_artist DESC, track_artist_ratio DESC
                                        ''', conn)

unique_artists = spotify_shares_daily['Artist'].unique()
spotify_graphs.append(go.Figure())
buttons = []

for i, artist in enumerate(unique_artists):
    artist_tracks = spotify_shares_daily[spotify_shares_daily['Artist'] == artist]

    tree = px.treemap(
        artist_tracks,
        path=[px.Constant(artist), 'Title'],
        values='track_artist_ratio',
        color='track_artist_ratio',
        color_continuous_scale='Blues'
    ).data[0]

    # TODO: show the titles when hover
    spotify_graphs[1].add_trace(tree)
    spotify_graphs[1].update_traces(hovertemplate='The share of the streams: %{value:.2f}%<extra></extra>')
    if i != 0:
        spotify_graphs[1].data[i].visible = False
    else:
        spotify_graphs[1].data[i].visible = True

    buttons.append(dict(
        label=artist,
        method='update',
        args=[{
            'visible': [j == i for j in range(len(unique_artists))],
            'title': f"Track Share for {artist}"
        }]
    ))

spotify_graphs[1].update_layout(
    title="Select an Artist",
    updatemenus=[
        dict(
            buttons=buttons,
            x=0.5,
            xanchor="center",
            y=1.1,
            yanchor="top",

        )
    ]
)

spotify_graphs[1].update_layout(
    margin=dict(t=100, l=25, r=25, b=25)
)

spotify2_json = json.dumps(spotify_graphs[1], cls=plotly.utils.PlotlyJSONEncoder)

with open("../flask_app/static/figures/spotify/spotify2.json", "w") as f:
    f.write(spotify2_json)

# The third graph: Which kind of tracks makes the artist popular the most (solo or feature)
spotify_streams_artist = pd.read_sql_query('''
                                            SELECT *
                                            FROM "spotify_artists"
                                           ''', conn)

spotify_graphs.append(go.Figure())
buttons = []

batch_size = 10
listener_types = ['As lead', 'Solo', 'As feature']
num_batches = 30

for i in range(num_batches):
    start = i * batch_size
    end = start + batch_size
    artists_batch = spotify_streams_artist.iloc[start:end]

    for kind in listener_types:
        spotify_graphs[2].add_trace(go.Bar(
            x=artists_batch['Artist'],
            y=artists_batch[kind],
            name=kind,
            visible=(i == 0),
            hovertemplate='<b>Artist: %{x}<br>Streams (in millions): %{y:.d}<br>Kind: ' + kind + ' </b><extra></extra>'
        ))

for i in range(num_batches):
    vis = [False] * (num_batches * len(listener_types))
    start_trace = i * len(listener_types)

    for j in range(len(listener_types)):
        vis[start_trace + j] = True

    buttons.append(dict(
        label=f'Top {i*batch_size + 1} - {min((i+1)*batch_size, len(spotify_streams_artist))} artists',
        method='update',
        args=[{'visible': vis},
              {'title': f'Listeners for artists {i*batch_size + 1} - {min((i+1)*batch_size, len(spotify_streams_artist))}'}]
    ))

spotify_graphs[2].update_layout(
    title='Select the artists',
    updatemenus=[dict(
        buttons=buttons,
        direction='down',
        showactive=True,
        x=0.5,
        xanchor='center',
        y=1.1,
        yanchor='top'
    )],
    barmode='group',
    xaxis_title='Artist',
    yaxis_title='Number of streams (in millions)',
    height=600,
    width=1100
)

spotify3_json = json.dumps(spotify_graphs[2], cls=plotly.utils.PlotlyJSONEncoder)

with open("../flask_app/static/figures/spotify/spotify3.json", "w") as f:
    f.write(spotify3_json)
