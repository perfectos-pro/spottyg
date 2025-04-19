from flask import Flask, request, jsonify, session, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

app = Flask(__name__, static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-default-secret-key")

sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback"),
    scope="playlist-read-private playlist-modify-private playlist-modify-public"
)

def get_spotify_client():
    token_info = session.get("token_info")
    if not token_info:
        return None
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
        session["token_info"] = token_info
    return spotipy.Spotify(auth=token_info["access_token"])

@app.route("/")
def index():
    return "Spotify GPT Agent is live!"

@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    return redirect("/")

@app.route("/search_track", methods=["GET"])
def search_track():
    sp = get_spotify_client()
    if not sp:
        return redirect("/login")
    query = request.args.get("q")
    results = sp.search(q=query, type="track", limit=5)
    return jsonify(results)

@app.route("/search_album", methods=["GET"])
def search_album():
    sp = get_spotify_client()
    if not sp:
        return redirect("/login")
    query = request.args.get("q")
    results = sp.search(q=query, type="album", limit=5)
    return jsonify(results)

@app.route("/get_playlists", methods=["GET"])
def get_playlists():
    sp = get_spotify_client()
    if not sp:
        return redirect("/login")
    playlists = sp.current_user_playlists()
    return jsonify(playlists)

@app.route("/create_playlist", methods=["POST"])
def create_playlist():
    sp = get_spotify_client()
    if not sp:
        return redirect("/login")
    data = request.json
    name = data.get("name")
    description = data.get("description", "")
    public = data.get("public", False)
    collaborative = data.get("collaborative", False)
    user_id = sp.me()["id"]
    new_playlist = sp.user_playlist_create(
        user=user_id,
        name=name,
        description=description,
        public=public,
        collaborative=collaborative
    )
    return jsonify(new_playlist)

@app.route("/add_to_playlist", methods=["POST"])
def add_to_playlist():
    sp = get_spotify_client()
    if not sp:
        return redirect("/login")
    data = request.json
    playlist_id = data["playlist_id"]
    track_uris = data["track_uris"]
    result = sp.playlist_add_items(playlist_id, track_uris)
    return jsonify(result)

@app.route("/openapi.yaml")
def serve_openapi_yaml():
    return app.send_static_file("openapi.yaml")