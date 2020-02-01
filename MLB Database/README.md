# Designing Database for Major League Baseball
For this assignment I will be working with a file of Major League Baseball games from Retrosheet. Retrosheet compiles detailed statistics on baseball games from the 1800s through to today. The main file I will be working from game_log.csv, has been produced by combining 127 separate CSV files from retrosheet, and has been pre-cleaned to remove some inconsistencies. The game log has hundreds of data points on each game which I will normalize into several separate tables using SQL, providing a robust database of game-level statistics.

In addition to the main file, I have also included three 'helper' files, also sourced from Retrosheet:

  - park_codes.csv
  - person_codes.csv
  - team_codes.csv
These three helper files in some cases contain extra data, but will also make things easier as they will form the basis for three of our normalized tables.

I will begin exploring the data by using pandas to read and explore the data. Setting the following options after I import pandas is recommended– they will prevent the DataFrame output from being truncated, given the size of the main game log file

# Overview

  1. Explore each table in python
  2. Importing Data into SQLite
  3. Create primary key
  4. Look for normalization opportunities
  5. Design normalization table
  6. Create tables without foreign keys
  7. Create tables
  8. Remove old tables
 
