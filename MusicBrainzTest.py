import requests
import json

# Prompt the user to enter an album name
album_name = input("Enter an album name: ")

# Query the MusicBrainz API for album data
musicbrainz_response = requests.get('https://musicbrainz.org/ws/2/release-group/', params={'query': album_name, 'type': 'album', 'limit': 5}, headers={'Accept': 'application/json'})

# Check if the response was successful (HTTP status code 200)
if musicbrainz_response.status_code == 200:
    # Parse the response JSON data
    musicbrainz_data = musicbrainz_response.json()
    
    # Output the album data
    for album in musicbrainz_data['release-groups']:
        print(album['title'])
        print(album['first-release-date'])
else:
    # Output an error message if the response was not successful
    print("Error retrieving album data from MusicBrainz API")
