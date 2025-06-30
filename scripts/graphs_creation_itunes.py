import sqlite3
import json
import pandas as pd
import scipy
import numpy as np

import plotly
import plotly.express as px
import plotly.graph_objects as go

conn = sqlite3.connect("../flask_app/database.db")

itunes_graphs = []

# # The first graph: Timeline - how changed the rankings of the best albums in 2014?
# itunes_albums_daily = pd.read_sql_query('''
#                                                 SELECT
#                                                     Artist,
#                                                     Title,
#                                                     Pos,
#                                                     "Date"
#                                                 FROM "archive_albums"
#                                                 WHERE Service = "iTunes"
#                                                       AND Region = "Global"
#                                                       AND "Date" BETWEEN '2014-01-01' AND '2014-12-31'
#                                                       AND "Pts" > 15000
#                                             ''', conn)
#
# unique_titles = itunes_albums_daily['Title'].unique()
# itunes_graphs.append(go.Figure())
# buttons = []
#
# for i, title in enumerate(unique_titles):
#     album_df = itunes_albums_daily[itunes_albums_daily['Title'] == title]
#
#     pl = px.line(
#         album_df,
#         x='Date',
#         y='Pos'
#     ).data[0]
#
#     itunes_graphs[0].add_trace(pl)
#     itunes_graphs[0].update_traces(hovertemplate='Position: %{y}<br><extra></extra>')
#     if i != 0:
#         itunes_graphs[0].data[i].visible = False
#     else:
#         itunes_graphs[0].data[i].visible = True
#
#     buttons.append(dict(
#         label=album_df['Artist'].iloc[0] + ' - ' + title,
#         method='update',
#         args=[{
#             'visible': [j == i for j in range(len(unique_titles))],
#             'title': f"Track Share for {title}"
#         }]
#     ))
#
# itunes_graphs[0].update_layout(
#     title="Select an Album",
#     updatemenus=[
#         dict(
#             buttons=buttons,
#             x=0.5,
#             xanchor="center",
#             y=1.1,
#             yanchor="top"
#         )
#     ]
# )
#
# itunes_graphs[0].update_layout(
#     margin=dict(t=100, l=25, r=25, b=25),
#     yaxis=dict(
#             autorange='reversed',
#             tickmode='linear',  # Maybe we don`t need it
#             dtick=1
#     ),
#     xaxis=dict(
#         nticks=20
#     )
# )
#
# itunes1_json = json.dumps(itunes_graphs[0], cls=plotly.utils.PlotlyJSONEncoder)
#
# with open("../flask_app/static/figures/itunes/itunes1.json", "w") as f:
#     f.write(itunes1_json)
#
# # The second graph - comparison: top-10 tracks in US (by sales) - how Slovak assess them comparing to other countries?
# top_sales_ratings_itunes = pd.read_sql_query('''SELECT
#                                                     t1.Artist,
#                                                     t1.Title,
#                                                     t2.Slovakia,
#                                                     t2."United States",
#                                                     t2."United Kingdom",
#                                                     t2.France,
#                                                     t2.Germany,
#                                                     t2.Switzerland,
#                                                     t2.Japan,
#                                                     t2.Austria,
#                                                     t2.Spain,
#                                                     t2.Belgium
#                                                 FROM (SELECT
#                                                         Artist,
#                                                         Title
#                                                     FROM "itunes_cumulative_united_states"
#                                                     ORDER BY Popularity DESC
#                                                     LIMIT 15) t1
#                                                     JOIN
#                                                     (SELECT
#                                                         Artist,
#                                                         Title,
#                                                         ROUND(AVG(SK), 2) AS Slovakia,
#                                                         ROUND(AVG(US), 2) AS "United States",
#                                                         ROUND(AVG(UK), 2) AS "United Kingdom",
#                                                         ROUND(AVG(FR), 2) AS France,
#                                                         ROUND(AVG(DE), 2) AS Germany,
#                                                         ROUND(AVG(CH), 2) AS Switzerland,
#                                                         ROUND(AVG(JP), 2) AS Japan,
#                                                         ROUND(AVG(AU), 2) AS Austria,
#                                                         ROUND(AVG(ES), 2) AS Spain,
#                                                         ROUND(AVG(BE), 2) AS Belgium
#                                                     FROM "archive_songs"
#                                                     WHERE Service = "iTunes" AND Region = "Global"
#                                                     GROUP BY Artist, Title) t2
#                                                     ON t1.Artist = t2.Artist AND t1.Title = t2.Title
#                                             ''', conn)
#
# top_sales_ratings_itunes = pd.melt(
#      top_sales_ratings_itunes,
#      id_vars=['Artist', 'Title'],
#      var_name='Country',
#      value_name='Popularity'
# )
#
# titles = top_sales_ratings_itunes['Title'].unique()
# artists = {title: top_sales_ratings_itunes[top_sales_ratings_itunes['Title'] == title]['Artist'].values[0]
#            for title in titles}
#
# itunes_graphs.append(go.Figure())
#
# for title in titles:
#     track_table = top_sales_ratings_itunes[top_sales_ratings_itunes['Title'] == title]
#     slovakia_streams = track_table[track_table['Country'] == 'Slovakia']['Popularity'].values[0]
#     other_countries = track_table[track_table['Country'] != 'Slovakia']
#
#     bar = go.Bar(
#         x=other_countries['Country'],
#         y=other_countries['Popularity'],
#         name='Other countries',
#         visible=False
#     )
#
#     line = go.Scatter(
#         x=other_countries['Country'],
#         y=[slovakia_streams] * len(other_countries),
#         mode='lines',
#         name='Slovakia',
#         line=dict(color='red', dash='dash'),
#         visible=False
#     )
#
#     itunes_graphs[1].add_trace(bar)
#     itunes_graphs[1].add_trace(line)
#
# itunes_graphs[1].data[0].visible = True
# itunes_graphs[1].data[1].visible = True
#
# buttons = []
# for i, title in enumerate(titles):
#     visibility = [False] * len(itunes_graphs[1].data)
#     visibility[i * 2] = True
#     visibility[i * 2 + 1] = True
#
#     buttons.append(dict(
#         label=f'{artists[title]} - {title}',
#         method="update",
#         args=[{"visible": visibility},
#               {"title": f"Popularity of {artists[title]} - {title} by Country"}]
#     ))
#
# itunes_graphs[1].update_layout(
#     updatemenus=[dict(
#         active=0,
#         buttons=buttons,
#         x=0.875,
#         xanchor="center",
#         y=1.2,
#         yanchor="top"
#     )],
#     title=f"Popularity of {artists[titles[0]]} - {titles[0]} by Country",
#     yaxis_title="Popularity",
#     xaxis_title="Country",
#     height=500
# )
#
# itunes2_json = json.dumps(itunes_graphs[1], cls=plotly.utils.PlotlyJSONEncoder)
#
# with open("../flask_app/static/figures/itunes/itunes2.json", "w") as f:
#     f.write(itunes2_json)

itunes_graphs.append(0)
itunes_graphs.append(0)

spotify_popularity_daily = pd.read_sql_query('''
                                                SELECT
                                                    t1.Artist,
                                                    t1.Region,
                                                    ROUND(t1.total_artist / t2.region_total, 6) AS popularity_spotify,
                                                    ROUND(t3.Popularity, 6) AS popularity_itunes
                                                FROM (
                                                    SELECT
                                                        Artist,
                                                        Region,
                                                        ROUND(SUM(Total), 6) AS total_artist
                                                    FROM "spotify_charts_daily"
                                                    WHERE Region = "United States"
                                                    GROUP BY Artist, Region
                                                ) t1
                                                JOIN (
                                                    SELECT
                                                        Region,
                                                        ROUND(SUM(Total), 6) AS region_total
                                                    FROM "spotify_charts_daily"
                                                    WHERE Region = "United States"
                                                    GROUP BY Region
                                                ) t2 ON t1.Region = t2.Region
                                                LEFT JOIN (
                                                    SELECT
                                                        Artist,
                                                        Region,
                                                        ROUND(AVG("0 period(s) ago"), 2) AS Popularity
                                                    FROM "itunes_archive_united_states"
                                                    GROUP BY Artist
                                                ) t3 ON t1.Artist = t3.Artist 
                                                WHERE popularity_itunes > 0
                                                ORDER BY t1.Region, popularity DESC
                                            ''', conn)

print(spotify_popularity_daily)
# spotify_top_artists = spotify_popularity_daily.sort_values('popularity', ascending=False).head(30)
# print(spotify_top_artists)
# spotify_popularity_daily = spotify_popularity_daily[spotify_popularity_daily['Artist'].isin(spotify_top_artists)]
# print(spotify_popularity_daily)

spotify_popularity_daily['log_popularity'] = np.log1p(spotify_popularity_daily['popularity'])
spotify_popularity_daily['z_score'] = (
    spotify_popularity_daily
    .groupby('Region')['log_popularity']
    .transform(scipy.stats.zscore)
)

itunes_popularity_daily = pd.read_sql_query('''
                                                SELECT
                                                    Artist,
                                                    Region,
                                                    ROUND(AVG("0 period(s) ago"), 2) AS Popularity
                                                FROM "itunes_archive_united_states"
                                                GROUP BY Artist
                                            ''', conn)

itunes_popularity_daily['Popularity'] = np.log1p(itunes_popularity_daily['Popularity'])
itunes_popularity_daily['z_score'] = (
    itunes_popularity_daily['Popularity'].transform(scipy.stats.zscore)
)

print(itunes_popularity_daily)

x = np.linspace(-5, 25, 500)
y = 1 / (np.sqrt(2 * np.pi)) * np.exp(-0.5 * x**2)

curve = go.Scatter(
    x=x, y=y,
    name='Normal distribution',
    line=dict(color='gray', dash='dash'),
    hovertemplate='<extra></extra>'
)

scatter = go.Scatter(
    x=spotify_popularity_daily['z_score'].values,
    y=itunes_popularity_daily['z_score'].values,
    name='Spotify/iTunes Distribution',
    mode='markers',
    text=itunes_popularity_daily['Artist'],
    hovertemplate='Artist: %{text}<br>Spotify: %{x}<br>iTunes: %{y}<extra></extra>'
)

itunes_graphs.append(go.Figure(data=[curve, scatter]))
itunes_graphs[2].show()

# itunes3_json = json.dumps(itunes_graphs[2], cls=plotly.utils.PlotlyJSONEncoder)

# with open("../flask_app/static/figures/itunes/itunes3.json", "w") as f:
#     f.write(itunes3_json)
