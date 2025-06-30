#!/usr/bin/env python
# coding: utf-8

# In[1]:


import re
import os

import pandas as pd
import numpy as np


# ## Data Cleaning

# The data were taken for the 5-years period (from 2014-01-01 to 2019-01-01). 
# 
# **iTunes archive:**
# The tables structure was not being changing during that period. The tables`  headers may seem strange at first glance (if you go to the source page), but there is an explanation: it describes the sales value X hours ago (comparing to the top 1 song). For instance, the fifth place could have a value of 0.2658 meaning that the song was only 26.58% successful (if we talk about sales) 0 hours ago particular date (for example, 2017-06-19). If we look at the next column which have a value 2 the according cell value will be related to the measurement that was made 2 hours before this date. 

# In[2]:


root = r'../data/raw/'


# In[3]:


# Spotify tables
spotify_charts_daily_global = pd.read_csv(root + 'spotify_charts_daily_global.csv', index_col=0, encoding='utf-8')
spotify_charts_daily_slovakia = pd.read_csv(root + 'spotify_charts_daily_slovakia.csv', index_col=0, encoding='utf-8')
spotify_charts_daily_united_states = pd.read_csv(root + 'spotify_charts_daily_united_states.csv', index_col=0, encoding='utf-8')
spotify_charts_weekly_global = pd.read_csv(root + 'spotify_charts_weekly_global.csv', index_col=0, encoding='utf-8')
spotify_charts_weekly_slovakia = pd.read_csv(root + 'spotify_charts_weekly_slovakia.csv', index_col=0, encoding='utf-8')
spotify_charts_weekly_united_states = pd.read_csv(root + 'spotify_charts_weekly_united_states.csv', index_col=0, encoding='utf-8')


# In[4]:


# Spotify (artists, listeners, top lists)
spotify_artists = pd.read_csv(root + 'spotify_artists.csv', index_col=0, encoding='utf-8')
spotify_listeners = pd.read_csv(root + 'spotify_listeners.csv', index_col=0, encoding='utf-8')
spotify_top_lists = pd.read_csv(root + 'spotify_top_lists.csv', index_col=0, encoding='utf-8')


# In[5]:


# iTunes archive table (only for US)
itunes_archive_united_states = pd.read_csv(root + 'itunes_archive_united_states.csv', index_col=0, low_memory=False, encoding='utf-8')
itunes_cumulative_united_states = pd.read_csv(root + 'itunes_cumulative_united_states.csv', index_col=0, encoding='utf-8')


# In[35]:


# Worldwide and European albums and songs (iTunes and Apple Music)
itunes_archive_worldwide_albums = pd.read_csv(root + 'itunes_archive_worldwide_albums.csv', index_col=0, low_memory=False, encoding='utf-8')
itunes_archive_worldwide_songs = pd.read_csv(root + 'itunes_archive_worldwide_songs.csv', index_col=0, low_memory=False, encoding='utf-8')
itunes_archive_european_albums = pd.read_csv(root + 'itunes_archive_european_albums.csv', index_col=0, low_memory=False, encoding='utf-8')
itunes_archive_european_songs = pd.read_csv(root + 'itunes_archive_european_songs.csv', index_col=0, low_memory=False, encoding='utf-8')
apple_music_archive_worldwide_albums = pd.read_csv(root + 'apple_music_archive_worldwide_albums.csv', index_col=0, low_memory=False, encoding='utf-8')
apple_music_archive_worldwide_songs = pd.read_csv(root + 'apple_music_archive_worldwide_songs.csv', index_col=0, low_memory=False, encoding='utf-8')
apple_music_archive_european_albums = pd.read_csv(root + 'apple_music_archive_european_albums.csv', index_col=0, low_memory=False, encoding='utf-8')
apple_music_archive_european_songs = pd.read_csv(root + 'apple_music_archive_european_songs.csv', index_col=0, low_memory=False, encoding='utf-8')


# In[7]:


# Radio charts archive
radio_charts_archive = pd.read_csv(root + 'radio_charts_archive.csv', index_col=0, encoding='utf-8')


# In[8]:


# YouTube (the most viewed clips)
youtube_clips = dict()
files = [f for f in os.listdir(root) if f.startswith('youtube_top_music_videos_')]

for f in files:
    suffix = f[f.rfind('_') + 1:f.find('.csv')]
    table = pd.read_csv(root + f, index_col=0, encoding='utf-8')

    if len(suffix) > 0:
        youtube_clips[suffix] = table
    else:
        youtube_clips['before 2010'] = table


# In[9]:


def basic_statistics(name: str, input_table: pd.DataFrame):
    print(f'Statistics of {name}')
    print(f'Shape: {input_table.shape}')
    with pd.option_context('display.max_rows', None):
        print(f'Missing values:\n{input_table.isnull().sum()}')
    print('-' * 50)


# In[10]:


def peak_count_process(input_table: pd.DataFrame):
    input_table['(x?)'] = input_table['(x?)'].apply(lambda x: int(x[x.find('x') + 1:x.find('?')]))


# In[11]:


def artist_tracks_process(input_table: pd.DataFrame):
    input_table[['Artist', 'Title']] = input_table['Artist and Title'].str.split(' -', n=1, expand=True)
    input_table['Title'] = input_table['Title'].apply(lambda x: x.strip() if isinstance(x, str) else None)
    input_table['Title'] = input_table['Title'].fillna('')
    input_table.drop(['Artist and Title'], axis=1, inplace=True)


# In[12]:


def move_columns(input_table: pd.DataFrame, columns_to_move: list, indices_destination: list):
    for index, column_name in zip(indices_destination, columns_to_move):
        column = input_table.pop(column_name)
        input_table.insert(index, column_name, column)


# In[13]:


def misaligned_date_process(row):
    found = False
    
    for col in row.index[:-1]:
        val = row[col]
        if isinstance(val, str) and re.match(r'^20\d{2}-\d{2}-\d{2}', val):
            row['Date'] = val
            row[col] = np.nan
            found = True
    if not found and not re.match(r'^20\d{2}-\d{2}-\d{2}', row['Date']):
        row['Date'] = np.nan
    return row


# ### 1. Spotify

# Features:
# 1. Artist and Title	
# 2. Wks - The number of weeks in the chart
# 3. T10 - Days in the Top 10 BEFORE the actual snapshot (some tracks in Top 10 could have missing values)
# 4. Peak (x?) - Highest position ever reached (peak) (x - the number of times it was reached)
# 5. PeakStreams - The highest number of daily streams this song has received on any single day
# 6. Total - The total number of stream at that moment of time

# In[14]:


# Covers charts from 2014/08/10 to 2025/06/10 and contains the overall ranking (aggregated daily and weekly charts)

basic_statistics('Spotify - Global (daily)', spotify_charts_daily_global)
basic_statistics('Spotify - Slovakia (daily)', spotify_charts_daily_slovakia)
basic_statistics('Spotify - United States (daily)', spotify_charts_daily_united_states)
basic_statistics('Spotify - Global (weekly)', spotify_charts_weekly_global)
basic_statistics('Spotify - Slovakia (weekly)', spotify_charts_weekly_slovakia)
basic_statistics('Spotify - United States (weekly)', spotify_charts_weekly_united_states)


# 1. T10 - it`s normal that some values are missing. But we can replace them with 0
# 2. (x?) - set to 1 when the value is missing. The track has reached some position in chart (Pk) but only once.
# 3. 'Artist and Title' column should be divided into two separate columns

# In[15]:


for table in [spotify_charts_daily_global, spotify_charts_daily_slovakia, spotify_charts_daily_united_states,
              spotify_charts_weekly_global, spotify_charts_weekly_slovakia, spotify_charts_weekly_united_states]:
    table['T10'].fillna(0, inplace=True)
    table['(x?)'].fillna('(x1)', inplace=True)
    peak_count_process(table)  # Convert to int values
    artist_tracks_process(table)  # Split 'Artist and Title' columns in two
    move_columns(table, ['Artist', 'Title', 'Region'], [0, 1, 2])  # Reorder the indices


# In[16]:


basic_statistics('Spotify - Artists', spotify_artists)
basic_statistics('Spotify - Listeners', spotify_listeners)
basic_statistics('Spotify - Top Lists', spotify_top_lists)


# Fill the unknown values in the columns 'As lead', 'Solo', 'As feature' with -1. (We want the values to be float values)

# In[17]:


spotify_artists.loc[:, 'As lead'] = spotify_artists['As lead'].fillna(-1)
spotify_artists.loc[:, 'Solo'] = spotify_artists['Solo'].fillna(-1)
spotify_artists.loc[:, 'As feature'] = spotify_artists['As feature'].fillna(-1)


# In[18]:


spotify_top_lists = spotify_top_lists.rename(columns={'Unnamed: 0': 'Period'})
artist_tracks_process(spotify_top_lists)
move_columns(spotify_top_lists, ['Artist', 'Title'], [1, 2])


# ### 2. iTunes Archive

# In[19]:


# This table is poorly structured: bad namings (my fault), the last column contains only missing values (I should drop it)
names = ['Position', 'Artist and Title']
names.extend(itunes_archive_united_states.columns[:20])
names.extend(['Date', '???'])
itunes_archive_united_states.columns = names
itunes_archive_united_states = itunes_archive_united_states.iloc[:, 0:23]


# In[20]:


basic_statistics('iTunes sales in US', itunes_archive_united_states)

# Assumes overall sales have remained constant over time. Based on daily top 100. So, it`s just daily aggregation.
basic_statistics('iTunes sales in US', itunes_cumulative_united_states)


# 1. The Cumulative table has no problems. Just divide 'Artist and Title' column.
# 2. But there are a lot of problems with the first table. The first and the last measurements are missing in the large part of cases. And the strangest is that the dates are also missing. => There is no problem with the measurements: some snapshots have fewer columns describing the particular timestamps. But the dates now are located in different columns and should be gathered.
# 3. The last measurements are not the problem: the majority of rows don't have this number of measurements.

# In[21]:


artist_tracks_process(itunes_cumulative_united_states)
itunes_cumulative_united_states['Region'] = 'United States'
move_columns(itunes_cumulative_united_states, ['Artist', 'Title', 'Region'], [0, 1, 2])


# In[22]:


artist_tracks_process(itunes_archive_united_states)
itunes_archive_united_states['Region'] = 'United States'
move_columns(itunes_archive_united_states, ['Artist', 'Title', 'Region'], [0, 1, 2])

itunes_archive_united_states = itunes_archive_united_states.apply(misaligned_date_process, axis=1)


# In[23]:


# I've noticed that the dollars create a separate column which shifted all the values in a result. So I should deal with it.
# Upd: It had also been the reason for missing values in the '0 period(s) ago' column.
col = itunes_archive_united_states['0 period(s) ago']
mask = (col == '$') | (col.isna())
replacement = itunes_archive_united_states[mask].iloc[:, 5:23]
replacement['19 period(s) ago'] = np.nan

itunes_archive_united_states.iloc[mask.values, 4:23] = replacement.values


# ### 3. Worldwide section (iTunes and Apple Music)

# In[36]:


basic_statistics('iTunes archive - album rankings (Global)', itunes_archive_worldwide_albums)
basic_statistics('iTunes archive - song rankings (Global)', itunes_archive_worldwide_songs)
basic_statistics('iTunes archive - album rankings (Europe)', itunes_archive_european_albums)
basic_statistics('iTunes archive - song rankings (Europe)', itunes_archive_european_songs)
basic_statistics('Apple Music archive - album rankings (Global)', apple_music_archive_worldwide_albums)
basic_statistics('Apple Music archive - song rankings (Global)', apple_music_archive_worldwide_songs)
basic_statistics('Apple Music archive - album rankings (Europe)', apple_music_archive_european_albums)
basic_statistics('Apple Music archive - song rankings (Europe)', apple_music_archive_european_songs)


# 1. There is a problem with song tables, but they are related to the changes in the namings ('Peak' -> 'Pk', 'Pos+' -> 'P+')
# 2. No problem with the missing values describing track sales (or popularity) in different countries -> replacing the NaNs with zeros.

# In[37]:


for table, region in [(itunes_archive_worldwide_albums, 'Global'), (itunes_archive_worldwide_songs, 'Global'),
              (apple_music_archive_worldwide_albums, 'Global'), (apple_music_archive_worldwide_songs, 'Global'),
              (itunes_archive_european_albums, 'Europe'), (itunes_archive_european_songs, 'Europe'),
              (apple_music_archive_european_albums, 'Europe'), (apple_music_archive_european_songs, 'Europe')]:
    table.rename(columns={'DATE': 'Date'}, inplace=True)
    table['(x?)'].fillna('(x1)', inplace=True)
    peak_count_process(table)
    table['Region'] = region
    artist_tracks_process(table)
    move_columns(table, ['Artist', 'Title', 'Region'], [0, 1, 2])


# In[38]:


def doubles_fix(input_table:pd.DataFrame):
    input_table['Pk'] = (
        input_table.get('Pk')
        .combine_first(input_table.get('Pk'))
        .combine_first(input_table.get('Peak'))
    )
    
    input_table['P+'] = (
        input_table.get('P+')
        .combine_first(input_table.get('P+'))
        .combine_first(input_table.get('Pos+'))
    )

    input_table.drop(columns=['Peak', 'Pos+'], errors='ignore', inplace=True)


# In[39]:


def peak_doubles_count_process(row):
    val = row.get('Pk')
    if isinstance(val, str):
        match = re.match(r'^(\d+)\((\d+)\)$', val)
        if match:
            row['(x?)'] = int(match.group(2))
            row['Pk'] = int(match.group(1))
    return row


# In[40]:


for table in [itunes_archive_worldwide_songs, itunes_archive_worldwide_albums,
          itunes_archive_european_songs, itunes_archive_european_albums]:
    doubles_fix(table)
    move_columns(table, ['P+', 'Pk', '(x?)', 'Date'], [4, 6, 7, len(table.columns) - 1])

itunes_archive_worldwide_songs = itunes_archive_worldwide_songs.apply(peak_doubles_count_process, axis=1)
itunes_archive_worldwide_albums = itunes_archive_worldwide_albums.apply(peak_doubles_count_process, axis=1)
itunes_archive_european_songs = itunes_archive_european_songs.apply(peak_doubles_count_process, axis=1)
itunes_archive_european_albums = itunes_archive_european_albums.apply(peak_doubles_count_process, axis=1)


# In[41]:


for table in [itunes_archive_worldwide_albums, itunes_archive_worldwide_songs, 
              apple_music_archive_worldwide_albums, apple_music_archive_worldwide_songs, 
              itunes_archive_european_albums, itunes_archive_european_songs,
              apple_music_archive_european_albums, apple_music_archive_european_songs]:
    table.fillna(0, inplace=True)


# ### 4. Radio charts

# 1. Spins = Number of times the song was played the past week (7 days).
# 2. Spins+ = Change in "Spins" compared to the day before.<br>
# Another way to explain this is that it's the difference between the number of spins a song received yesterday and the number of spins it received on the same day the week before.
# 
# 3. Bullet = Total increase or decrease in spins compared to last week.
# 4. Bullet+ = Change in "Bullet" compared to the day before.<br>
# Positive "Bullet", positive "Bullet+" = Song is increasing, and more rapidly than before.<br>
# Positive "Bullet", negative "Bullet+" = Song is increasing, but it's slowing down.<br>
# Negative "Bullet", positive "Bullet+" = Song is decreasing, but not as fast as before.<br>
# Negative "Bullet", negative "Bullet+" = Song is decreasing, even faster than before.
# 
# 5. Aud = Audience reached in millions. <br>
# Each spin is worth a certain audience value, depending on the station and the time of day. It is cumulative, so "100 million" does not necessarily mean that 100 million people have heard it. It could be 5 million people each hearing the song 20 times.
# 
# 6. Aud+ = Change in "Aud" compared to the day before.
# 
# 7. Days = Number of days on the chart.
# 8. iTunes = Current US iTunes ranking.
# 9. Pk = All the peak values.

# In[32]:


basic_statistics('Radio charts - archive', radio_charts_archive)


# 1. Classic processing + We have 1827 missing rows. This is because the author decided to add some empty rows which separate the top-100 from the remaining tracks.
# 2. Pos and P+ - the tracks after top-100 are not marked by the author of the statistics -> replace the missing values by 100+ (101.0* because it should be float value) and ? respectively
# 3. Days/Pk/Aud+ - similar reason, but some tracks below top-100 have the values. The remaining ones could be also replaced with the '?' (or -1, because we want these columns to be int/float values).
# 4. Formats - sometimes contain additional values in the parentheses describing the changes. There is a very small number of them, so they could be truncated.

# In[42]:


# Basic pipeline
radio_charts_archive['(x?)'].fillna('(x1)', inplace=True)
peak_count_process(radio_charts_archive)
radio_charts_archive['Region'] = 'United States'
artist_tracks_process(radio_charts_archive)
move_columns(radio_charts_archive, ['Artist', 'Title', 'Region'], [0, 1, 2])
radio_charts_archive = radio_charts_archive[-radio_charts_archive['Artist'].isna()]


# In[43]:


# Filling the missing values
radio_charts_archive.loc[:, 'Pos'] = radio_charts_archive['Pos'].fillna(101.0)
radio_charts_archive.loc[:, 'P+'] = radio_charts_archive['P+'].fillna('?')
radio_charts_archive.loc[:, 'Days'] = radio_charts_archive['Days'].fillna(-1)
radio_charts_archive.loc[:, 'Pk'] = radio_charts_archive['Pk'].fillna(-1)
radio_charts_archive.loc[:, 'Aud+'] = radio_charts_archive['Pk'].fillna(-1)


# In[44]:


# '--' can be changed to -1 as we don't know the real value. 
# There are also two-position cells for some tracks. We will choose the highest one. 
for service in ['iTunes', 'Spotify', 'Apple M', 'Shazam']:
    radio_charts_archive[service] = radio_charts_archive[service].replace({'--': -1})
    radio_charts_archive[service] = radio_charts_archive[service].apply(lambda x: int(min(x.split('/'))) 
                                                                       if isinstance(x, str) and '/' in x 
                                                                       else int(x))


# In[45]:


# 'Formats' column
radio_charts_archive['Formats'] = radio_charts_archive['Formats'].apply(lambda x: float(x[:x.find('(')].strip()) 
                                                                       if isinstance(x, str) and '(' in x 
                                                                       else float(x))


# ### 5. YouTube (Top music videos)

# In[37]:


for year, table in youtube_clips.items():
    basic_statistics(f'YouTube - the most viewed clips ({year})', table)


# In[46]:


youtube_clips['before 2010']['Publication year'] = 'before 2010'


# ### 6. Preparing CSVs and saving the files

# In[58]:


spotify_charts_daily = pd.concat([spotify_charts_daily_global, spotify_charts_daily_slovakia, spotify_charts_daily_united_states], ignore_index=True)
spotify_charts_weekly = pd.concat([spotify_charts_weekly_global, spotify_charts_weekly_slovakia, spotify_charts_weekly_united_states], ignore_index=True)
itunes_archive_albums = pd.concat([itunes_archive_worldwide_albums, itunes_archive_european_albums], ignore_index=True)
itunes_archive_songs = pd.concat([itunes_archive_worldwide_songs, itunes_archive_european_songs], ignore_index=True)
apple_music_archive_albums = pd.concat([apple_music_archive_worldwide_albums, apple_music_archive_european_albums], ignore_index=True)
apple_music_archive_songs = pd.concat([apple_music_archive_worldwide_songs, apple_music_archive_european_songs], ignore_index=True)
youtube_clips_overall = pd.concat(youtube_clips.values(), ignore_index=True)


# In[133]:


# Linkin Park has another pattern (In The End [Official HD Music Video] - Linkin Park) -> (<video> - <name>)
# I will deal with it separately

youtube_clips_overall[['Artist', 'Title']] = youtube_clips_overall['Video'].str.split(r'\s*[-–]\s*', n=1, expand=True)

mask = youtube_clips_overall['Title'] == 'Linkin Park'
youtube_clips_overall.loc[mask, ['Artist', 'Title']] = youtube_clips_overall.loc[mask, ['Title', 'Artist']].values

youtube_clips_overall['Title'] = youtube_clips_overall['Title'].apply(lambda x: x.strip() if isinstance(x, str) else None)
youtube_clips_overall['Title'] = youtube_clips_overall['Title'].fillna('')
youtube_clips_overall.drop(['Video'], axis=1, inplace=True)
move_columns(youtube_clips_overall, ['Artist', 'Title'], [0, 1])
youtube_clips_overall['Title'] = youtube_clips_overall['Title'].apply(lambda x: x[:min(x.find('(') if x.find('(') != -1 else len(x), x.find('[') if x.find('[') != -1 else len(x))].rstrip() if '[' in x or '(' in x else x)


# In[59]:


itunes_archive_albums['Service'] = 'iTunes'
itunes_archive_songs['Service'] = 'iTunes'
apple_music_archive_albums['Service'] = 'Apple Music'
apple_music_archive_songs['Service'] = 'Apple Music'


# In[60]:


move_columns(itunes_archive_albums, ['Service'], [0])
move_columns(itunes_archive_songs, ['Service'], [0])
move_columns(apple_music_archive_albums, ['Service'], [0])
move_columns(apple_music_archive_songs, ['Service'], [0])


# In[61]:


archive_albums = pd.concat([itunes_archive_albums, apple_music_archive_albums], ignore_index=True)
archive_songs = pd.concat([itunes_archive_songs, apple_music_archive_songs], ignore_index=True)


# In[64]:


spotify_charts_daily.to_csv('../data/spotify_charts_daily.csv', index=False)
spotify_charts_weekly.to_csv('../data/spotify_charts_weekly.csv', index=False)
spotify_artists.to_csv('../data/spotify_artists.csv', index=False)
spotify_listeners.to_csv('../data/spotify_listeners.csv', index=False)
spotify_top_lists.to_csv('../data/spotify_top_lists.csv', index=False)

itunes_archive_united_states.to_csv('../data/itunes_archive_united_states.csv', index=False)
itunes_cumulative_united_states.to_csv('../data/itunes_cumulative_united_states.csv', index=False)

archive_albums.to_csv('../data/archive_albums.csv', index=False)
archive_songs.to_csv('../data/archive_songs.csv', index=False)

radio_charts_archive.to_csv('../data/radio_charts_archive.csv', index=False)

youtube_clips_overall.to_csv('../data/youtube_clips_overall.csv', index=False)
