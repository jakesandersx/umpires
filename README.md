# Grading MLB Umpires

# Important Note

This idea was 100% stolen from [UmpireScorecards](https://www.umpscorecards.com). Please check them out
and give them the credit they deserve. I wrote this code simply
to challenge myself using Python.

# Overview

This project aims to develop a Python program that grades MLB umpires based on their performance. The program will leverage available MLB data, such as Statcast pitch data, to evaluate umpires' accuracy and consistency in making calls. By analyzing various factors, including correct calls, incorrect calls, and the impact of those calls on game outcomes, the program will generate a comprehensive grading system for umpires.

The grading process will involve calculating metrics such as accuracy percentage on both balls and strikes, and generate an overall performance rating for each umpire. These metrics will provide objective measures of an umpire's decision-making abilities and their impact on the game. Ultimately, the Python program will provide valuable insights into umpires' performance and contribute to enhancing the quality and integrity of officiating in MLB.



### What this project offers

This project will take a given game, and output 2 items:<br>
1. Visual of every missed call from a game
2. A .txt file explaining details behind every call

The file will create a new folder in the parent directory of the file and place all of the data in this folder.

The visual image will provide basic information, such as what teams played,
who was the home plate umpire, and will locate all of the missed calls
from that game on a strike zone. 

The .txt file given will go into more detail and explain details from every call,
such as the count, who the batter/pitcher were, how many base runners were on,
and the speed of the pitch from every missed call.

### Data Scraping

All pitch data is scraped using Statcast pitch data from the  `pybaseball` library. Other data, such as reference data,
umpire names, and more is gathered from MLB's official [API](https://statsapi.mlb.com/). A link to pybaseball's github can be found [here](https://github.com/jldbc/pybaseball).


# Requirements
- Python 3.x
- `pybaseball` library

# Installation
1. Clone this repository or download the project as a zip file.

2. Install the required dependencies by running the following command: `pip install pybaseball`

# Usage
1. Import the necessary modules:
```
from pybaseball import statcast_single_game, playerid_reverse_lookup
import requests
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc, ConnectionPatch
import pandas as pd
import numpy as np
import os
import warnings
```
### Optional Modules

If wanting to store data via MySQL:
```
import mysql.connector
```


And uncomment all of the MySQL code within the `umpire_scorecard_game.py` Be sure to also change all `mysql.connector.connect()` data to your corresponding database and table information.

2. Inside of `umpire_scorecard_game`, define the game you wish to find (found with MLB Advanced Media) and call it with the main
function:

`plot_game(717911)`


# Large Dataset Gathering
To gather large amounts of data, I have created 3 files: `all_games_xxx.py`, which can get all data from a given day, month, or year, respectively. I have also commented out code within `all_games_year` which includes a list and a for loop to 
gather data from multiple years - uses `years.py` to automatically get start and end dates of a specified 
year. However, `years.py` only accounts for the regular season, and will not track any games from the Postseason
or Spring Training. If you wish to find data for any of those games, you must manually change the dates.

All data that you wish to track will automatically be stored locally to your PC.
To find the data, go to the parent directory of your code and locate `masterfiles`. From there, you can sort by year, and then by individual teams and umpires.
I have provided a few examples from the 2023 season which shows the final results of the code.




# Important Notes:
The top and bottom of every strike zone is approximated. This is taken by retrieving
the top and botttom of every hitter's strike zone within a given game, and approximating
a strike zone based on the average from all of the data. That being said, the code is far from perfect
and can occasionally miss pitches.

For this code, data must be used from the 2015 season-onward, as 2015 was the
first season that Statcast began tracking pitches, which is how
this data is gathered.
