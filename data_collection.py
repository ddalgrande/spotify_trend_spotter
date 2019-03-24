import os
import sys
import spotipy
import webbrowser
import spotipy.util as util
from json.decoder import JSONDecodeError
from pprint import pprint as pprint
import pandas as pd

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


# Get latest 10,000 new releases for selected country

album_releases = []

for i in range(0, 1):
    albums = spotifyObject.new_releases(country='gb', limit= 50, offset=i)
    album_releases.append(albums)


# Get info from albums

album_information = []

for idx, album_release in enumerate(album_releases):
    albums = album_releases[idx]['albums']['items']
    for a in albums:
        a_content = {}
        a_content['album_type'] = a['album_type']
        a_content['album_name'] = a['name']
        a_content['album_url'] = a['href']
        artists = a['artists']
        for name in artists: 
            a_content['artist_name'] = name['name']
            a_content['artist_uri'] = name['uri']
        a_content['release_date'] = a['release_date']
        a_content['album_uri'] = a['uri']

        album_information.append(a_content)

df = pd.DataFrame(album_information)
        
        
# Get audio analysis for each track

tracks = []

for u in df['album_uri'].values:
    album_tracks = spotifyObject.album_tracks(u, limit = 10)

    if album_tracks is type(list):

        for idx, t in enumerate(album_tracks):
            track = {'album_uri': u}
            items = album_tracks['items']
            for item in items:
                track['track_name'] = item['name']
                track['track_duration_ms'] = item['duration_ms']
                track['track_uri'] = item['uri']
                audio_analysis = spotifyObject.audio_analysis(track['track_uri'])
                audio_features = spotifyObject.audio_features(tracks=[track['track_uri']])

            tracks.append(track)

    else:

        track = {'album_uri': u}
        items = album_tracks['items']
        for item in items:
            track['track_name'] = item['name']
            track['track_duration_ms'] = item['duration_ms']
            track['track_uri'] = item['uri']
            audio_analysis = spotifyObject.audio_analysis(track['track_uri'])
            track_bars = audio_analysis['bars']
            for idx, bar in enumerate(track_bars):
                track['bars_start_' + str(idx)] = bar['start']
                track['bars_duration_' + str(idx)] = bar['duration']
                track['bars_confidence_' + str(idx)] = bar['confidence']
            track_beats = audio_analysis['beats']
            for idx, beat in enumerate(track_beats):
                track['beats_bars_start_' + str(idx)] = beat['start']
                track['beats_duration_' + str(idx)] = beat['duration']
                track['beats_confidence_' + str(idx)] = beat['confidence']
            track_sections = audio_analysis['sections']
            for idx, sc in enumerate(track_sections):
                track['section_start_' + str(idx)] = sc['start']
                track['section_duration_' + str(idx)] = sc['duration']
                track['section_confidence_' + str(idx)] = sc['confidence']
                track['section_loudness_' + str(idx)] = sc['loudness']
                track['section_tempo_' + str(idx)] = sc['tempo']
                track['section_tempo_confidence_' + str(idx)] = sc['tempo_confidence']
                track['section_key_' + str(idx)] = sc['key']
                track['section_key_confidence_' + str(idx)] = sc['key_confidence']
                track['section_mode_' + str(idx)] = sc['mode']
                track['section_mode_confidence_' + str(idx)] = sc['mode_confidence']
                track['section_time_signature_' + str(idx)] = sc['time_signature']
                track['section_ime_signature_confidence_' + str(idx)] = sc['time_signature_confidence']
            track_segments = audio_analysis['segments']
            for idx, sg in enumerate(track_segments):
                track['segment_start_' + str(idx)] = sg['start']
                track['segment_duration_' + str(idx)] = sg['duration']
                track['segment_confidence_' + str(idx)] = sg['confidence']
                track['segment_loudness_start_' + str(idx)] = sg['loudness_start']
                track['segment_loudness_max_time_' + str(idx)] = sg['loudness_max_time']
                track['segment_loudness_max_' + str(idx)] = sg['loudness_max']
                # track['segment_loudness_end_' + str(idx)] = sg['loudness_end']
                pitches = sg['pitches']
                for idx, pitch in enumerate(pitches):
                    track['segment_pitch_' + str(idx)] = pitch
                timbres = sg['timbre']
                for idx, timbre in enumerate(timbres):
                    track['segment_timbre_' + str(idx)] = timbre
            track_tatums = audio_analysis['tatums']
            for idx, tatum in enumerate(track_tatums):
                track['tatums_start_' + str(idx)] = tatum['start']
                track['tatums_duration_' + str(idx)] = tatum['duration']
                track['tatums_confidence_' + str(idx)] = tatum['confidence']
            track_feature = audio_analysis['track']
            track['track_analysis_channels'] = track_feature['analysis_channels']
            track['track_analysis_sample_rate'] = track_feature['analysis_sample_rate']
            track['track_code_version'] = track_feature['code_version']
            track['track_end_of_fade_in'] = track_feature['end_of_fade_in']
            track['track_key'] = track_feature['key']
            track['track_key_confidence'] = track_feature['key_confidence']
            track['track_loudness'] = track_feature['loudness']
            track['track_mode'] = track_feature['mode']
            track['track_mode_confidence'] = track_feature['mode_confidence']
            track['track_num_samples'] = track_feature['num_samples']
            track['track_offset_seconds'] = track_feature['offset_seconds']
            track['track_rhythm_version'] = track_feature['rhythm_version']
            track['track_sample_md5'] = track_feature['sample_md5']
            track['track_synch_version'] = track_feature['synch_version']
            track['track_tempo'] = track_feature['tempo']
            track['track_tempo_confidence'] = track_feature['tempo_confidence']
            track['track_time_signature'] = track_feature['time_signature']
            track['track_time_signature_confidence'] = track_feature['time_signature_confidence']
            track['track_window_seconds'] = track_feature['window_seconds']
        tracks.append(track)

df_tracks = pd.DataFrame(tracks)

new_releases_df = pd.merge(df_tracks, df, how = 'left', on = 'album_uri')

# Get hits


# Get featured playlists for country

