import sqlite3
import json
import pandas as pd

import plotly
import plotly.express as px
import plotly.graph_objects as go

conn = sqlite3.connect("../flask_app/database.db")

apple_music_graphs = []

# The first graph: Europe vs. Worldwide - the differences in listeners` preferences (only for artists
# having more than 5500 points and more than 2 tracks)

# The data for Apple Music are only available starting from "2017-06-29"
artist_average_rating = pd.read_sql_query('''
                                                SELECT
                                                    Artist,
                                                    Region,
                                                    ROUND(AVG(Pts), 2) as average_rating
                                                FROM "archive_songs"
                                                WHERE "Date" > "2017-06-29"
                                                GROUP BY "Artist", "Region"
                                                HAVING AVG(Pts) > 5500 and COUNT(DISTINCT Title) >= 3
                                            ''', conn)

apple_music_graphs.append(px.bar(
    artist_average_rating,
    x="Artist",
    y="average_rating",
    color="Region",
    barmode="group",
    text="average_rating",
    labels={"average_rating": "Average Rating"},
    title="Average Song Ratings per Artist by Region"
))

apple_music_graphs[0].update_traces(texttemplate='%{text:.1f}', textposition='outside')
apple_music_graphs[0].update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

apple_music1_json = json.dumps(apple_music_graphs[0], cls=plotly.utils.PlotlyJSONEncoder)

with open("../flask_app/static/figures/apple_music/apple_music1.json", "w") as f:
    f.write(apple_music1_json)

# The second graph: top preferences (albums) by countries
countries_preferences = pd.read_sql_query('''
                                            SELECT 
                                                Artist,
                                                Title,
                                                ROUND(AVG(SK), 2) AS Slovakia,
                                                ROUND(AVG(US), 2) AS "United States",
                                                ROUND(AVG(UK), 2) AS "United Kingdom",
                                                ROUND(AVG(FR), 2) AS France,
                                                ROUND(AVG(DE), 2) AS Germany,
                                                ROUND(AVG(CH), 2) AS Switzerland,
                                                ROUND(AVG(JP), 2) AS Japan,
                                                ROUND(AVG(AU), 2) AS Austria,
                                                ROUND(AVG(ES), 2) AS Spain,
                                                ROUND(AVG(BE), 2) AS Belgium
                                            FROM "archive_albums"
                                            WHERE "Region" = "Global" AND "Service" = "Apple Music"
                                            GROUP BY "Artist", "Title"
                                        ''', conn)

countries_preferences = pd.melt(
     countries_preferences,
     id_vars=['Artist', 'Title'],
     var_name='Country',
     value_name='Popularity'
)

countries = countries_preferences['Country'].unique()

apple_music_graphs.append(go.Figure())
buttons = []

for i, country in enumerate(countries):
    top_albums = (
        countries_preferences[countries_preferences['Country'] == country]
        .nlargest(10, 'Popularity')
        .sort_values('Popularity', ascending=False)
    )

    artists = {title: countries_preferences[countries_preferences['Title'] == title]['Artist'].values[0]
               for title in top_albums['Title'].values}
    x_vals = [f'{artists[title]} - {title}' for title in top_albums['Title']]
    x_vals = [val if len(val) <= 35 else val[:35] + '...' for val in x_vals]

    trace = go.Bar(
        x=x_vals,
        y=top_albums['Popularity'],
        name=country,
        visible=(i == 0)
    )

    apple_music_graphs[1].add_trace(trace)

    buttons.append(dict(
        label=country,
        method="update",
        args=[
            {"visible": [j == i for j in range(len(countries))]},
            {"title": f"Top 10 Albums in {country}",
             "xaxis": {"title": "Album"},
             "yaxis": {"title": "Popularity"}}
        ]
    ))

apple_music_graphs[1].update_layout(
    updatemenus=[dict(
        active=0,
        buttons=buttons,
        x=0.9,
        xanchor="center",
        y=1.3,
        yanchor="top"
    )],
    title=f"Top 10 Albums in {countries[0]}",
    xaxis_title="Album",
    yaxis_title="Popularity",
    height=500,
)

apple_music2_json = json.dumps(apple_music_graphs[1], cls=plotly.utils.PlotlyJSONEncoder)

with open("../flask_app/static/figures/apple_music/apple_music2.json", "w") as f:
    f.write(apple_music2_json)
