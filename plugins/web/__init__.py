from threading import Thread
import os
import logging
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO, emit

from pokemongo_bot import logger
from pokemongo_bot.event_manager import manager
from api.json_encodable import JSONEncodable

# pylint: disable=unused-variable, unused-argument

logging.getLogger('socketio').disabled = True
logging.getLogger('engineio').disabled = True
logging.getLogger('werkzeug').disabled = True


def run_flask():
    root_dir = os.path.join(os.getcwd(), 'web')
    app = Flask(__name__, static_folder=root_dir)
    app.use_reloader = False
    app.debug = False
    app.config["SECRET_KEY"] = "OpenPoGoBot"
    socketio = SocketIO(app, logging=False, engineio_logger=False)

    cached_events = {
        "logging": []
    }

    active_bots = set()

    @manager.on("bot_initialized")
    def bot_initialized(bot):
        active_bots.add(bot.get_username())
        socketio.emit("bot_initialized", bot.get_username(), namespace="/event")

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    @app.route("/<path:path>")
    def static_proxy(path):
        return app.send_static_file(path)

    @app.route("/get-running-bots")
    def get_running_bots():
        return jsonify(list(active_bots))

    @socketio.on("connect", namespace="/event")
    def connect():
        for event in cached_events:
            socketio.emit(event, cached_events[event], namespace="/event")
        logger.log("Web client connected", "yellow", fire_event=False)

    @socketio.on("disconnect", namespace="/event")
    def disconnect():
        logger.log("Web client disconnected", "yellow", fire_event=False)

    @manager.on("logging")
    def logging_event(text="", color="black"):
        line = {"output": text, "color": color}
        cached_events["logging"].append(line)
        socketio.emit("logging", [line], namespace="/event")

    @manager.on("position_updated")
    def position_update(bot, coordinates=None):
        if coordinates is None:
            return
        emitted_object = {
            "coordinates": coordinates,
            "username": bot.get_username()
        }
        cached_events["position"] = emitted_object
        socketio.emit("position", emitted_object, namespace="/event")

    @manager.on("gyms_found", priority=-2000)
    def gyms_found_event(bot=None, gyms=None):
        if gyms is None or len(gyms) == 0:
            return
        emitted_object = {
            "gyms": JSONEncodable.encode_list(gyms),
            "username": bot.get_username()
        }
        cached_events["gyms"] = emitted_object
        socketio.emit("gyms", emitted_object, namespace="/event")

    @manager.on("pokestops_found", priority=-2000)
    def pokestops_found_event(bot=None, pokestops=None):
        if pokestops is None or len(pokestops) == 0:
            return
        emitted_object = {
            "pokestops": JSONEncodable.encode_list(pokestops),
            "username": bot.get_username()
        }
        cached_events["pokestops"] = emitted_object
        socketio.emit("pokestops", emitted_object, namespace="/event")

    @manager.on("player_update", priority=-2000)
    def player_updated_event(bot=None, player=None):
        if player is None:
            return
        emitted_object = {
            "player": player.to_json_encodable(),
            "username": bot.get_username()
        }
        cached_events["player"] = emitted_object
        socketio.emit("player", emitted_object, namespace="/event")

    @manager.on("inventory_update", priority=-2000)
    def inventory_updated_event(bot, inventory=None):
        # type: (PokemonGoBot, Dict[int, int]) -> None
        if inventory is None or inventory.get("count", 0) == 0:
            return
        emitted_object = {
            "inventory": inventory,
            "username": bot.get_username()
        }
        cached_events["inventory"] = emitted_object
        socketio.emit("inventory", emitted_object, namespace="/event")

    @manager.on("pokemon_found", priority=-2000)
    def pokemon_found_event(bot=None, encounters=None):
        if encounters is None or len(encounters) == 0:
            return
        emitted_object = {
            "nearby_pokemon": JSONEncodable.encode_list(encounters),
            "username": bot.get_username()
        }
        cached_events["nearby_pokemon"] = emitted_object
        socketio.emit("nearby_pokemon", emitted_object, namespace="/event")

    socketio.run(app, host="0.0.0.0", port=8000, debug=False, use_reloader=False, log_output=False)


WEB_THREAD = Thread(target=run_flask)
WEB_THREAD.daemon = True
WEB_THREAD.start()
