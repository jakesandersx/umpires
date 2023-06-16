import umpire_scorecard_game
import requests
from datetime import datetime

def format_date(date_string):
    date = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
    formatted_date = date.strftime("%B %d, %Y")
    return formatted_date

def get_game_info(date):
    base_url = "https://statsapi.mlb.com/api/v1/schedule"
    params = {
        "sportId": 1,  # 1 represents MLB
        "date": date  # Format: "YYYY-MM-DD"
    }

    response = requests.get(base_url, params=params)
    data = response.json()
    #print(data)

    games_info = []
    for date in data['dates']:
        for game in date['games']:
            game_info = {
                'game_id': game['gamePk'],
                'home_team': game['teams']['home']['team']['name'],
                'away_team': game['teams']['away']['team']['name'],
                # 'away_score': game['teams']['away']['score'],
                # 'home_score': game['teams']['home']['score'],
                'date': format_date(game['gameDate'])
            }
            games_info.append(game_info)

    for game in games_info:
        umpire_scorecard_game.plot_game(game['game_id'])
        umpire_scorecard_game.reset(umpire_scorecard_game)
        print(f"Game ID: {game['game_id']}")
        print(f"Home Team: {game['home_team']}")
        print(f"Away Team: {game['away_team']}")
        print(f"Date: {game['date']}")
        print("------------------")

# Example usage
date = "2023-06-03"
get_game_info(date)