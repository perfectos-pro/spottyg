from flask import Flask, request, jsonify
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

app = Flask(__name__)

sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback"),
    scope="playlist-read-private playlist-modify-private playlist-modify-public"
)

sp = spotipy.Spotify(auth_manager=sp_oauth)

@app.route("/")
def index():
    return "Spotify GPT Agent is live!"

@app.route("/search_track", methods=["GET"])
def search_track():
    query = request.args.get("q")
    results = sp.search(q=query, type="track", limit=5)
    return jsonify(results)

@app.route("/search_album", methods=["GET"])
def search_album():
    query = request.args.get("q")
    results = sp.search(q=query, type="album", limit=5)
    return jsonify(results)

@app.route("/get_playlists", methods=["GET"])
def get_playlists():
    playlists = sp.current_user_playlists()
    return jsonify(playlists)

@app.route("/create_playlist", methods=["POST"])
def create_playlist():
    data = request.json
    name = data.get("name")
    description = data.get("description", "")
    user_id = sp.me()["id"]
    new_playlist = sp.user_playlist_create(user=user_id, name=name, description=description)
    return jsonify(new_playlist)

@app.route("/add_to_playlist", methods=["POST"])
def add_to_playlist():
    data = request.json
    playlist_id = data["playlist_id"]
    track_uris = data["track_uris"]
    result = sp.playlist_add_items(playlist_id, track_uris)
    return jsonify(result)