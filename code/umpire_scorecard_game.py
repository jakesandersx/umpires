import matplotlib
matplotlib.use('Agg')
import requests
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc, ConnectionPatch
from pybaseball import statcast_single_game, playerid_reverse_lookup
import pandas as pd
import numpy as np
import os
import warnings
import mysql.connector
warnings.filterwarnings("ignore", message="Setting the 'color' property will override the edgecolor or facecolor properties.")

# initializing globals
file_paths = []
strike_count = 0
ball_count = 0
missed_strike_count = 0
missed_ball_count = 0
total_calls = 0
total_misses = 0
strike_accuracy = 0
ball_accuracy = 0
total_accuracy = 0

# function to reset scores and file paths, only used for massive data gathering
def reset(id):
    id.file_paths = []
    id.strike_count = 0
    id.ball_count = 0
    id.missed_strike_count = 0
    id.missed_ball_count = 0
    id.total_calls = 0
    id.total_misses = 0
    id.strike_accuracy = 0
    id.ball_accuracy = 0
    id.total_accuracy = 0
    plt.close()



# getting basic game information given the same game_id as the scorecards function
def get_game_info(game_id):

    try:
        url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
        response = requests.get(url)
        data = response.json()

        stadium_name = data['teams']['home']['team']['venue']['name']
        city = data['teams']['home']['team']['locationName']
        time = data['info'][-5]['value']

        return stadium_name, city, time

    except Exception as e:
        for file_path in file_paths:
            with open(file_path, "a") as file:
                print(f'Error: {e}')
                file.write('Error in retrieving pitch data')


# getting the name of home plate umpire from the same game_id
def get_home_plate_umpire(game_id):
    try:
        url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"

        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            umpires = data['officials']
            umpire = next((official['official']['fullName'] for official in umpires if official['officialType'] == 'Home Plate'), None)

            if umpire:
                return umpire
            else:
                return "Home plate umpire information not found"
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        for file_path in file_paths:
            with open(file_path, "a") as file:
                print(f'Error: {e}')
                file.write('Error in filing')



# getting game information
def plot_game(game_id: int):
    try:
        data = statcast_single_game(game_id)

        # initializing variables to defaults in case they are unreadable from the json data
        away_color = 'black'
        home_color = 'black'


        stadium_name, city, time = get_game_info(game_id)

        storing_game_data = data['game_date'].unique()[0]
        storing_game_data = storing_game_data.strftime('%Y-%m-%d').replace(':', '_')
        storing_year = storing_game_data.split("-")[0] # Replace colons with underscores
        game_date = data['game_date'].unique()[0].strftime('%B %d, %Y')  # Format game date
        home_team = data['home_team'].values[0]
        away_team = data['away_team'].values[0]

        home_score = data['home_score'].values[0]
        away_score = data['away_score'].values[0]

        umpire = get_home_plate_umpire(game_id)


        # creating file paths and appending to list to write to later
        #-----------------------------------------------------------------------------------------------------------
        file_path1 = f"../masterfiles/{storing_year}/umpire_files/{umpire}/descriptions/{storing_game_data}_{home_team}_{away_team}.txt"
        file_paths.append(file_path1)
        file_path2 = (f'../masterfiles/{storing_year}/teams/{home_team}/descriptions/{storing_game_data}_vs_{away_team}.txt')
        file_paths.append(file_path2)
        file_path3 = (f'../masterfiles/{storing_year}/teams/{away_team}/descriptions/{storing_game_data}_at_{home_team}.txt')
        file_paths.append(file_path3)


        txt1 = f"../masterfiles/{storing_year}/umpire_files/{umpire}/descriptions"
        txt2 = f"../masterfiles/{storing_year}/teams/{home_team}/descriptions"
        txt3 = f"../masterfiles/{storing_year}/teams/{away_team}/descriptions"

        scorecard1 = f"../masterfiles/{storing_year}/umpire_files/{umpire}/scorecards"
        scorecard2 = f"../masterfiles/{storing_year}/teams/{home_team}/scorecards"
        scorecard3 = f"../masterfiles/{storing_year}/teams/{away_team}/scorecards"
        #-----------------------------------------------------------------------------------------------------------

        # making directories if they do not exist
        os.makedirs(txt1, exist_ok=True)
        os.makedirs(txt2, exist_ok=True)
        os.makedirs(txt3, exist_ok=True)

        os.makedirs(scorecard1, exist_ok=True)
        os.makedirs(scorecard2, exist_ok=True)
        os.makedirs(scorecard3, exist_ok=True)

        # left and right edge of strike zone - universal
        SZ_LEFT = -0.75
        SZ_RIGHT = 0.75

        # plot initializing
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_xlim(-2, 2)
        ax.set_ylim(0, 5)
        ax.set_aspect('equal')
        ax.axis('off')

        sz_bot_avg = np.mean(data['sz_bot'])
        sz_top_avg = np.mean(data['sz_top'])
        strike_zone_box = Rectangle((SZ_LEFT, sz_bot_avg), SZ_RIGHT - SZ_LEFT,
                                    sz_top_avg - sz_bot_avg,
                                    linewidth=1, edgecolor='none', facecolor='lightgray')
        ax.add_patch(strike_zone_box)
        zone_width = (SZ_RIGHT - SZ_LEFT) / 3
        zone_height = (sz_top_avg - sz_bot_avg) / 3
        for i in range(3):
            for j in range(3):
                zone_left = SZ_LEFT + i * zone_width
                zone_bottom = sz_bot_avg + j * zone_height
                zone_rect = Rectangle((zone_left, zone_bottom), zone_width, zone_height,
                                      linewidth=1, edgecolor='black', facecolor='none')
                ax.add_patch(zone_rect)
        # creating the boxes inside of the zone


        # grading the umpire using pre-determined scenarios
        def calculate_missed_call_score(call, miss=None):
            global strike_count, missed_strike_count, ball_count, missed_ball_count

            if call == 'S':
                strike_count += 1
                if miss == 'Y':
                    missed_ball_count += 1
            elif call == 'B':
                ball_count += 1
                if miss == 'Y':
                    missed_strike_count += 1

            total_calls = strike_count + ball_count
            total_misses = missed_strike_count + missed_ball_count


            return ball_count, strike_count, missed_ball_count, missed_strike_count, total_calls, total_misses


        def calculate_colors():
            global total_calls, total_misses, strike_accuracy, ball_accuracy, total_accuracy, total_color, strike_color, ball_color

            total_calls = strike_count + ball_count
            total_misses = missed_strike_count + missed_ball_count

            strike_accuracy = int(100*((strike_count - missed_strike_count) / strike_count))
            ball_accuracy = int(100*((ball_count - missed_ball_count) / ball_count))
            total_accuracy = int(100*((total_calls - total_misses) / total_calls))

            strike_color = 'green' if strike_accuracy >= 94 else 'orange' if strike_accuracy >= 85 else 'red'
            ball_color = 'green' if ball_accuracy >= 94 else 'orange' if ball_accuracy >= 85 else 'red'
            total_color = 'green' if total_accuracy >= 94 else 'orange' if total_accuracy >= 85 else 'red'

            return strike_color, ball_color, total_color


        #return player name given player_id
        def get_player_name_rl(player_id: int):
            name = playerid_reverse_lookup([player_id])
            first_name = name['name_first'].values[0].capitalize()
            last_name = name['name_last'].values[0].capitalize()
            return f"{first_name} {last_name}"

        # scorecards functionality to draw pitches on the plot
        def plot_pitch(pitch, sz_top, sz_bottom, sz_left, sz_right, max_distance=1.65):
            x = pitch['plate_x']
            y = pitch['plate_z']

            if not pitch.empty:
                # if pitch is called a strike but is outside calculated strike zone
                if pitch['type'] == 'S':
                    if not (sz_left <= x <= sz_right and sz_bottom <= y <= sz_top):
                        distance_outside_zone = max(
                            abs(x - sz_left),
                            abs(x - sz_right),
                            abs(y - sz_bottom),
                            abs(y - sz_top)
                        )
                        #check pitch location
                        if distance_outside_zone <= max_distance:
                            circle = Circle((x, y), radius=0.12, linewidth=0.75, edgecolor='black', facecolor='red')
                            ax.add_patch(circle)

                            # number of patches plotted so far
                            pitch_number = len(ax.patches) - 10

                            # label the pitch with a number inside the circle
                            ax.text(x, y, str(pitch_number), color='black', ha='center', va='center', fontsize=9)

                            # write data to all files for given pitch
                            for file_path in file_paths:
                                with open(file_path, "a") as file:
                                    file.write("Missed call:\n")
                                    file.write(f"  Pitch number: {pitch_number}\n")
                                    file.write(f"  Pitcher: {get_player_name_rl(pitch['pitcher'])}\n")
                                    file.write(f"  Batter: {get_player_name_rl(pitch['batter'])}\n")
                                    file.write(f"  Velocity: {pitch['release_speed']} mph\n")
                                    file.write(f"  Inning: {pitch['inning']}\n")
                                    file.write(f"  Count: {pitch['balls']}-{pitch['strikes']}\n")
                                    file.write(f"  Base Runners: {get_base_runners(pitch)}\n")
                                    file.write("  Ball that was called a strike\n")
                                    file.write("============================\n")
                            file.close()
                            '''description = mysql.connector.connect(
                                user='your_user',
                                password='your_pass',
                                host='your_host',
                                database='your_db',
                                auth_plugin='your_pass'
                            )
                            cursor = description.cursor()
                            insert_data = "INSERT INTO descriptions(game_id, missed_call, pitcher, batter, velocity, inning, count, base_runners, caption) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                            description_data = (game_id, pitch_number, get_player_name_rl(pitch['pitcher']), get_player_name_rl(pitch['batter']),
                            pitch['release_speed'], pitch['inning'], f"{pitch['balls']}-{pitch['strikes']}",
                            get_base_runners(pitch), 'Ball was called a strike')
                            cursor.execute(insert_data, description_data)
                            description.commit()
                            description.close()'''

                            calculate_missed_call_score('S', 'Y')
                        calculate_missed_call_score('S')

                            # if pitch is called a ball but is inside calculated strike zone
                elif pitch['type'] == 'B':
                    if (sz_left <= x <= sz_right and sz_bottom <= y <= sz_top):
                        circle = Circle((x, y), radius=0.12, linewidth=0.75, edgecolor='black', facecolor='green')
                        ax.add_patch(circle)

                        pitch_number = len(ax.patches) - 10     # number of patches plotted so far

                        #label the pitch with a number inside the circle
                        ax.text(x, y, str(pitch_number), color='black', ha='center', va='center', fontsize=9)

                        # write data to all files for given pitch
                        for file_path in file_paths:
                            with open(file_path, "a") as file:
                                file.write("Missed call:\n")
                                file.write(f"  Pitch number: {pitch_number}\n")
                                file.write(f"  Pitcher: {get_player_name_rl(pitch['pitcher'])}\n")
                                file.write(f"  Batter: {get_player_name_rl(pitch['batter'])}\n")
                                file.write(f"  Velocity: {pitch['release_speed']} mph\n")
                                file.write(f"  Inning: {pitch['inning']}\n")
                                file.write(f"  Count: {pitch['balls']}-{pitch['strikes']}\n")
                                file.write(f"  Base Runners: {get_base_runners(pitch)}\n")
                                file.write("  Strike that was called a ball\n")
                                file.write("============================\n")
                        file.close()
                        '''description = mysql.connector.connect(
                            user='your_user',
                            password='your_pass',
                            host='your_host',
                            database='your_db',
                            auth_plugin='your_pass'
                        )
                        cursor = description.cursor()
                        insert_data = "INSERT INTO descriptions(game_id, missed_call, pitcher, batter, velocity, inning, count, base_runners, caption) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        description_data = (game_id, pitch_number, get_player_name_rl(pitch['pitcher']), get_player_name_rl(pitch['batter']), pitch['release_speed'], pitch['inning'], f"{pitch['balls']}-{pitch['strikes']}", get_base_runners(pitch), 'Strike was called a ball')
                        cursor.execute(insert_data, description_data)
                        description.commit()
                        description.close()'''

                        calculate_missed_call_score('B', 'Y')
                    calculate_missed_call_score('B')

            else:
                print('No pitch data')

        # base runner data for descriptions files and weighted_score calculations
        def get_base_runners(pitch):
            try:
                on_1b = pitch['on_1b']
                on_2b = pitch['on_2b']
                on_3b = pitch['on_3b']
                base_runners = []

                if pd.notnull(on_1b):
                    base_runners.append(f"{get_player_name_rl(on_1b)} on 1st")
                if pd.notnull(on_2b):
                    base_runners.append(f"{get_player_name_rl(on_2b)} on 2nd")
                if pd.notnull(on_3b):
                    base_runners.append(f"{get_player_name_rl(on_3b)} on 3rd")
                if not base_runners:
                    base_runners.append(f"None")

                return ', '.join(base_runners)
            except Exception as e:
                for file_path in file_paths:
                    with open(file_path, "a") as file:
                        print(f'Error: {e}')
                        file.write('Error in retrieving pitch data')

        # plotting all missed pitches on the plot
        try:
            for _, pitch in data.iterrows():
                plot_pitch(pitch, data['sz_top'].values[0], data['sz_bot'].values[0], SZ_LEFT, SZ_RIGHT)
        except KeyError as e:
            print(f"Error: {e}")

        # getting average strike zone height to make most accurate zone given a game
        # dictionary for mlb teams and their colors - used to give each team their assigned color on the plot
        mlb_team_colors = {
            'ARI': 'Red',
            'ATL': 'Red',
            'BAL': 'Orange',
            'BOS': 'Red',
            'CWS': 'Black',
            'CHC': 'Blue',
            'CIN': 'Red',
            'CLE': 'Navy',
            'COL': 'Purple',
            'DET': 'Navy',
            'HOU': 'Orange',
            'KCR': 'RoyalBlue',
            'LAA': 'Red',
            'LAD': 'DodgerBlue',
            'MIA': 'Teal',
            'MIL': 'Gold',
            'MIN': 'Navy',
            'NYY': 'Navy',
            'NYM': 'Blue',
            'OAK': 'Green',
            'PHI': 'Red',
            'PIT': 'Gold',
            'SDD': 'Brown',
            'SFG': 'Orange',
            'SEA': 'Navy',
            'STL': 'Red',
            'TBR': 'Navy',
            'TEX': 'Blue',
            'TOR': 'Blue',
            'WSH': 'Red'
        }

        #dictionary for mlb teams and their cities - used to plot home team city on png
        mlb_team_cities = {
            "Phoenix": "AZ",
            "Atlanta": "GA",
            "Baltimore": "MD",
            "Boston": "MA",
            "Chicago": "IL",
            "Cincinnati": "OH",
            "Cleveland": "OH",
            "Denver": "CO",
            "Detroit": "MI",
            "Houston": "TX",
            "Kansas City": "MO",
            "Anaheim": "CA",
            "Los Angeles": "CA",
            "Miami": "FL",
            "Milwaukee": "WI",
            "Minneapolis": "MN",
            "New York City": "NY",
            "Oakland": "CA",
            "Philadelphia": "PA",
            "Pittsburgh": "PA",
            "San Diego": "CA",
            "San Francisco": "CA",
            "Seattle": "WA",
            "St. Louis": "MO",
            "Tampa Bay": "FL",
            "Arlington": "TX",
            "Toronto": "ON",
            "Washington, D.C.": "DC"
        }

        if home_team in mlb_team_colors:
            home_color = mlb_team_colors[home_team]

        if away_team in mlb_team_colors:
            away_color = mlb_team_colors[away_team]


        def draw_partial_circle(percentage, x, y, color):

            # calculate the extent of the circle based on the percentage and add it to the plot
            extent = 360 * percentage / 100
            circle = Arc((x, y), 0.65, 0.65, theta1=0, theta2=extent, edgecolor='black', linewidth=4, color=color)
            ax.add_patch(circle)

        # draw extra plot data such as game information and legend
        #---------------------------------------------------------------------------------------------------------------------
        calculate_colors()
        ax.annotate(f"{game_date}", xy=(0.7, 4.6), fontsize=12, weight='bold')
        ax.annotate(f"{time[:-1]}", xy=(1.0, 4.25), fontsize=12, weight='bold')

        ax.annotate(f"{home_team}", xy=(-1.7, 4.6), fontsize=11, color=home_color, weight='bold')
        ax.annotate(f" vs ", xy=(-1.28, 4.6), fontsize=11, color='black', weight='bold')
        ax.annotate(f"{away_team}", xy=(-0.94, 4.6), fontsize=11, color=away_color, weight='bold')

        ax.annotate(f"{home_score}", xy=(-1.4, 4.25), fontsize=11, color=home_color, weight='bold')
        ax.annotate(f" - ", xy=(-1.21, 4.25), fontsize=11, color='black', weight='bold')
        ax.annotate(f"{away_score}", xy=(-1, 4.25), fontsize=11, color=away_color, weight='bold')

        #ax.annotate(f"{location}", xy=(-1.79, 3.8), fontsize=11, color=home_color, weight='bold')

        ax.annotate(f"{umpire}", xy=(-1, 5), fontsize=18, weight='bold')
        ax.annotate(f"  Called\n    Ball\nAccuracy", xy=(-2, 0.8), fontsize=14, weight='bold')
        draw_partial_circle(strike_accuracy, -0.5, 1.12, strike_color)
        ax.annotate(f"{strike_accuracy}%", xy=(-0.73, 1.04), fontsize=14, weight='bold', color=strike_color)

        draw_partial_circle(total_accuracy, 0, 4.4, total_color)
        ax.annotate(f"{total_accuracy}%", xy=(-0.23, 4.32), fontsize=14, weight='bold', color=total_color)
        ax.annotate(f"Total Accuracy", xy=(-0.8, 3.8), fontsize=13, weight='bold', color='black')


        ax.annotate(f"{missed_strike_count} of {ball_count} called balls\n  were true strikes", xy=(-1.7, 0.2), fontsize=9, weight='bold')

        draw_partial_circle(ball_accuracy, 0.5, 1.12, ball_color)
        ax.annotate(f"{ball_accuracy}%", xy=(0.27, 1.04), fontsize=14, weight='bold', color=ball_color)
        ax.annotate(f"  Called\n  Strike\nAccuracy", xy=(1, 0.8), fontsize=14, weight='bold')
        ax.annotate(f"{missed_ball_count} of {strike_count} called strikes\n    were true balls", xy=(0.2, 0.2), fontsize=9, weight='bold')

        ax.annotate(f"Green", xy=(-1.65, 3), fontsize=11, color='green', weight='bold')
        green_line = ConnectionPatch((-1.7, 2.95), (-1, 2.95), "data", "data", linewidth=1.5, arrowstyle='-', color='green')
        ax.add_artist(green_line)
        ax.annotate(f"Strikes that\nwere called\n     balls", xy=(-1.72, 2.55), fontsize=7.5, color='black', weight='bold')
        ax.annotate(f"Red", xy=(1.05, 3), fontsize=11, color='red', weight='bold')
        red_line = ConnectionPatch((1, 2.95), (1.5, 2.95), "data", "data", linewidth=1.5, arrowstyle='-', color='red')
        ax.add_artist(red_line)
        ax.annotate(f" Balls that\nwere called\n  strikes", xy=(0.93, 2.55), fontsize=7.5, color='black', weight='bold')
        # ----------------------------------------------------------------------------------------------------------------------

        plt.savefig(f'../masterfiles/{storing_year}/umpire_files/{umpire}/scorecards/{storing_game_data}_{home_team}_{away_team}.png',
                    dpi=300)
        plt.savefig(f'../masterfiles/{storing_year}/teams/{home_team}/scorecards/{storing_game_data}_vs_{away_team}.png', dpi=300)
        plt.savefig(f'../masterfiles/{storing_year}/teams/{away_team}/scorecards/{storing_game_data}_at_{home_team}.png', dpi=300)

        plt.savefig('image.png')
        with open('image.png', 'rb') as file:
            image = file.read()


        '''recap = mysql.connector.connect(
            user='your_user',
            password='your_pass',
            host='your_host',
            database='your_db',
            auth_plugin='your_pass'
        )

        # insert data into mysql database
        cursor = recap.cursor()
        insert_data = "INSERT INTO recap(game_id, umpire_name, home_team, away_team, total_score, strike_score, ball_score, total_strikes, total_balls, missed_strikes, missed_balls, date, scorecard) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        umpire_data = (game_id, umpire, home_team, away_team, total_accuracy, strike_accuracy, ball_accuracy, strike_count, ball_count, missed_strike_count, missed_ball_count, storing_game_data, image)
        cursor.execute(insert_data, umpire_data)
        recap.commit()
        recap.close()'''


        # saving the plots as png images with their respective names in their respective file directories
        plt.savefig(f'../masterfiles/{storing_year}/umpire_files/{umpire}/scorecards/{storing_game_data}_{home_team}_{away_team}.png', dpi=300)
        plt.savefig(f'../masterfiles/{storing_year}/teams/{home_team}/scorecards/{storing_game_data}_vs_{away_team}.png', dpi=300)
        plt.savefig(f'../masterfiles/{storing_year}/teams/{away_team}/scorecards/{storing_game_data}_at_{home_team}.png', dpi=300)

        plt.close(fig)

    # error handling
    except Exception as e:
        for file_path in file_paths:
            with open(file_path, "a") as file:
                print(f'Error: {e}')
                file.write('Error in retrieving pitch data')

    # after all pitch data is written to file, write a recap of the game with basic info
    try:
        for file_path in file_paths:
            with open(file_path, "a") as file:
                file.write("\n\nGame Recap\n")
                file.write(f"{home_team} vs {away_team}\n")
                file.write(f"{home_score} - {away_score}\n")
                file.write(f"Umpire: {umpire} - {total_accuracy}% accuracy")
                file.write(f"Strike Accuracy: {strike_accuracy}% | Ball Accuracy: {ball_accuracy}")
                file.write(f"Total Balls/Strikes Called: {ball_count}, {strike_count}")
                file.write(f"Missed Balls/Strikes: {missed_ball_count}, {missed_strike_count}")

    # error handling
    except UnboundLocalError as e:
        with open(file_path, "a") as file:
            file.write("\n\nGame Recap\n")
            file.write(f"{home_team} vs {away_team}\n")
            file.write(f"{home_score} - {away_score}\n")
            file.write(f"Umpire: {umpire} - {total_accuracy}% accuracy")
            print(f'Error: {e}')
            file.write('local variable error')


'''
comment this code out
if using any of the 
any_games_xxx.py files
for data gathering
'''
plot_game(717916)