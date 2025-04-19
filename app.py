from flask import Flask, request, jsonify, session, redirect
import spotipy
import traceback
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
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ")[1]
        app.logger.info("Token received via Authorization header")
        return spotipy.Spotify(auth=token)
    if not token_info:
        return None
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
        session["token_info"] = token_info
    return spotipy.Spotify(auth=token_info["access_token"])

@app.route("/")
def index():
    app.logger.info("Request made to index endpoint")
    return "Spotify GPT Agent is live!"

@app.route("/login")
def login():
    app.logger.info("Request made to login endpoint")
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    app.logger.info("Request made to callback endpoint")
    code = request.args.get('code')
    if not code:
        app.logger.error("Missing authorization code in callback.")
        return jsonify({"error": "Missing authorization code"}), 400
    try:
        token_info = sp_oauth.get_access_token(code)
        session["token_info"] = token_info
        app.logger.info("Spotify token acquired and stored in session.")
        return redirect("/")
    except Exception as e:
        app.logger.error(f"Token exchange failed: {str(e)}")
        return jsonify({"error": str(e), "details": traceback.format_exc()}), 500

@app.route("/debug_token")
def debug_token():
    app.logger.info("Request made to debug_token endpoint")
    sp = get_spotify_client()
    if not sp:
        return jsonify({"error": "No valid session or token"}), 401
    try:
        user_info = sp.me()
        app.logger.info(f"Token debug successful for user: {user_info['id']}")
        return jsonify(user_info)
    except Exception as e:
        app.logger.error(f"Token debug failed: {str(e)}")
        return jsonify({"error": str(e), "details": traceback.format_exc()}), 500

@app.route("/token_handoff")
def token_handoff():
    app.logger.info("Request made to token_handoff endpoint")
    try:
        token_info = session.get("token_info")
        if not token_info:
            return jsonify({"error": "No token in session"}), 401
        return jsonify(token_info)
    except Exception as e:
        app.logger.error(f"Token handoff failed: {str(e)}")
        return jsonify({"error": str(e), "details": traceback.format_exc()}), 500

@app.route("/search_track", methods=["GET"])
def search_track():
    app.logger.info("Request made to search_track endpoint")
    sp = get_spotify_client()
    if not sp:
        return redirect("/login")
    query = request.args.get("q")
    try:
        results = sp.search(q=query, type="track", limit=5)
        app.logger.info(f"Search track: {query}")
        return jsonify(results)
    except Exception as e:
        app.logger.error(f"Error searching track '{query}': {str(e)}")
        return jsonify({"error": str(e), "details": traceback.format_exc()}), 500

@app.route("/search_album", methods=["GET"])
def search_album():
    app.logger.info("Request made to search_album endpoint")
    sp = get_spotify_client()
    if not sp:
        return redirect("/login")
    query = request.args.get("q")
    try:
        results = sp.search(q=query, type="album", limit=5)
        app.logger.info(f"Search album: {query}")
        return jsonify(results)
    except Exception as e:
        app.logger.error(f"Error searching album '{query}': {str(e)}")
        return jsonify({"error": str(e), "details": traceback.format_exc()}), 500

@app.route("/get_playlists", methods=["GET"])
def get_playlists():
    app.logger.info("Request made to get_playlists endpoint")
    sp = get_spotify_client()
    if not sp:
        return redirect("/login")
    try:
        playlists = sp.current_user_playlists()
        app.logger.info("Retrieved user playlists")
        return jsonify(playlists)
    except Exception as e:
        app.logger.error(f"Error retrieving playlists: {str(e)}")
        return jsonify({"error": str(e), "details": traceback.format_exc()}), 500

@app.route("/create_playlist", methods=["POST"])
def create_playlist():
    app.logger.info("Request made to create_playlist endpoint")
    sp = get_spotify_client()
    if not sp:
        return redirect("/login")
    data = request.json
    name = data.get("name")
    description = data.get("description", "")
    public = data.get("public", False)
    collaborative = data.get("collaborative", False)
    try:
        user_id = sp.me()["id"]
        new_playlist = sp.user_playlist_create(
            user=user_id,
            name=name,
            description=description,
            public=public,
            collaborative=collaborative
        )
        app.logger.info(f"Created playlist for user {user_id}: {new_playlist['id']}")
        return jsonify(new_playlist)
    except Exception as e:
        app.logger.error(f"Error creating playlist: {str(e)}")
        return jsonify({"error": str(e), "details": traceback.format_exc()}), 500

@app.route("/add_to_playlist", methods=["POST"])
def add_to_playlist():
    app.logger.info("Request made to add_to_playlist endpoint")
    sp = get_spotify_client()
    if not sp:
        return redirect("/login")
    data = request.json
    playlist_id = data["playlist_id"]
    track_uris = data["track_uris"]
    try:
        result = sp.playlist_add_items(playlist_id, track_uris)
        app.logger.info(f"Added tracks to playlist {playlist_id}: {track_uris}")
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error adding to playlist '{playlist_id}': {str(e)}")
        return jsonify({"error": str(e), "details": traceback.format_exc()}), 500

@app.route("/openapi.yaml")
def serve_openapi_yaml():
    app.logger.info("Request made to serve_openapi_yaml endpoint")
    return app.send_static_file("openapi.yaml")