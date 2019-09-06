"""Choose random songs from a spotify playlist to dump in a groupme chat."""
import json
import random
import urllib.parse
import datetime

import spotipy
from spotipy import util
import requests


CREDS_FILE = "creds.json"
PAST_TRACKS_FILE = "past_tracks.json"
TIMESTAMP_FORMAT = "%I O'CLOCK"


def get_apple_link(search_terms):
    """Get a link to the song from Apple based on artist, name, and album."""

    query = " ".join(search_terms)
    query = urllib.parse.quote_plus(query)
    response = requests.get(f"https://itunes.apple.com/search?term={query}&limit=1")
    if not response.ok or not response.content:
        return ""

    content = json.loads(response.content)
    results = content["results"]
    if not results:
        return ""

    url = results[0]["trackViewUrl"]
    return url


def get_track_details(track):
    """Get the name, artist, and album, and links from the track dict."""
    details = {}

    artists = track["track"]["artists"]
    details["artist"] = "Unknown"
    if artists:
        details["artist"] = artists[0]["name"]

    details["name"] = track["track"]["name"]
    details["album"] = track["track"]["album"]["name"]
    details["apple link"] = get_apple_link(
        (details["artist"], details["name"], details["album"])
    )
    details["spotify link"] = track["track"]["external_urls"]["spotify"]

    return details


def send_track(track, spotify, g_creds, s_creds):
    """Send the chosen track to the groupme chat."""

    details = get_track_details(track)
    playlist = spotify.user_playlist(s_creds["username"], s_creds["playlist"])
    playlist_link = playlist["external_urls"]["spotify"]
    now = datetime.datetime.now().strftime(TIMESTAMP_FORMAT)

    message = (
        f"THE TIME IS {now}\n\n"
        f"SONG OF THE DAY\n-------------------\n{details['name']}\n"
        f"artist: {details['artist']}\nalbum: {details['album']}"
        f"\n\nSpotify: {details['spotify link']}\nApple: {details['apple link']}"
        f"\n\nPlaylist: {playlist_link}\nAddition Form: {s_creds['form_link']}"
    )

    post_params = {"bot_id": g_creds["bot_id"], "text": message}
    requests.post("https://api.groupme.com/v3/bots/post", params=post_params)


def record_chosen_track(track):
    """Add the chosen track to the past tracks file."""
    past_tracks = load_past_tracks()
    past_tracks.append(track["track"]["id"])
    with open(PAST_TRACKS_FILE, "w") as f:
        f.write(json.dumps(past_tracks))


def load_past_tracks():
    """Load the tracks which have already been used."""
    try:
        with open(PAST_TRACKS_FILE) as f:
            past_tracks = json.load(f)
            return past_tracks
    except FileNotFoundError:
        with open(PAST_TRACKS_FILE, "w") as f:
            f.write(json.dumps([]))
        return []


def get_remaining_tracks(spotify, s_creds):
    """Get the tracks from the spotify playlist which have not been used."""
    results = spotify.user_playlist_tracks(s_creds["username"], s_creds["playlist"])
    tracks = results["items"]
    all_track_ids = set([track["track"]["id"] for track in tracks])
    past_track_ids = set(load_past_tracks())
    remaining_track_ids = all_track_ids - past_track_ids

    # Get track dicts from ids
    remaining_tracks = [
        track for track in tracks if track["track"]["id"] in remaining_track_ids
    ]

    return remaining_tracks


def get_credentials():
    """Load the credentials from the json."""
    with open(CREDS_FILE) as f:
        creds = json.load(f)

    s_creds = creds["spotify"]
    g_creds = creds["groupme"]

    return s_creds, g_creds


def get_spotify(s_creds):
    """Get the spotify object from which to make requests."""
    # Authorize Spotify
    token = util.prompt_for_user_token(
        s_creds["username"],
        s_creds["scopes"],
        s_creds["client_id"],
        s_creds["client_secret"],
        s_creds["redirect_uri"],
    )

    return spotipy.Spotify(auth=token)


def main():
    """Start the program."""
    s_creds, g_creds = get_credentials()
    spotify = get_spotify(s_creds)
    remaining_tracks = get_remaining_tracks(spotify, s_creds)
    if remaining_tracks:
        chosen_track = random.choice(remaining_tracks)
    else:
        # TODO: Handle no more remaining
        return

    send_track(chosen_track, spotify, g_creds, s_creds)
    record_chosen_track(chosen_track)


if __name__ == "__main__":
    main()
