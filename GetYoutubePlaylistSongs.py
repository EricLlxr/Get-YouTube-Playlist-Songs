from pyyoutube import Api
import requests
import click

# Config
API_KEY = "" # Add your own key here
PLAYLIST_ID = "" # Example: PLFVbJV_jTp8Xqxs-vtwgRYj7yt5n0OO4N
PROGRESS_BAR_ENABLE = True

# Constants
YT = "https://www.youtube.com/watch?v="
MAX_BUFFER_SIZE = 128
AMPERSAND = "\\u0026"
SONG_IDENTIFIER = 'Song"},"contents"'
ARTIST_IDENTIFIER = 'Artist"},"contents"'

# Globals
songs_list = []
no_songs_list = []

# Find all substring in a string
def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub)
        
def process_video(video):
    global no_songs_list
    global songs_list
    
    # Video id from Youtube Api and compose a URL
    id = video.contentDetails.videoId
    URL = f"{YT}{id}"
    
    # Get the html from the Youtube url and decode the content into a string
    page = requests.get(URL)
    data = page.content.decode()
    
    # Check for Songs - if there are none then return
    song_indexes = list(find_all(data, SONG_IDENTIFIER))
    if len(song_indexes) == 0:
        no_songs_list.append(video.snippet.title)
        return
    artist_indexes = list(find_all(data, ARTIST_IDENTIFIER))
    
    if PROGRESS_BAR_ENABLE is False:
        print(f"{video.snippet.title}")
    
    for i, song_index in enumerate(song_indexes):
        song_data = data[song_index:song_index + MAX_BUFFER_SIZE]
        
        # Two ways song data is stores try to replace the first if that doesn't work then try the other
        song = song_data.replace(SONG_IDENTIFIER + ':[{"runs":[{"text":"', '')
        if SONG_IDENTIFIER in song:
            song = song_data.replace(SONG_IDENTIFIER + ':[{"simpleText":"', '')
            song = song[:song.find('"}],"t')]
        else:
            song = song[:song.find('","nav')]
        
        # Voodoo magic that gets the artist
        artist_index = artist_indexes[i]
        artist_data = data[artist_index:artist_index + MAX_BUFFER_SIZE].split(":")
        artist = artist_data[2]
        if artist == '[{"text"':
            artist = artist_data[3]
        artist = artist[1:artist[1:].find('"') + 1]
        
        # Combine song name and and artist for the 'track'
        track = f"{artist.replace(AMPERSAND, '&')} - {song.replace(AMPERSAND, '&')}"
        songs_list.append(track)
        if PROGRESS_BAR_ENABLE is False:
            print(f"\t{track}")

# Youtube API
api = Api(api_key=API_KEY)

# Ask youtube for the number of videos and then get all those videos in the playlist.
itemCount = api.get_playlist_by_id(playlist_id=PLAYLIST_ID).items[0].contentDetails.itemCount
playlist = api.get_playlist_items(playlist_id=PLAYLIST_ID, count=itemCount)

# Completely pointless but it's cool
if PROGRESS_BAR_ENABLE:
    with click.progressbar(playlist.items) as bar:
        for video in bar:
            process_video(video)
else:
    for video in playlist.items:
        process_video(video)

songs_set = set(songs_list)
if PROGRESS_BAR_ENABLE is False:
    for song in songs_set:
        print(song)
print(f"\nNumber of videos: {len(playlist.items)}")
print(f"Total number of songs found: {len(songs_set)}")
print(f"Could not find songs for {len(no_songs_list)} videos:\n {no_songs_list}")
