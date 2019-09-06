"""Choose random songs from a spotify playlist to dump in a groupme chat."""
import json
import random

import spotipy
from spotipy import util


CREDS_FILE = "creds.json"
PAST_TRACKS_FILE = "past_tracks.json"


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
    remaining_tracks = [track for track in tracks if track["track"]["id"] in remaining_track_ids]

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
    record_chosen_track(chosen_track)


if __name__ == "__main__":
    main()
