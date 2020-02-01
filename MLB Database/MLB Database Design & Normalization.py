#!/usr/bin/env python
# coding: utf-8

# # Designing Database for Major League Baseball
# 
# For this assignment I will be working with a file of [Major League Baseball](https://en.wikipedia.org/wiki/Major_League_Baseball) games from [Retrosheet](http://www.retrosheet.org/). Retrosheet compiles detailed statistics on baseball games from the 1800s through to today. The main file I will be working from game_log.csv, has been produced by combining 127 separate CSV files from retrosheet, and has been pre-cleaned to remove some inconsistencies. The game log has hundreds of data points on each game which I will normalize into several separate tables using SQL, providing a robust database of game-level statistics.
# 
# In addition to the main file, I have also included three 'helper' files, also sourced from Retrosheet:
# 
# - park_codes.csv
# - person_codes.csv
# - team_codes.csv
# 
# These three helper files in some cases contain extra data, but will also make things easier as they will form the basis for three of our normalized tables.
# 
# I will begin exploring the data by using pandas to read and explore the data. Setting the following options after I import pandas is recommended– they will prevent the DataFrame output from being truncated, given the size of the main game log file:

# In[1]:


import sqlite3
import pandas as pd
import csv

pd.set_option('max_columns', 180)
pd.set_option('max_rows', 200000)
pd.set_option('max_colwidth', 5000)


# ## Understanding data
# 
# ### Log Dataset

# In[2]:


log = pd.read_csv("game_log.csv",low_memory=False)
print(log.shape)
log.head()


# In[3]:


log.tail()


# #### Insights:
# 
# Looking at the data from the game_log file we can see there are over 170,000 rows, meaning each row represents a game that has been played.
# 
# Details on each game:
# 
# - Game date range: 1871 to 2016
# - Individual player stats
# - Game stats
# - Team stats
# - Refree information
# - Awards such as who performed better or won/loss
# 
# ### Person dataset

# In[4]:


person = pd.read_csv('person_codes.csv')
print(person.shape)
person.head()


# In[5]:


person.tail()


# #### Insights
# 
# This dataset shows us individual people's information of whether they were a player, a manager, a coach or an umpire. This is probably a mass directory that links people with IDs anout when they debut in their respective position.
# 
# Manager's are seen as Head Coaches, where as a Coach is more specializaed such as a batting coach or pitching coach.
# 
# ### Park dataset

# In[6]:


park = pd.read_csv('park_codes.csv')
print(park.shape)
park.head()


# In[7]:


park.tail()


# #### Insights
# 
# This dataset is about the locations of the stadiums being used for the games. There is also information about possible nicknames of the stadiums.
# 
# ### Team Codes Dataset

# In[8]:


team = pd.read_csv('team_codes.csv')
print(team.shape)
team.head()


# In[9]:


team.tail()


# #### Insights
# 
# This dataset provides information about the team mainly about their history and location. There is an interesting column franch_id which I will explore more in detail next.

# In[10]:


team["franch_id"].value_counts().head()


# It is interesting that some franch_ids may be occuring for more than one team. 

# In[11]:


team[team["franch_id"] == 'BS1']


# It looks like that the franchise ids remain the same but the team city changes similarly corresponding to the start and end date, while keeping the nickname. This must mean they move to a new city to relocate which is common in U.S. sports.
# 
# **Leagues**
# 
# The baseball league normally has two main leagues the American (AL) and the National (NL).

# In[12]:


log["h_league"].value_counts()


# It is clear the AL and the NL are the main leagues but there are still a few leagues worth learning more about.

# In[13]:


def league_info(league):
    league_games = log[log["h_league"] == league]
    earliest = league_games["date"].min()
    latest = league_games["date"].max()
    print("{} went from {} to {}".format(league,earliest,latest))

for league in log["h_league"].unique():
    league_info(league)


# Now we have some years which will help us do some research. After some googling we come up with:
# 
# - NL: National League
# - AL: American League
# - AA: American Association
# - FL: Federal League
# - PL: Players League
# - UA: Union Association
# 
# ## Importing Data into SQLite

# In[14]:


DB = "mlb.db"

def run_query(q):
    with sqlite3.connect(DB) as conn:
        return pd.read_sql(q,conn)

def run_command(c):
    with sqlite3.connect(DB) as conn:
        conn.execute('PRAGMA foreign_keys = ON;')
        conn.isolation_level = None
        conn.execute(c)

def show_tables():
    q = '''
    SELECT
        name,
        type
    FROM sqlite_master
    WHERE type IN ("table","view");
    '''
    return run_query(q)


# In[15]:


tables = {
    "game_log": log,
    "person_codes": person,
    "team_codes": team,
    "park_codes": park
}

with sqlite3.connect(DB) as conn:    
    for name, data in tables.items():
        conn.execute("DROP TABLE IF EXISTS {};".format(name))
        data.to_sql(name,conn,index=False)


# In[25]:


show_tables()


# ### Create primary key for log table

# In[17]:


c1 = """
ALTER TABLE game_log
ADD COLUMN game_id TEXT;
"""

# try/except loop since ALTER TABLE
# doesn't support IF NOT EXISTS
try:
    run_command(c1)
except:
    pass

c2 = """
UPDATE game_log
SET game_id = date || h_name || number_of_game
/* WHERE prevents this if it has already been done */
WHERE game_id IS NULL; 
"""

run_command(c2)

q = """
SELECT
    game_id,
    date,
    h_name,
    number_of_game
FROM game_log
LIMIT 5;
"""

run_query(q)


# ## Looking for Normalization Opportunities
# The following are opportunities for normalization of our data:
# 
# - In person_codes, all the debut dates will be able to be reproduced using game log data.
# - In team_codes, the start, end and sequence columns will be able to be reproduced using game log data.
# - In park_codes, the start and end years will be able to be reproduced using game log data. While technically the state is an attribute of the city, we might not want to have a an incomplete city/state table so we will leave this in.
# - There are lots of places in game log where we have a player ID followed by the players name. We will be able to remove this and use the name data in person_codes
# - In game_log, all offensive and defensive stats are repeated for the home team and the visiting team. We could break these out and have a table that lists each game twice, one for each team, and cut out this column repetition.
# - Similarly, in game_log, we have a listing for 9 players on each team with their positions - we can remove these and have one table that tracks player appearances and their positions.
# - We can do a similar thing with the umpires from game_log, instead of listing all four positions as columns, we can put the umpires either in their own table or make one table for players, umpires and managers.
# - We have several awards in game_log like winning pitcher and losing pitcher. We can either break these out into their own table, have a table for awards, or combine the awards in with general appearances like the players and umpires.
# 
# ## Planning a Normalized Schema
# 
# <img src="MLB Schema.png">
# 
# ## Creating tables without foreign keys
# 
# ### persons table - NEW

# In[18]:


c1 = """
CREATE TABLE IF NOT EXISTS person (
    person_id TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT
);
"""

c2 = """
INSERT OR IGNORE INTO person
SELECT id,
       first,
       last
FROM person_codes;
"""

q = """
SELECT *
FROM person
LIMIT 5;"""

run_command(c1)
run_command(c2)
run_query(q)


# ### park table - NEW

# In[26]:


c1 = """
CREATE TABLE IF NOT EXISTS park (
    park_id TEXT PRIMARY KEY,
    name TEXT,
    nickname TEXT,
    city TEXT,
    state TEXT,
    notes TEXT
);
"""

c2 = """
INSERT OR IGNORE INTO park
SELECT
    park_id,
    name,
    aka,
    city,
    state,
    notes
FROM park_codes;
"""

q = """
SELECT * FROM park
LIMIT 5;
"""

run_command(c1)
run_command(c2)
run_query(q)


# ### league table - NEW

# In[28]:


c1 = """
CREATE TABLE IF NOT EXISTS league (
    league_id TEXT PRIMARY KEY,
    league_name TEXT
);
"""

c2 = """
INSERT OR IGNORE INTO league
VALUES
    ("NL", "National League"),
    ("AL", "American League"),
    ("AA", "American Association"),
    ("FL", "Federal League"),
    ("PL", "Players League"),
    ("UA", "Union Association")
;
"""

q = """
SELECT *
FROM league;"""

run_command(c1)
run_command(c2)
run_query(q)


# ### appearance table - NEW

# In[35]:


c1 = "DROP TABLE IF EXISTS appearance_type;"

run_command(c1)

c2 = """
CREATE TABLE appearance_type (
    appearance_type_id TEXT PRIMARY KEY,
    name TEXT,
    category TEXT
);
"""
run_command(c2)

appearance_type = pd.read_csv('appearance_type.csv')

with sqlite3.connect('mlb.db') as conn:
    appearance_type.to_sql('appearance_type',
                           conn,
                           index=False,
                           if_exists='append')

q = """
SELECT * FROM appearance_type;
"""

run_query(q)


# Now that I have added all of the tables that don't have foreign key relationships, I will add the next two tables. The game and team tables need to exist before the two appearance tables are created.
# 
# Here are some notes on the normalization choices made with each of these tables:
# 
# - team
#  - The start, end, and sequence columns can be derived from the game level data.
# 
# - game
#  - We have chosen to include all columns for the game log that don't refer to one specific team or player, instead putting those in two appearance tables.
#  - We have removed the column with the day of the week, as this can be derived from the date.
#  - We have changed the day_night column to day, with the intention of making this a boolean column. Even though SQLite doesn't support the BOOLEAN type, we can use this when creating our table and SQLite will manage the underlying types behind the scenes (for more on how this works refer to the SQLite documentation. This means that anyone quering the schema of our database in the future understands how that column is intended to be used.
#  
#  
# ### team table - NEW

# In[36]:


c1 = """
CREATE TABLE IF NOT EXISTS team (
    team_id TEXT PRIMARY KEY,
    league_id TEXT,
    city TEXT,
    nickname TEXT,
    franch_id TEXT
);"""

c2 = """
INSERT OR IGNORE INTO team
SELECT
    team_id,
    league,
    city,
    nickname,
    franch_id
FROM team_codes;
"""

q = """
SELECT*
FROM team
LIMIT 5;"""

run_command(c1)
run_command(c2)
run_query(q)


# ### game table - NEW

# In[37]:


c1 = """
CREATE TABLE IF NOT EXISTS game (
    game_id TEXT PRIMARY KEY,
    date TEXT,
    number_of_game INTEGER,
    park_id TEXT,
    length_outs INTEGER,
    day BOOLEAN,
    competition TEXT,
    forfeit TEXT,
    protest TEXT,
    attendance INTEGER,
    length_minutes INTEGER,
    addtional_info TEXT,
    acquisition_info TEXT
);
"""

c2 = """
INSERT OR IGNORE INTO game
SELECT
    game_id,
    date,
    number_of_game,
    park_id,
    length_outs,
    CASE
        WHEN day_night = "D" THEN 1
        WHEN day_night = "N" THEN 0
        ELSE NULL
        END
        AS day,
    completion,
    forefeit,
    protest,
    attendance,
    length_minutes,
    additional_info,
    acquisition_info
FROM game_log;
"""

q = """
SELECT *
FROM game
LIMIT 5;
"""

run_command(c1)
run_command(c2)
run_query(q)


# ### Adding the Team Appearance Table
# The team_appearance table has a compound primary key composed of the team name and the game ID. In addition, a boolean column home is used to differentiate between the home and the away team. The rest of the columns are scores or statistics that in our original game log are repeated for each of the home and away teams.

# In[39]:


c1 = """
CREATE TABLE IF NOT EXISTS team_appearance(
    team_id TEXT,
    game_id TEXT,
    home BOOLEAN,
    league_id TEXT,
    score INTEGER,
    line_score TEXT,
    at_bats INTEGER,
    hits INTEGER,
    doubles INTEGER,
    triples INTEGER,
    homeruns INTEGER,
    rbi INTEGER,
    sacrifice_hits INTEGER,
    sacrifice_flies INTEGER,
    hit_by_pitch INTEGER,
    walks INTEGER,
    intentional_walks INTEGER,
    strikeouts INTEGER,
    stolen_bases INTEGER,
    caught_stealing INTEGER,
    grounded_into_double INTEGER,
    first_catcher_interference INTEGER,
    left_on_base INTEGER,
    pitchers_used INTEGER,
    individual_earned_runs INTEGER,
    team_earned_runs INTEGER,
    wild_pitches INTEGER,
    balks INTEGER,
    putouts INTEGER,
    assists INTEGER,
    errors INTEGER,
    passed_balls INTEGER,
    double_plays INTEGER,
    triple_plays INTEGER,
    PRIMARY KEY (team_id, game_id),
    FOREIGN KEY (team_id) REFERENCES team(team_id),
    FOREIGN KEY (game_id) REFERENCES game(game_id),
    FOREIGN KEY (team_id) REFERENCES team(team_id)
);
"""

run_command(c1)

c2 = """
INSERT OR IGNORE INTO team_appearance
    SELECT
        h_name,
        game_id,
        1 AS home,
        h_league,
        h_score,
        h_line_score,
        h_at_bats,
        h_hits,
        h_doubles,
        h_triples,
        h_homeruns,
        h_rbi,
        h_sacrifice_hits,
        h_sacrifice_flies,
        h_hit_by_pitch,
        h_walks,
        h_intentional_walks,
        h_strikeouts,
        h_stolen_bases,
        h_caught_stealing,
        h_grounded_into_double,
        h_first_catcher_interference,
        h_left_on_base,
        h_pitchers_used,
        h_individual_earned_runs,
        h_team_earned_runs,
        h_wild_pitches,
        h_balks,
        h_putouts,
        h_assists,
        h_errors,
        h_passed_balls,
        h_double_plays,
        h_triple_plays
    FROM game_log

UNION

    SELECT    
        v_name,
        game_id,
        0 AS home,
        v_league,
        v_score,
        v_line_score,
        v_at_bats,
        v_hits,
        v_doubles,
        v_triples,
        v_homeruns,
        v_rbi,
        v_sacrifice_hits,
        v_sacrifice_flies,
        v_hit_by_pitch,
        v_walks,
        v_intentional_walks,
        v_strikeouts,
        v_stolen_bases,
        v_caught_stealing,
        v_grounded_into_double,
        v_first_catcher_interference,
        v_left_on_base,
        v_pitchers_used,
        v_individual_earned_runs,
        v_team_earned_runs,
        v_wild_pitches,
        v_balks,
        v_putouts,
        v_assists,
        v_errors,
        v_passed_balls,
        v_double_plays,
        v_triple_plays
    from game_log;
"""

run_command(c2)


q = """
SELECT * FROM team_appearance
WHERE game_id = (
                 SELECT MIN(game_id) from game
                )
   OR game_id = (
                 SELECT MAX(game_id) from game
                )
ORDER By game_id, home;
"""

run_query(q)


# ### Adding the Person Appearance Table
# The person_appearance table will be used to store information on appearances in games by managers, players, and umpires as detailed in the appearance_type table.

# In[40]:



c0 = "DROP TABLE IF EXISTS person_appearance"

run_command(c0)

c1 = """
CREATE TABLE person_appearance (
    appearance_id INTEGER PRIMARY KEY,
    person_id TEXT,
    team_id TEXT,
    game_id TEXT,
    appearance_type_id,
    FOREIGN KEY (person_id) REFERENCES person(person_id),
    FOREIGN KEY (team_id) REFERENCES team(team_id),
    FOREIGN KEY (game_id) REFERENCES game(game_id),
    FOREIGN KEY (appearance_type_id) REFERENCES appearance_type(appearance_type_id)
);
"""

c2 = """
INSERT OR IGNORE INTO person_appearance (
    game_id,
    team_id,
    person_id,
    appearance_type_id
) 
    SELECT
        game_id,
        NULL,
        hp_umpire_id,
        "UHP"
    FROM game_log
    WHERE hp_umpire_id IS NOT NULL    

UNION

    SELECT
        game_id,
        NULL,
        [1b_umpire_id],
        "U1B"
    FROM game_log
    WHERE "1b_umpire_id" IS NOT NULL

UNION

    SELECT
        game_id,
        NULL,
        [2b_umpire_id],
        "U2B"
    FROM game_log
    WHERE [2b_umpire_id] IS NOT NULL

UNION

    SELECT
        game_id,
        NULL,
        [3b_umpire_id],
        "U3B"
    FROM game_log
    WHERE [3b_umpire_id] IS NOT NULL

UNION

    SELECT
        game_id,
        NULL,
        lf_umpire_id,
        "ULF"
    FROM game_log
    WHERE lf_umpire_id IS NOT NULL

UNION

    SELECT
        game_id,
        NULL,
        rf_umpire_id,
        "URF"
    FROM game_log
    WHERE rf_umpire_id IS NOT NULL

UNION

    SELECT
        game_id,
        v_name,
        v_manager_id,
        "MM"
    FROM game_log
    WHERE v_manager_id IS NOT NULL

UNION

    SELECT
        game_id,
        h_name,
        h_manager_id,
        "MM"
    FROM game_log
    WHERE h_manager_id IS NOT NULL

UNION

    SELECT
        game_id,
        CASE
            WHEN h_score > v_score THEN h_name
            ELSE v_name
            END,
        winning_pitcher_id,
        "AWP"
    FROM game_log
    WHERE winning_pitcher_id IS NOT NULL

UNION

    SELECT
        game_id,
        CASE
            WHEN h_score < v_score THEN h_name
            ELSE v_name
            END,
        losing_pitcher_id,
        "ALP"
    FROM game_log
    WHERE losing_pitcher_id IS NOT NULL

UNION

    SELECT
        game_id,
        CASE
            WHEN h_score > v_score THEN h_name
            ELSE v_name
            END,
        saving_pitcher_id,
        "ASP"
    FROM game_log
    WHERE saving_pitcher_id IS NOT NULL

UNION

    SELECT
        game_id,
        CASE
            WHEN h_score > v_score THEN h_name
            ELSE v_name
            END,
        winning_rbi_batter_id,
        "AWB"
    FROM game_log
    WHERE winning_rbi_batter_id IS NOT NULL

UNION

    SELECT
        game_id,
        v_name,
        v_starting_pitcher_id,
        "PSP"
    FROM game_log
    WHERE v_starting_pitcher_id IS NOT NULL

UNION

    SELECT
        game_id,
        h_name,
        h_starting_pitcher_id,
        "PSP"
    FROM game_log
    WHERE h_starting_pitcher_id IS NOT NULL;
"""

template = """
INSERT INTO person_appearance (
    game_id,
    team_id,
    person_id,
    appearance_type_id
) 
    SELECT
        game_id,
        {hv}_name,
        {hv}_player_{num}_id,
        "O{num}"
    FROM game_log
    WHERE {hv}_player_{num}_id IS NOT NULL

UNION

    SELECT
        game_id,
        {hv}_name,
        {hv}_player_{num}_id,
        "D" || CAST({hv}_player_{num}_def_pos AS INT)
    FROM game_log
    WHERE {hv}_player_{num}_id IS NOT NULL;
"""

run_command(c1)
run_command(c2)

for hv in ["h","v"]:
    for num in range(1,10):
        query_vars = {
            "hv": hv,
            "num": num
        }
        run_command(template.format(**query_vars))


# In[41]:


print(run_query("SELECT COUNT(DISTINCT game_id) games_game FROM game"))
print(run_query("SELECT COUNT(DISTINCT game_id) games_person_appearance FROM person_appearance"))

q = """
SELECT
    pa.*,
    at.name,
    at.category
FROM person_appearance pa
INNER JOIN appearance_type at on at.appearance_type_id = pa.appearance_type_id
WHERE PA.game_id = (
                   SELECT max(game_id)
                    FROM person_appearance
                   )
ORDER BY team_id, appearance_type_id
"""

run_query(q)


# ## Removing old tables

# In[42]:


show_tables()


# In[43]:


tables = [
    "game_log",
    "park_codes",
    "team_codes",
    "person_codes"
]

for t in tables:
    c = '''
    DROP TABLE {}
    '''.format(t)
    
    run_command(c)

show_tables()


# ## Final Result is my schema
# 
# <img src="MLB Schema.png">

# In[ ]:




