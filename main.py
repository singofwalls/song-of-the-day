"""Create the thingy Graham wanted.

this is some bad code...
"""

import os
import random
import urllib.request
import json
import xml.etree.ElementTree as et
import requests
import unicodedata

import spotipy
import spotipy.util as util

PLAYLIST = "Synced Bands"
BOT_ID = "REDACTED"
USERNAME = "REDACTED"
CLIENT_ID = "REDACTED"
CLIENT_SECRET = "REDACTED"
REDIRECT_URI = "REDACTED"
IMAGE = "REDACTED"

xml_path = os.environ["USERPROFILE"] + "/music/itunes/iTunes Music Library.xml"

tree = et.parse(xml_path)
root = tree.getroot()


def get_tree(path, value=False):
    _local_tree = [root]
    for i, child in enumerate(path):
        if i == len(path) - 1 and not value:
            return _local_tree
        _local_tree = _local_tree[child]
    return _local_tree


def find_path_to_playlist(playlist, path):
    local_tree = get_tree(path)
    while len(local_tree) and path:
        while path[-1] < len(local_tree):
            if local_tree[path[-1]].text == playlist:
                return path
            elif len(local_tree[path[-1]]):
                local_tree = local_tree[path[-1]]
                path.append(0)
            else:
                path[-1] += 1

        path.pop()
        if not path:
            break
        path[-1] += 1
        local_tree = get_tree(path)
    return None


def remove_accents(input_str):
    """Found here: https://stackoverflow.com/a/517974."""
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    only_ascii = nfkd_form.encode("ASCII", "ignore")
    return only_ascii.decode("ASCII")


def format_name(name):
    return remove_accents(
        "".join(ch for ch in name if (ch.isalnum() or ch == " ")).lower()
    )


playlists_path = find_path_to_playlist("Playlists", [0])

path = find_path_to_playlist(PLAYLIST, playlists_path)
if isinstance(path, type(None)):
    raise Exception("Could not find playlist.")

while get_tree(path, True).tag != "array":
    path[-1] += 1

track_ids = [song[1].text for song in get_tree(path, True)]

file_path = os.environ["USERPROFILE"] + "\\documents\\chosen_songs.txt"

# Create file if does not already exist
f = open(file_path, "a")
f.close()

blacklisted = []
with open(file_path, "r") as f:
    for line in f.read().split("\n"):
        if line:
            blacklisted.append(line)

remaining_tracks = set(track_ids) - set(blacklisted)
if not remaining_tracks:
    raise Exception("No tracks remain")
chosen_track = random.choice(tuple(remaining_tracks))

with open(file_path, "a") as f:
    f.write(str(chosen_track) + "\n")

song = None

path = find_path_to_playlist("Tracks", [0])
path[-1] += 1
for i, track in enumerate(get_tree(path, True)):
    if track.text == chosen_track:
        path.append(i)
        path[-1] += 1
        song = get_tree(path, True)
        break

original_name = None
original_artist = None

for i, key in enumerate(song):
    if key.text == "Name":
        original_name = song[i + 1].text
    if key.text == "Artist":
        original_artist = song[i + 1].text

name = format_name(original_name)
artist = format_name(original_artist)

itunes_song_info = urllib.request.urlopen(
    ('https://itunes.apple.com/search?term="' + name + '" ' + artist).replace(" ", "+")
).read()
json_string_itunes = itunes_song_info.decode("utf8").replace("\n", "")
json_itunes = json.loads(json_string_itunes)
results = json_itunes["results"]

itunes_link = ""
for track in results:
    if (
        format_name(track["trackName"]) == name
        and format_name(track["artistName"]) == artist
    ):
        itunes_link = track["trackViewUrl"]
        break

if isinstance(itunes_link, type(None)):
    print("No itunes link found.")

token = util.prompt_for_user_token(
    username=USERNAME,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scope="user-library-read",  # Apparent I have to provide a scope even if my script requires no user acess ... i think
    redirect_uri=REDIRECT_URI,  # Apparently I have to provide a url to verify against my account ... i think
)
spotify = spotipy.Spotify(token)
results = spotify.search(q=("track:" + name + " artist:" + artist), type="track")

spotify_link = ""

try:
    results = results["tracks"]["items"]
    for track in results:
        if format_name(track["name"]) == name and artist in [
            format_name(a["name"]) for a in track["artists"]
        ]:
            spotify_link = track["external_urls"]["spotify"]
            break
    else:
        raise IndexError(
            "Wow, I can't believe I'm actually writing this statement... Sry"
        )
except IndexError as e:
    print("No spotify link found.")

print(original_name, original_artist)

if not isinstance(spotify_link, type(None)):
    print(spotify_link)
if not isinstance(itunes_link, type(None)):
    print(itunes_link)

message = f"SONG OF THE DAY\n-------------------\n{original_artist}: {original_name}\n\nSpotify: {spotify_link}\nApple: {itunes_link}"

post_params = {"bot_id": BOT_ID, "text": IMAGE}
requests.post("https://api.groupme.com/v3/bots/post", params=post_params)

post_params = {
    "bot_id": BOT_ID,
    "text": message,
    # "attachments": [{"type": "image", "url": IMAGE}],
}
requests.post("https://api.groupme.com/v3/bots/post", params=post_params)
