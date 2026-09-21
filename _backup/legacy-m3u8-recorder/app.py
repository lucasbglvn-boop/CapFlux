import os
import subprocess
import sys

from flask import Flask, jsonify, render_template, request

from recorder import RecorderManager, load_config

app = Flask(__name__)
manager = RecorderManager()


@app.route("/")
def index():
    config = load_config()
    return render_template("index.html", default_output=config["default_output_folder"])


@app.route("/api/start", methods=["POST"])
def api_start():
    data = request.get_json(force=True)
    try:
        result = manager.start_recording(
            data.get("room_label", ""),
            data.get("link_text", ""),
            data.get("output_folder", "").strip(),
        )
        return jsonify({"ok": True, "session": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/stop", methods=["POST"])
def api_stop():
    data = request.get_json(force=True)
    try:
        result = manager.stop_recording(data.get("job_id", "").strip())
        return jsonify({"ok": True, "session": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/stop-all", methods=["POST"])
def api_stop_all():
    manager.stop_all()
    return jsonify({"ok": True})


@app.route("/api/status")
def api_status():
    return jsonify({"ok": True, "sessions": manager.get_status()})


@app.route("/api/log/<job_id>")
def api_log(job_id):
    return jsonify({"ok": True, "log": manager.get_log(job_id)})


@app.route("/api/pick-folder", methods=["POST"])
def api_pick_folder():
    data = request.get_json(force=True) or {}
    initial_dir = data.get("current_folder", "").strip()
    if not initial_dir or not os.path.isdir(initial_dir):
        initial_dir = load_config()["default_output_folder"]
        if not os.path.isdir(initial_dir):
            initial_dir = os.path.expanduser("~")

    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pick_folder.py")
    try:
        result = subprocess.run(
            [sys.executable, script_path, initial_dir],
            capture_output=True, text=True, timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        folder = result.stdout.strip()
        if not folder:
            return jsonify({"ok": False, "cancelled": True})
        return jsonify({"ok": True, "folder": folder})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
