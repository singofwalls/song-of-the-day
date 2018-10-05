"""Create the thingy Graham wanted.

this is some bad code...
"""

import os
import random
import urllib.request
import json
import xml.etree.ElementTree as et

import spotipy
import spotipy.util as util

PLAYLIST = "Loved"

xml_path = (
    os.environ["USERPROFILE"] + "/music/itunes/iTunes Music Library.xml"
)

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


def format_name(name):
    return "".join(ch for ch in name if (ch.isalnum() or ch == " ")).lower()


playlists_path = find_path_to_playlist("Playlists", [0])

path = find_path_to_playlist(PLAYLIST, playlists_path)
if isinstance(path, type(None)):
    raise Exception("Could not find playlist.")

while get_tree(path, True).tag != "array":
    path[-1] += 1

track_ids = [song[1].text for song in get_tree(path, True)]

file_path = os.environ["USERPROFILE"] + "\\documents\\chosen_songs.txt"

f = open(file_path, "a")
f.close()

blacklisted = []
with open(file_path, "r") as f:
    for line in f.read().split("\n"):
        if line:
            blacklisted.append(line)

chosen_track = None
attempts = 1000
while isinstance(chosen_track, type(None)) or chosen_track in blacklisted:
    chosen_track = track_ids[random.randint(0, len(track_ids) - 1)]
    attempts -= 1
    if attempts < 0:
        raise Exception("Chosen all songs already")

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

name = None
artist = None

for i, key in enumerate(song):
    if key.text == "Name":
        name = song[i + 1].text
    if key.text == "Artist":
        artist = song[i + 1].text

name = format_name(name)
artist = format_name(artist)

print(chosen_track, name, artist)

itunes_song_info = urllib.request.urlopen(
    ('https://itunes.apple.com/search?term="' + name + '" ' + artist)
    .replace(" ", "+")
    .encode("ascii", "ignore")
    .decode("ascii")
).read()
json_string_itunes = itunes_song_info.decode("utf8").replace("\n", "")
json_itunes = json.loads(json_string_itunes)
results = json_itunes["results"]

itunes_link = None
for track in results:
    if (
        format_name(track["trackName"]) == name
        and format_name(track["artistName"]) == artist
    ):
        itunes_link = track["trackViewUrl"]
        break

if isinstance(itunes_link, type(None)):
    print("No itunes link found.")

# spotify_song_info = urllib.request.urlopen(
#     ("https://api.spotify.com/v1/search?q="+ name + " " + artist + "&type=artist,track").replace(" ", "%20")
# ).read()

token = util.prompt_for_user_token(
    username="REDACTED",
    client_id="REDACTED",
    client_secret="REDACTED",
    scope="user-library-read",
    redirect_uri="REDACTED",
)
spotify = spotipy.Spotify(token)
results = spotify.search(
    q=("track:" + name + " artist:" + artist).encode("ascii", "ignore").decode("ascii"),
    type="track",
)

spotify_link = None

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

if not isinstance(spotify_link, type(None)):
    print(spotify_link)
if not isinstance(itunes_link, type(None)):
    print(itunes_link)
