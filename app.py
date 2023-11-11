import os
import base64
import json
import requests
import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
app = Flask(__name__)
CORS(app) 

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, time, timedelta

# Create an instance of the scheduler
scheduler = BackgroundScheduler()

# Define the job to run the fetch_results() function every 2 minutes within certain time windows
def run_fetch_results_every_2_minutes():
    now = datetime.utcnow()
    time_windows = [
        (time(2, 25), time(2, 55)),
        (time(10, 25), time(10, 55)),
        (time(18, 25), time(18, 55))
    ]

    for start_time, end_time in time_windows:
        start_datetime = datetime.combine(now.date(), start_time)
        end_datetime = datetime.combine(now.date(), end_time)

        # If the current time has passed the end time for today, schedule for the next day
        if now.time() > end_time:
            start_datetime += timedelta(days=1)
            end_datetime += timedelta(days=1)

        scheduler.add_job(
            fetch_results,
            trigger='interval',
            minutes=2,
            start_date=start_datetime,
            end_date=end_datetime
        )

# Start the scheduler
scheduler.start()

# Define the fetch_results() function that contains your main code to fetch and process the results
def fetch_results():
    import requests
    import json
    import base64
    import re
    import pytz
    from datetime import datetime, timedelta
    import uuid
    import dotenv
    import os
    from dotenv import load_dotenv
    import base64

    # Define the base URL
    base_url = 'https://competition.trackmania.nadeo.club/api/competitions?length={}&offset={}'
    results_url = 'https://competition.trackmania.nadeo.club/api/competitions/{}/rounds'
    participants_url = 'https://club.trackmania.nadeo.club/api/matches/{}/results'
    matches_url = 'https://competition.trackmania.nadeo.club/api/rounds/{}/matches'
    display_names_url = 'https://prod.trackmania.core.nadeo.online/accounts/displayNames/?accountIdList={}'

    # Load environment variables from .env
    load_dotenv()

    # Define the regex
    pattern = re.compile(r'^SRoyal 202\d-\d\d-\d\d #\d')

    # Get the email and password from environment variables
    email = os.environ.get("EMAIL")
    password = os.environ.get("PASSWORD")
    credentials = f"{email}:{password}"
    credentials_encoded = base64.b64encode(credentials.encode()).decode()

    headers_ubisoft = {
        "Content-Type": "application/json",
        "Ubi-AppId": "86263886-327a-4328-ac69-527f0d20a237",
        "Authorization": f"Basic {credentials_encoded}",
        "User-Agent": "Trackmania Royal Fan Site / lotnead@protonmail.com"
    }

    try:
        # Send POST request to Ubisoft
        print("Sending POST request to Ubisoft")
        response = requests.post("https://public-ubiservices.ubi.com/v3/profiles/sessions", headers=headers_ubisoft)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Something went wrong", err)

    # Get the Ubisoft authentication ticket
    ubi_ticket = response.json().get('ticket')

    # Set up headers for Nadeo
    headers_nadeo = {
        "Content-Type": "application/json",
        "Authorization": f"ubi_v1 t={ubi_ticket}",
        "User-Agent": "Trackmania Royal Fan Site / lotnead@protonmail.com"
    }

    body_nadeo_club = {
        "audience": "NadeoClubServices"
    }

    body_nadeo_services = {
        "audience": "NadeoServices"
    }
    body_nadeo_live = {
        "audience": "NadeoServices"
    }

    try:
        # Send POST request to Nadeo for LiveServices token
        response_nadeo_live = requests.post("https://prod.trackmania.core.nadeo.online/v2/authentication/token/ubiservices",
                                            headers=headers_nadeo, data=json.dumps(body_nadeo_live))
        response_nadeo_live.raise_for_status()

        # Send POST request to Nadeo for Services token
        response_nadeo_services = requests.post("https://prod.trackmania.core.nadeo.online/v2/authentication/token/ubiservices",
                                                headers=headers_nadeo, data=json.dumps(body_nadeo_services))
        response_nadeo_services.raise_for_status()
        
        # Send POST request to Nadeo for ClubServices token
        response_nadeo_club = requests.post("https://prod.trackmania.core.nadeo.online/v2/authentication/token/ubiservices",
                                            headers=headers_nadeo, data=json.dumps(body_nadeo_club))
        response_nadeo_club.raise_for_status()

    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Something went wrong", err)

    def get_access_token():
        token_url = "https://api.trackmania.com/api/access_token"
        payload = {
            'grant_type': 'client_credentials',
            'client_id': os.environ.get("CLIENT_ID"),
            'client_secret': os.environ.get("CLIENT_SECRET")
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            response = requests.post(token_url, headers=headers, data=payload)
            response.raise_for_status()
            token_data = response.json()
            return token_data.get('access_token')
        except requests.exceptions.HTTPError as err:
            print(f"HTTP Error: {err}")
        except requests.exceptions.RequestException as err:
            print(f"Error: {err}")
        return None

    # Get the access tokens
    access_token_live = response_nadeo_live.json().get('accessToken')
    access_token_services = response_nadeo_services.json().get('accessToken')
    access_token_club = response_nadeo_club.json().get('accessToken')

    # Set headers for game API
    headers_game = {
        "Authorization": f"nadeo_v1 t={access_token_club}",
    }

    # Fetch competitions in batches
    offset = 0
    length = 50  # Set this to the number of competitions you want to retrieve
    base_url = 'https://competition.trackmania.nadeo.club/api/competitions?length={}&offset={}'

    # Make the request
    print("Fetching competitions")
    response = requests.get(base_url.format(length, offset), headers=headers_game)

    # Ensure the request was successful
    if response.status_code != 200:
        print('Request failed with status code', response.status_code)

    # Load the data from the response
    data = json.loads(response.text)

    # Assign all fetched competitions to unsorted_competitions
    unsorted_competitions = data

    # Search for the competition
    competitions = [competition for competition in data if pattern.match(competition['name']) and not any(x in competition['name'] for x in ['xbl', 'luna', 'psn', 'pc'])]

    # Get the current UTC time
    current_time = datetime.now(pytz.utc)

    # Sort the competitions by their time difference from the current time
    #competitions.sort(key=lambda x: abs(datetime.fromtimestamp(x['endDate']/1000, pytz.utc) - current_time))

    # Filter competitions that have matches already generated
    competitions_with_matches_generated = [comp for comp in competitions if datetime.fromtimestamp(comp['matchesGenerationDate'], pytz.utc) <= current_time]

    # If no competitions have matches already generated, take the last one (the one closest to the current time)
    if not competitions_with_matches_generated:
        closest_competition = competitions[-1]
    else:
        # Sort competitions with matches already generated by their time difference from the current time
        competitions_with_matches_generated.sort(key=lambda x: abs(datetime.fromtimestamp(x['matchesGenerationDate'], pytz.utc) - current_time))
        closest_competition = competitions_with_matches_generated[0]

    # Get the ID of the closest competition
    closest_competition_id = closest_competition['liveId']
    closest_competition_idtag = closest_competition['id']

    # Fetch the results for the closest competition
    print("Fetching results for the closest competition")
    response = requests.get(results_url.format(closest_competition_id), headers=headers_game)

    # Ensure the request was successful
    if response.status_code != 200:
        print('Request failed with status code', response.status_code)
    else:
        # Write the results to a JSON file
        with open('newest_winner_rounds.json', 'w') as f:
            json.dump(response.json(), f, indent=4)

    # Write all competitions to a JSON file
    with open('competitions_unsorted.json', 'w') as f:
        json.dump(unsorted_competitions, f, indent=4)

    # Write selected competitions to a JSON file
    with open('competitions.json', 'w') as f:
        json.dump(competitions, f, indent=4)

    # Load the rounds from the newest_winner_rounds.json file
    with open('newest_winner_rounds.json', 'r') as f:
        rounds = json.load(f)
    # Load the rounds from the newest_winner_rounds.json file
    with open('newest_winner_rounds.json', 'r') as f:
        rounds = json.load(f)

    # Define the matches URL
    matches_url = 'https://competition.trackmania.nadeo.club/api/rounds/{}/matches'

    # For each round, get the matches
    for round in rounds:
        round_id = round.get('id')

        if round_id:
            # Fetch the matches for the round
            response = requests.get(matches_url.format(round_id), headers=headers_game)
            print(f"Fetching matches for round {round_id}... Response: {response.status_code}")

            # Ensure the request was successful
            if response.status_code != 200:
                print(f'Request failed with status code {response.status_code} for round {round_id}')
            else:
                # Load the matches from the response
                matches = json.loads(response.text)

                # Save the matches to a JSON file
                with open(f'matches_round_{round_id}.json', 'w') as f:
                    json.dump(matches, f, indent=4)
                    print(f"Matches for round {round_id} saved.")

    # For each round, get the matches
    for round in rounds:
        round_id = round.get('id')

        if round_id:
            # Load the matches from the corresponding JSON file
            with open(f'matches_round_{round_id}.json', 'r') as f:
                matches_data = json.load(f)

            # Fetch the matches from the matches_data
            matches = matches_data['matches']

            # Fetch the access token for display names
            access_token_for_display_names = get_access_token()
            if not access_token_for_display_names:
                print("Failed to obtain access token for display names.")
                return  # or handle this situation appropriately

            # For each match, get the participants
            for match in matches:
                club_match_id = match['id']

                # Fetch the participants for the match using the clubMatchLiveId
                participants_url = f'https://competition.trackmania.nadeo.club/api/matches/{club_match_id}/results?length=60'
                response_participants = requests.get(participants_url, headers=headers_game)
                print(f"Fetching participants for match {club_match_id}... Response: {response_participants.status_code}")

                # Ensure the request was successful
                if response_participants.status_code != 200:
                    print(f'Request failed with status code {response_participants.status_code} for match {club_match_id}')
                else:
                    # Load the participants and teams from the response
                    participants_data = json.loads(response_participants.text)
                    participants = participants_data['results']
                    teams = participants_data['teams']

                    
                    # Extract account IDs from participants
                    account_ids = [participant['participant'] for participant in participants]
                    print(f"Account IDs extracted: {account_ids}")

                    # Fetch display names using account IDs
                    display_names_headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {access_token_for_display_names}",
                        "User-Agent": "Trackmania Royal Fan Site / lotnead@protonmail.com"
                    }

                    # Forming the new URL for display names
                    new_display_names_url = "https://api.trackmania.com/api/display-names"
                    account_ids_params = {'accountId[]': account_ids}

                    # Making the GET request to the new endpoint
                    new_display_names_response = requests.get(new_display_names_url, headers=display_names_headers, params=account_ids_params)

                    # Debugging: Print response details
                    print(f"Display Names API Call - Status Code: {new_display_names_response.status_code}")
                    print(f"Display Names API Call - Response Headers: {new_display_names_response.headers}")
                    print(f"Display Names API Call - Response Body: {new_display_names_response.text}")

                    # Checking and processing the response
                    if new_display_names_response.status_code == 200:
                        new_display_names_data = new_display_names_response.json()
                        print(f"Display Names Response Data: {new_display_names_data}")
                    else:
                        print(f"Failed to fetch display names. Status code: {new_display_names_response.status_code}")
                        new_display_names_data = {}

                    # Loop through participants and update their display names
                    for participant in participants:
                        account_id = participant['participant']
                        display_name = new_display_names_data.get(account_id, 'Unknown')
                        participant['participant'] = display_name  # Replace the account ID with display name

                    # Initialize modified_participants dictionary for each match
                    modified_participants = {
                        "SuperRoyalID": closest_competition_idtag,
                        "SuperRoyalName": closest_competition['name'],
                        "tags": match.get("tags", []),
                        "results": participants,
                        "teams": teams,
                    }

                    # Save modified participants data to a separate JSON file
                    with open(f'modified_participants_match_{club_match_id}.json', 'w') as f:
                        json.dump(modified_participants, f, indent=4)
                    print(f"Modified participants for match {club_match_id} saved.")

                    # Define the list of names based on position
                    names = [
                    { "name": "Flamingo" }, { "name": "Pig" }, { "name": "Clown Fish" }, { "name": "Fox" },
                    { "name": "Octopus" }, { "name": "Butterfly" }, { "name": "Crocodile" }, { "name": "Grasshopper" },
                    { "name": "Ladybug" }, { "name": "Macaw Parrot" }, { "name": "Giraffe" }, { "name": "Bee" },
                    { "name": "Dolphin" }, { "name": "Peafowl" }, { "name": "Kangaroo" }, { "name": "Monkey" },
                    { "name": "Panda" }, { "name": "Zebra" }, { "name": "Rabbit" }, { "name": "Polar Bear" }
                ]
                    # Get the tag and create a filename based on the tags
                    tag = match.get("tags", "")
                    tag_filename = "_".join(tag) if tag else "NoTag"

                    # Replace the team names with the appropriate names based on the "position" field under "teams"
                    for team in modified_participants['teams']:
                        position = team["position"]
                        team_name = names[int(position) % len(names)]["name"]
                        team["RoyalAnimal"] = team_name
                        

                    # Update the "results" section
                    for result in modified_participants['results']:
                        team_id = result['team']
                        for team in modified_participants['teams']:
                            if team['team'] == team_id:
                                result['RoyalAnimal'] = team['RoyalAnimal']
                                result['TeamResult'] = team['rank']
                                break


                    # Save the modified participants data to a separate JSON file based on the tag
                    with open(f'{tag_filename}.json', 'w') as f:
                        json.dump(modified_participants, f, indent=4)
                    print(f"Modified participants for match {club_match_id} saved in {tag_filename}.json")

import datetime
import json
import requests

from apscheduler.schedulers.background import BackgroundScheduler

# Create an instance of the scheduler
scheduler = BackgroundScheduler()

# Define the job to run the fetch_maps_info() function
@scheduler.scheduled_job('cron', hour=18, minute=1, timezone='UTC')
def fetch_maps_info_job():
    fetch_maps_info()

# Start the scheduler
scheduler.start()

def fetch_maps_info():
    import base64
    import os
    from dotenv import load_dotenv
    import requests
    import json
    import datetime


    # Load environment variables from .env
    load_dotenv()

    # Set up your credentials and headers
    email = os.environ.get("EMAIL")
    password = os.environ.get("PASSWORD")
    credentials = f"{email}:{password}"
    credentials_encoded = base64.b64encode(credentials.encode()).decode()


    headers_ubisoft = {
        "Content-Type": "application/json",
        "Ubi-AppId": "86263886-327a-4328-ac69-527f0d20a237",
        "Authorization": f"Basic {credentials_encoded}",
        "User-Agent": "Trackmania Royal Fan Site / lotnead@protonmail.com"
    }

    try:
        # Send POST request to Ubisoft
        response = requests.post("https://public-ubiservices.ubi.com/v3/profiles/sessions", headers=headers_ubisoft)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Something went wrong", err)

    # Get the Ubisoft authentication ticket
    ubi_ticket = response.json().get('ticket')

    # Set up headers for Nadeo
    headers_nadeo = {
        "Content-Type": "application/json",
        "Authorization": f"ubi_v1 t={ubi_ticket}",
    }

    body_nadeo_live = {
        "audience": "NadeoLiveServices"
    }

    body_nadeo_services = {
        "audience": "NadeoServices"
    }

    try:
        # Send POST request to Nadeo for LiveServices token
        response_nadeo_live = requests.post("https://prod.trackmania.core.nadeo.online/v2/authentication/token/ubiservices",
                                            headers=headers_nadeo, data=json.dumps(body_nadeo_live))
        response_nadeo_live.raise_for_status()

        # Send POST request to Nadeo for Services token
        response_nadeo_services = requests.post("https://prod.trackmania.core.nadeo.online/v2/authentication/token/ubiservices",
                                                headers=headers_nadeo, data=json.dumps(body_nadeo_services))
        response_nadeo_services.raise_for_status()

    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Something went wrong", err)

    # Get the access tokens
    access_token_live = response_nadeo_live.json().get('accessToken')
    access_token_services = response_nadeo_services.json().get('accessToken')

    # Set headers for game API
    headers_game = {
        "Authorization": f"nadeo_v1 t={access_token_live}",
    }

    params = {
        "length": 3,
        "offset": 0,
        "royal": True
    }

    try:
        # Get the current Royal Map Pool
        map_list_response = requests.get("https://live-services.trackmania.nadeo.live/api/token/campaign/month",
                                        headers=headers_game, params=params)
        map_list_response.raise_for_status()
        map_list_response = map_list_response.json()

        # Sort the map list by startTimestamp
        map_list_response['monthList'] = sorted(map_list_response['monthList'], key=lambda x: x['days'][0]['startTimestamp'])

        # Get the UIDs for the 30 most recent maps
        all_map_uids = [monthDay['mapUid'] for month in map_list_response['monthList'] for monthDay in month['days'] if
                        'mapUid' in monthDay]

        # Concatenate the map UIDs into a comma-separated string
        map_uids_string = ','.join(all_map_uids)

        # Get map info for each UID
        map_info_url = 'https://prod.trackmania.core.nadeo.online/maps/'
        map_info_headers = {
            'Authorization': f'nadeo_v1 t={access_token_services}'
        }
        map_info_params = {
            'mapUidList': map_uids_string
        }

        try:
            map_info_response = requests.get(map_info_url, headers=map_info_headers, params=map_info_params)
            map_info_response.raise_for_status()
            map_info = map_info_response.json()

            # Get the list of unique account IDs from the map info
            account_ids = list(set([map_data['author'] for map_data in map_info]))

            # Function to retrieve display names from account IDs
            def get_display_names(account_ids):
                display_names_url = "https://prod.trackmania.core.nadeo.online/accounts/displayNames/"
                display_names_params = {
                    "accountIdList": ','.join(account_ids)
                }

                try:
                    response = requests.get(display_names_url, headers=map_info_headers, params=display_names_params)
                    response.raise_for_status()
                    display_names = response.json()
                    return display_names
                except requests.exceptions.RequestException as e:
                    print(f"Error during getting display names: {e}")
                    return []

            # Get display names corresponding to the account IDs
            display_names = get_display_names(account_ids)

            # Update the map info with author's display name and startTimestamp
            for map_data in map_info:
                author_account_id = map_data['author']
                # Find the display name for the author's account ID
                author_display_name = next(
                    (display_name['displayName'] for display_name in display_names if
                    display_name['accountId'] == author_account_id), 'Nadeo')
                # Update the authorDisplayName and startTimestamp in map data
                map_data['authorDisplayName'] = author_display_name
                map_data['startTimestamp'] = next(
                    (monthDay['startTimestamp'] for month in map_list_response['monthList'] for monthDay in month['days'] if
                    monthDay['mapUid'] == map_data['mapUid']), None)

            # Sort the map info by startTimestamp
            map_info = sorted(map_info, key=lambda x: x['startTimestamp'], reverse=True)

            # Take only the newest 20 map objects
            map_info = map_info[:20]

            # Define the days of the week when maps enter
            entry_days_of_week = [0, 2, 5]  # Monday: 0, Wednesday: 2, Saturday: 5

            # Generate the entry days for the next 20 maps
            all_map_entry_days = []
            day_counter = 0
            while len(all_map_entry_days) < 20:
                # Calculate the next entry day based on the current date and day counter
                next_entry_day = datetime.date.today() + datetime.timedelta(days=day_counter)
                
                # Check if the day of the week matches one of the entry days
                if next_entry_day.weekday() in entry_days_of_week:
                    # Append the entry day to the list
                    all_map_entry_days.append(next_entry_day.day)
                
                # Increment the day counter
                day_counter += 1

            # Update the map info with entry days
            for i, map_data in enumerate(map_info):
                map_data['entryDay'] = all_map_entry_days[i]

            # Write the updated map info to a new JSON file with indentation
            with open('map_info_with_names.json', 'w') as f:
                json.dump(map_info, f, indent=4)

            # Write the updated map info to a new JSON file with indentation
            with open('map_info_with_names.json', 'w') as f:
                json.dump(map_info, f, indent=4)

        except requests.exceptions.RequestException as e:
            print(f"Error during getting map info: {e}")
            exit(1)

    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Something went wrong", err)

    # Print response
    print(map_list_response)
    with open('response.json', 'w') as f:
        json.dump(map_list_response, f, indent=4)
        
@app.route('/getmaps')
def trigger_fetch_maps_info():
    fetch_maps_info()
    return "Map information fetched and processed successfully!"

@app.route('/maps')
def get_maps_info():
    with open('map_info_with_names.json', 'r') as f:
        map_info = json.load(f)
    return jsonify(map_info)


import json
# Create an instance of the scheduler
scheduler = BackgroundScheduler()

# Define the job to run the fetch_results() function
@scheduler.scheduled_job('cron', hour='2-18', minute='25', timezone='UTC')
def run_fetch_results_job():
    fetch_results()

# Start the scheduler
scheduler.start()

@app.route('/')
def home():
    return "Welcome to the Trackmania Royal Fan Site!"

# Create a route to trigger the fetch_results() function
@app.route('/fetch_results')
def trigger_fetch_results():
    fetch_results()
    return "Results fetched and processed successfully!"

# Routes for displaying the modified JSON files@app.route('/Master_Final')
@app.route('/masterf')
def master_final():
    try:
        with open('Master_Final.json', 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": "Failed to load Master Final data. Please try again later."}), 500

@app.route('/goldf')
def gold_final():
    try:
        with open('Gold_Final.json', 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": "Failed to load Gold Final data. Please try again later."}), 500

@app.route('/silverf')
def silver_final():
    try:
        with open('Silver_Final.json', 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": "Failed to load Silver Final data. Please try again later."}), 500

@app.route('/bronzef')
def bronze_final():
    try:
        with open('Bronze_Final.json', 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": "Failed to load Bronze Final data. Please try again later."}), 500

if __name__ == '__main__':
    app.run()
