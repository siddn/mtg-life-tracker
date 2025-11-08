from flask import Flask, render_template, request, url_for, redirect
from flask_socketio import SocketIO, join_room, emit
import time
import threading
import requests

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

request_headers = {
    'User-Agent': 'MTGLifeTrackerApp/1.0',
    'Accept': 'application/json',
}

# Simple in-memory store for life trackers per per lobby
# Each lobby is deffined by its key, a lobby ID, which mapps to a dict of life tracker states. The keys in that dict are the player IDs, which start as P1, P2, etc.
# IDs can be added dynamically as needed, and an affiliated "name" can be stored alongside the life total.
lobby_template = {
    "P1": {"life": 40, "name": "Player 1", "commander_damage": {}, "poison": 0},
    "P2": {"life": 40, "name": "Player 2", "commander_damage": {}, "poison": 0},
    "P3": {"life": 40, "name": "Player 3", "commander_damage": {}, "poison": 0},
    "P4": {"life": 40, "name": "Player 4", "commander_damage": {}, "poison": 0},
}

lobby_cache = {}
last_seen = {}

lobby_TTL = 60 * 60  # 1 hour

def lobby_prune():
    current_time = time.time()
    for lobby_id, last_seen_time in last_seen.items():
        if current_time - last_seen_time > lobby_TTL:
            del lobby_cache[lobby_id]
            del last_seen[lobby_id]
    
threading.Thread(target=lobby_prune, daemon=True).start()

def generate_lobby_id():
    random_mtg_card = requests.get("https://api.scryfall.com/cards/random", headers=request_headers).json()
    # Sanitize the card name to be URL-friendly
    card_name = random_mtg_card["name"].replace(" ", "-").lower()
    card_name = card_name.replace("'", "")
    card_name = card_name.replace(",", "")
    card_name = card_name.replace(":", "")
    if card_name not in lobby_cache.keys():
        return card_name
    return generate_lobby_id()

@app.route("/", methods=["GET", "POST"])
def index():
    if (request.method == "POST"):
        lobby_id = request.form.get("lobby_id")
        if not lobby_id:
            lobby_id = generate_lobby_id()
        return redirect(url_for("lobby", lobby_id=lobby_id))
    return render_template("index.html")

@app.route("/lobby/<lobby_id>")
def lobby(lobby_id):
    return render_template("lobby.html", lobby_id=lobby_id)

@socketio.on("join")
def on_join(data):
    lobby = data["lobby"]
    join_room(lobby)
    if lobby not in lobby_cache:
        lobby_cache[lobby] = lobby_template.copy()
    emit("update", lobby_cache[lobby], room=lobby)
    last_seen[lobby] = time.time()

@socketio.on("change")
def on_change(data):
    lobby = data["lobby"]
    delta = data["delta"]
    player = data["player"]
    lobby_cache[lobby][player]["life"] = lobby_cache[lobby][player].get("life", 20) + delta
    emit("update", lobby_cache[lobby], room=lobby)
    last_seen[lobby] = time.time()

@socketio.on("change_commander_damage")
def on_change_commander_damage(data):
    lobby = data["lobby"]
    identifier = data["identifier"]
    otherId = data["otherId"]
    delta = data["delta"]
    lobby_cache[lobby][identifier]["commander_damage"][otherId] = lobby_cache[lobby][identifier]["commander_damage"].get(otherId, 0) + delta
    emit("update", lobby_cache[lobby], room=lobby)
    last_seen[lobby] = time.time()

@socketio.on("change_poison")
def on_change_poison(data):
    lobby = data["lobby"]
    delta = data["delta"]
    player = data["player"]
    lobby_cache[lobby][player]["poison"] = lobby_cache[lobby][player].get("poison", 0) + delta
    emit("update", lobby_cache[lobby], room=lobby)
    last_seen[lobby] = time.time()

@socketio.on("rename")
def on_rename(data):
    lobby = data["lobby"]
    player = data["player"]
    new_name = data["name"]
    lobby_cache[lobby][player]["name"] = new_name
    emit("update", lobby_cache[lobby], room=lobby)
    last_seen[lobby] = time.time()

@socketio.on("add_player")
def on_add_player(data):
    lobby = data["lobby"]
    player_id = f"P{len(lobby_cache[lobby]) + 1}"
    lobby_cache[lobby][player_id] = {"life": 40, "name": f"Player {len(lobby_cache[lobby]) + 1}", "commander_damage": {}, "poison": 0}
    emit("update", lobby_cache[lobby], room=lobby)
    last_seen[lobby] = time.time()

@socketio.on("remove_player")
def on_remove_player(data):
    # remove the last player added
    lobby = data["lobby"]
    if len(lobby_cache[lobby]) > 1:
        player_id = f"P{len(lobby_cache[lobby])}"
        del lobby_cache[lobby][player_id]
        emit("update", lobby_cache[lobby], room=lobby)
    last_seen[lobby] = time.time()

@socketio.on("reset")
def on_reset(data):
    lobby = data["lobby"]
    # Reset life totals to 40 and other stats to default
    for player in lobby_cache[lobby].values():
        player["life"] = 40
        player["commander_damage"] = {}
        player["poison"] = 0
    emit("update", lobby_cache[lobby], room=lobby)
    last_seen[lobby] = time.time()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MTG Life Tracker App")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    socketio.run(app, host="0.0.0.0", port=5000, debug=args.debug)