from flask import Flask, jsonify, send_from_directory, request
import subprocess, os, signal, sys

app = Flask(__name__, static_folder="static", static_url_path="")

STREAM_SCRIPT = os.path.expanduser("~/peopleflow_app/camera_server.py")

# デフォルト（必要なら後でUI/環境変数化できる）
DEFAULT_CAMERA_ID = int(os.environ.get("CAMERA_ID", "0"))
DEFAULT_CAMERA_PORT = int(os.environ.get("CAMERA_PORT", "5001"))

PID_FILE = f"/tmp/peopleflow_stream_{DEFAULT_CAMERA_ID}_{DEFAULT_CAMERA_PORT}.pid"


def resolve_python_exec():
    """Prefer the bundled venv python, but fall back to the current interpreter."""
    venv_python = os.path.expanduser("~/peopleflow_app/.venv/bin/python")
    return venv_python if os.path.exists(venv_python) else sys.executable

def is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def get_local_ip():
    # 接続先に依存しない取り方（ルーティングがあれば取れる）
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"

@app.get("/")
def index():
    return app.send_static_file("index.html")

@app.get("/api/stream/status")
def stream_status():
    running = False
    pid = None
    if os.path.exists(PID_FILE):
        try:
            pid = int(open(PID_FILE).read().strip())
            running = is_running(pid)
            if not running:
                os.remove(PID_FILE)
        except Exception:
            pass

    ip = get_local_ip()
    url = f"http://{ip}:{DEFAULT_CAMERA_PORT}/stream" if ip != "unknown" else f"http://<pi-ip>:{DEFAULT_CAMERA_PORT}/stream"
    return jsonify({
        "running": running,
        "pid": pid,
        "camera_id": DEFAULT_CAMERA_ID,
        "port": DEFAULT_CAMERA_PORT,
        "stream_url": url
    })

@app.post("/api/stream/start")
def stream_start():
    # 既に動いてたらそのまま返す
    if os.path.exists(PID_FILE):
        pid = int(open(PID_FILE).read().strip())
        if is_running(pid):
            return jsonify({"ok": True, "running": True, "pid": pid, "message": "already running"})
        else:
            os.remove(PID_FILE)

    # Prefer bundled venv python; fall back to current interpreter.
    py = resolve_python_exec()
    cmd = [py, STREAM_SCRIPT, str(DEFAULT_CAMERA_ID), str(DEFAULT_CAMERA_PORT)]

    proc = subprocess.Popen(cmd, start_new_session=True)
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))

    return jsonify({"ok": True, "running": True, "pid": proc.pid})

@app.post("/api/stream/stop")
def stream_stop():
    if not os.path.exists(PID_FILE):
        return jsonify({"ok": True, "running": False, "message": "not running"})

    pid = int(open(PID_FILE).read().strip())
    try:
        os.killpg(pid, signal.SIGTERM)
    except Exception:
        pass

    try:
        os.remove(PID_FILE)
    except Exception:
        pass

    return jsonify({"ok": True, "running": False})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
