import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

# DROP TABLES

staging_events_table_drop = "DROP TABLE IF EXISTS staging_events"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs"
songplay_table_drop = "DROP TABLE IF EXISTS songplays"
user_table_drop = "DROP TABLE IF EXISTS users"
song_table_drop = "DROP TABLE IF EXISTS songs"
artist_table_drop = "DROP TABLE IF EXISTS artist"
time_table_drop = "DROP TABLE IF EXISTS time"

# CREATE TABLES

staging_events_table_create= ("""
CREATE TABLE IF NOT EXISTS
staging_events(
    artist               VARCHAR,
    auth                 VARCHAR,
    firstName            VARCHAR,
    gender               VARCHAR,
    itemInSession        INT,
    lastName             VARCHAR,
    length               FLOAT,
    level                VARCHAR,
    location             VARCHAR,
    method               VARCHAR,
    page                 VARCHAR,
    registration         VARCHAR,
    sessionId            INT,
    song                 VARCHAR,
    status               VARCHAR,
    ts                   VARCHAR,
    userAgent            VARCHAR,
    userId               VARCHAR PRIMARY KEY
);
""")

staging_songs_table_create = ("""
CREATE TABLE IF NOT EXISTS
staging_songs(
    num_songs            INT,
    artist_id            VARCHAR,
    artist_latitude      FLOAT NOT NULL,
    artist_longitude     FLOAT NOT NULL,
    artist_location      VARCHAR NOT NULL,
    artist_name          VARCHAR,
    song_id              VARCHAR NOT NULL,
    title                VARCHAR,
    location             VARCHAR,
    duration             FLOAT,
    year                 INT
);
""")

songplay_table_create = ("""
CREATE TABLE IF NOT EXISTS 
songplays(
    songplay_id         INT             PRIMARY KEY IDENTITY(0,1) NOT NULL,
    start_time          TIMESTAMP       NOT NULL,
    user_id             VARCHAR         NOT NULL,
    level               VARCHAR,
    song_id             VARCHAR         NOT NULL,
    artist_id           VARCHAR         NOT NULL,
    session_id          BIGINT          NOT NULL,
    location            VARCHAR         NOT NULL,
    user_agent          TEXT            NOT NULL
);
""")

user_table_create = ("""
CREATE TABLE IF NOT EXISTS 
users(
    user_id             VARCHAR PRIMARY KEY NOT NULL,
    first_name          VARCHAR NOT NULL,
    last_name           VARCHAR NOT NULL,
    gender              VARCHAR NOT NULL,
    level               VARCHAR NOT NULL
);
""")

song_table_create = ("""
CREATE TABLE IF NOT EXISTS 
songs(
    song_id             VARCHAR PRIMARY KEY NOT NULL,
    title               VARCHAR NOT NULL,
    artist_id           VARCHAR NOT NULL,
    year                INTEGER NOT NULL,
    duration            FLOAT   NOT NULL
);
""")

artist_table_create = ("""
CREATE TABLE IF NOT EXISTS 
artists(
    artist_id          VARCHAR PRIMARY KEY NOT NULL, 
    name               VARCHAR NOT NULL,
    location           VARCHAR NOT NULL, 
    latitude           FLOAT   NOT NULL, 
    longitude          FLOAT   NOT NULL
);
""")

time_table_create = ("""
CREATE TABLE IF NOT EXISTS 
time(
    start_time         TIMESTAMP PRIMARY KEY NOT NULL, 
    hour               INTEGER NOT NULL, 
    day                INTEGER NOT NULL, 
    week               INTEGER NOT NULL, 
    month              INTEGER NOT NULL, 
    year               INTEGER NOT NULL, 
    weekday            INTEGER NOT NULL 
);
""")

# STAGING TABLES
staging_events_copy = ("""
    copy staging_events from {data_bucket}
    credentials 'aws_iam_role={role_arn}'
    region 'us-west-2' format as JSON {log_json_path}
    timeformat as 'epochmillisecs';
""").format(data_bucket=config['S3']['LOG_DATA'], role_arn=config['IAM_ROLE']['ARN'], log_json_path=config['S3']['LOG_JSONPATH'])

staging_songs_copy = ("""
    copy staging_songs from {data_bucket}
    credentials 'aws_iam_role={role_arn}'
    region 'us-west-2' format as JSON 'auto';
""").format(data_bucket=config['S3']['SONG_DATA'], role_arn=config['IAM_ROLE']['ARN'])

# FINAL TABLES

songplay_table_insert = ("""
INSERT INTO songplays (start_time, user_id, level, song_id, artist_id, session_id, location, user_agent) 
SELECT  
    TIMESTAMP 'epoch' + e.ts/1000 * interval '1 second' as start_time, 
    e.userId, 
    e.level, 
    s.song_id,
    s.artist_id, 
    e.sessionId,
    e.location, 
    e.userAgent
FROM staging_events e, staging_songs s
WHERE e.page Like 'NextSong' 
AND e.song = s.title 
AND e.artist = s.artist_name 
AND e.length = s.duration
""")

user_table_insert = ("""
    INSERT INTO users (user_id, first_name, last_name, gender, level)
    SELECT  DISTINCT(userId) AS user_Id,
            firstName        AS first_name,
            lastName         AS last_name,
            gender,
            level
     FROM staging_events
     WHERE user_id IS NOT NULL
     AND page Like 'NextSong';
""")

song_table_insert = ("""
    INSERT INTO songs (song_id, title, artist_id, year, duration)
    SELECT DISTINCT(song_id) AS song_id,
        title,
        artist_id,
        year,
        duration
    FROM staging_songs
    WHERE song_id IS NOT NULL;
""")

artist_table_insert = ("""
    INSERT INTO artists (artist_id, name, location, latitude, longitude)
    SELECT DISTINCT(artist_id) AS artist_id,
        artist_name            AS name,
        artist_location        AS location,
        artist_latitude        AS latitude,
        artist_longitude       AS longitude
    FROM staging_songs
    WHERE artist_id IS NOT NULL
    AND latitude IS NOT NULL
    AND location IS NOT NULL;
""")

time_table_insert = ("""
    INSERT INTO time (start_time, hour, day, week, month, year, weekday)
    SELECT DISTINCT(start_time) AS start_time,
        EXTRACT(hour      FROM start_time)       AS hour,
        EXTRACT(day       FROM start_time)       AS day,
        EXTRACT(week      FROM start_time)       AS week,
        EXTRACT(month     FROM start_time)       AS month,
        EXTRACT(year      FROM start_time)       AS year,
        EXTRACT(dayofweek FROM start_time)       AS weekday
    FROM songplays;
""")

# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]
