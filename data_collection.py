"""
Fetches new song releases from the Spotify API, analyzes their audio features and popularity,
identifies potential 'hit' candidates based on predefined criteria, and saves the results
to a CSV file.

Command-Line Arguments:
    username (str): Your Spotify username (required for API authentication).
    country_code (str, optional): The 2-letter ISO country code for new releases
                                  and featured playlists (e.g., 'US', 'GB').
                                  Defaults to 'US'.
    num_release_pages (int, optional): The number of pages of new releases to fetch.
                                       Each page contains 50 albums.
                                       Defaults to 1.

Output:
    Outputs a CSV file named 'spotify_hit_candidates.csv' in the script's directory.
    This file contains detailed information for each track, including its audio features,
    popularity, whether it's in a featured playlist, and the 'is_hit_candidate' flag.
"""
import os
import sys
import spotipy
import webbrowser
import spotipy.util as util
from json.decoder import JSONDecodeError
from pprint import pprint as pprint
import pandas as pd

# --- Configuration ---
POPULARITY_THRESHOLD = 60 # Threshold for a track to be considered popular

# --- Command-Line Argument Parsing ---
if len(sys.argv) < 2:
    print("Usage: python data_collection.py <username> [country_code] [num_release_pages]")
    sys.exit(1) # Exit if username is not provided

username = sys.argv[1]

# Set country_code from argument or default to 'US'
if len(sys.argv) > 2:
    country_code = sys.argv[2]
else:
    country_code = 'US'

# Set number of new release pages from argument or default to 1
if len(sys.argv) > 3:
    try:
        num_release_pages = int(sys.argv[3])
        if num_release_pages < 1: # Ensure at least one page is fetched
            print("Warning: Number of pages must be at least 1. Defaulting to 1.")
            num_release_pages = 1
    except ValueError:
        print("Warning: Invalid value for number of pages. Defaulting to 1.")
        num_release_pages = 1
else:
    num_release_pages = 1

# --- Spotify API Authentication ---
scope = 'user-read-private user-read-playback-state user-modify-playback-state'

# Erase cache and prompt for user permission if token is invalid or missing
try:
    token = util.prompt_for_user_token(username, scope)
except (AttributeError, JSONDecodeError):
    os.remove(f".cache-{username}") # Remove potentially corrupted cache file
    token = util.prompt_for_user_token(username, scope)

# Create Spotify API object
spotifyObject = spotipy.Spotify(auth=token)


# --- Fetch New Album Releases ---
album_releases = []
print(f"Fetching {num_release_pages} page(s) of new releases for country: {country_code}...")
for i in range(num_release_pages):
    # Fetch 50 albums per page, using offset for pagination
    albums_page = spotifyObject.new_releases(country=country_code, limit=50, offset=i*50)
    if albums_page:
        album_releases.append(albums_page)

# --- Extract Album Information ---
album_information = []
print("Extracting album information...")
for idx, album_release_page in enumerate(album_releases):
    if album_release_page and 'albums' in album_release_page and 'items' in album_release_page['albums']:
        albums_on_page = album_release_page['albums']['items']
        for a in albums_on_page:
            a_content = {}
            a_content['album_type'] = a.get('album_type')
            a_content['album_name'] = a.get('name')
            a_content['album_url'] = a.get('href')
            artists = a.get('artists', [])
            if artists: # Check if artists list is not empty
                # For simplicity, using the first artist's details
                a_content['artist_name'] = artists[0].get('name')
                a_content['artist_uri'] = artists[0].get('uri')
            a_content['release_date'] = a.get('release_date')
            a_content['album_uri'] = a.get('uri')
            album_information.append(a_content)

# Create a DataFrame for album information
df_albums = pd.DataFrame(album_information)
        
# --- Get Track Details, Audio Features, and Popularity ---
tracks_data = [] # Renamed from 'tracks' to avoid confusion
print("Fetching track details, audio features, and popularity...")
if not df_albums.empty: # Proceed only if albums were found
    for album_uri in df_albums['album_uri'].values:
        album_tracks_results = spotifyObject.album_tracks(album_uri, limit=50) # Fetch up to 50 tracks per album

        if album_tracks_results and isinstance(album_tracks_results, dict) and 'items' in album_tracks_results:
            for item in album_tracks_results['items']:
                track_info = {'album_uri': album_uri}
                track_info['track_name'] = item.get('name')
                track_info['track_duration_ms'] = item.get('duration_ms')
                track_info['track_uri'] = item.get('uri')

                if track_info['track_uri']: # Proceed only if track_uri is valid
                    # Fetch audio features for the current track
                    audio_features_list = spotifyObject.audio_features(tracks=[track_info['track_uri']])
                    if audio_features_list and audio_features_list[0]: # Check if data is returned
                        features = audio_features_list[0]
                        track_info['danceability'] = features.get('danceability')
                        track_info['energy'] = features.get('energy')
                        track_info['key'] = features.get('key')
                        track_info['loudness'] = features.get('loudness')
                        track_info['mode'] = features.get('mode')
                        track_info['speechiness'] = features.get('speechiness')
                        track_info['acousticness'] = features.get('acousticness')
                        track_info['instrumentalness'] = features.get('instrumentalness')
                        track_info['liveness'] = features.get('liveness')
                        track_info['valence'] = features.get('valence')
                        track_info['tempo'] = features.get('tempo')

                    # Fetch full track details for popularity
                    track_details = spotifyObject.track(track_info['track_uri'])
                    if track_details:
                        track_info['popularity'] = track_details.get('popularity', None)
                    else:
                        track_info['popularity'] = None
                else:
                    # Handle cases where track_uri might be None (e.g., local files, though unlikely for new releases)
                    print(f"Skipping track with missing URI in album {album_uri}")
                    continue # Skip to the next track

                tracks_data.append(track_info)
else:
    print("No albums found to process for tracks.")


# --- Identify Tracks in Featured Playlists ---
featured_track_uris = set()
print(f"Fetching featured playlists for country: {country_code}...")
featured_playlists_data = spotifyObject.featured_playlists(country=country_code, limit=50) # Fetch up to 50 featured playlists

if featured_playlists_data and featured_playlists_data.get('playlists') and featured_playlists_data['playlists'].get('items'):
    for playlist in featured_playlists_data['playlists']['items']:
        playlist_id = playlist.get('id')
        if playlist_id:
            print(f"Fetching tracks for playlist ID: {playlist_id}...")
            # Request only track URIs for efficiency
            playlist_items_results = spotifyObject.playlist_items(playlist_id, fields='items.track.uri,next')
            # Handle pagination for playlists with more than 100 tracks
            while playlist_items_results:
                for item_wrapper in playlist_items_results.get('items', []):
                    if item_wrapper and item_wrapper.get('track') and item_wrapper['track'].get('uri'):
                        featured_track_uris.add(item_wrapper['track']['uri'])
                # Check if there is a next page of playlist items
                if playlist_items_results.get('next'):
                    playlist_items_results = spotifyObject.next(playlist_items_results)
                else:
                    playlist_items_results = None # Exit pagination loop

# Mark tracks if they are in any featured playlist
print("Marking tracks found in featured playlists...")
for track_entry in tracks_data: # Renamed loop variable for clarity
    # Ensure 'track_uri' exists before checking against the set
    if 'track_uri' in track_entry:
        track_entry['in_featured_playlist'] = track_entry['track_uri'] in featured_track_uris
    else:
        track_entry['in_featured_playlist'] = False


# --- Combine Data and Define 'Hits' ---
# Create a DataFrame for track data
df_tracks = pd.DataFrame(tracks_data)

# Merge track data with album data
# Ensure df_albums is not empty to avoid errors on merge
if not df_albums.empty and not df_tracks.empty:
    new_releases_df = pd.merge(df_tracks, df_albums, how='left', on='album_uri')
elif not df_tracks.empty: # Only tracks data is available
    print("Warning: Album data was empty. Proceeding with tracks data only.")
    new_releases_df = df_tracks
    # Add missing album columns as NaN if necessary, or ensure downstream code handles their absence
    for col in ['album_type', 'album_name', 'album_url', 'artist_name', 'artist_uri', 'release_date']:
        if col not in new_releases_df:
            new_releases_df[col] = None
else: # No track data, possibly no album data either
    print("No track data collected. Output CSV will be empty or not generated.")
    new_releases_df = pd.DataFrame() # Create an empty DataFrame

# Define 'is_hit_candidate' based on popularity and presence in featured playlists
if not new_releases_df.empty:
    # Ensure 'popularity' column exists and is numeric, fill NaNs with 0
    if 'popularity' not in new_releases_df: new_releases_df['popularity'] = 0 # Add column if missing
    new_releases_df['popularity'] = pd.to_numeric(new_releases_df['popularity'], errors='coerce').fillna(0).astype(int)

    # Ensure 'in_featured_playlist' column exists and is boolean
    if 'in_featured_playlist' not in new_releases_df: new_releases_df['in_featured_playlist'] = False # Add column if missing
    new_releases_df['in_featured_playlist'] = new_releases_df['in_featured_playlist'].astype(bool)

    # A track is a hit candidate if its popularity is above threshold OR it's in a featured playlist
    new_releases_df['is_hit_candidate'] = (new_releases_df['popularity'] >= POPULARITY_THRESHOLD) | \
                                          (new_releases_df['in_featured_playlist'] == True)
else:
    print("DataFrame is empty, skipping 'is_hit_candidate' definition.")

# --- Store Results ---
if not new_releases_df.empty:
    try:
        new_releases_df.to_csv('spotify_hit_candidates.csv', index=False)
        print("Results saved to spotify_hit_candidates.csv")
    except Exception as e:
        print(f"Error saving DataFrame to CSV: {e}")
else:
    print("No data to save to CSV.")

# Placeholder comments for potential future sections (as in original)
# Get hits (This seems to be a general comment for the script's purpose)
# Get featured playlists for country (This action is already performed above)

print("Script finished.")
