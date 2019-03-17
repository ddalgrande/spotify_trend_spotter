import os
import sys
import spotipy
import webbrowser
import spotipy.util as util
from json.decoder import JSONDecodeError

# Get the username from terminal
username = sys.argv[1]
scope = 'user-read-private user-read-playback-state user-modify-playback-state'

# Erase cache and prompt for user permission
try:
    token = util.prompt_for_user_token(username, scope) # add scope
except (AttributeError, JSONDecodeError):
    os.remove(f".cache-{username}")
    token = util.prompt_for_user_token(username, scope) # add scope

# Create our spotify object with permissions
spotifyObject = spotipy.Spotify(auth=token)


# Get latest 500 new releases for selected country


# Get tracks from albums


# Get audio analysis for each track


# Get audio features for each track


# Get featured playlists for country



# User information
user = spotifyObject.current_user()
displayName = user['display_name']
followers = user['followers']['total']
print ('usernanme:', displayName, '\nfollowers:', followers)

