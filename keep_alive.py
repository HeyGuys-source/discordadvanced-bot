import os
import threading
import time
import datetime
from flask import Flask, request, jsonify, Response
from werkzeug.serving import make_server

# Advanced Flask Server Class (non-blocking)
class ServerThread(threading.Thread):
    def __init__(self, app, host="0.0.0.0", port=8080):
        threading.Thread.__init__(self)
        self.srv = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()
        self.daemon = True

    def run(self):
        print(f"[KeepAlive] Flask server starting on http://0.0.0.0:8080")
        self.srv.serve_forever()

    def shutdown(self):
        print("[KeepAlive] Shutting down Flask server...")
        self.srv.shutdown()

# Instantiate Flask app
app = Flask("keep_alive_server")

# Keep-alive data
server_start_time = time.time()
ping_log = []

# Root endpoint (Render pings this)
@app.route("/", methods=["GET"])
def index():
    return Response("Bot is alive. ✔️", status=200, mimetype="text/plain")

# Health check / status endpoint
@app.route("/health", methods=["GET"])
def health_check():
    uptime = str(datetime.timedelta(seconds=int(time.time() - server_start_time)))
    return jsonify({
        "status": "online",
        "uptime": uptime,
        "ping_count": len(ping_log)
    }), 200

# Logging endpoint (if you want to ping it externally for logs)
@app.route("/ping", methods=["POST", "GET"])
def log_ping():
    now = datetime.datetime.utcnow().isoformat()
    ping_log.append(now)
    if len(ping_log) > 100:
        ping_log.pop(0)
    return jsonify({"message": "Ping received.", "timestamp": now}), 200

# Optional shutdown route (protect this!)
@app.route("/shutdown", methods=["POST"])
def shutdown():
    shutdown_token = request.headers.get("Authorization")
    if shutdown_token != os.getenv("KEEPALIVE_SHUTDOWN_TOKEN", "default_token"):
        return jsonify({"error": "Unauthorized"}), 403
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        return jsonify({"error": "Server shutdown failed"}), 500
    func()
    return jsonify({"message": "Server shutting down..."}), 200

# Keep-alive entrypoint
def keep_alive():
    print("[KeepAlive] Initializing keep_alive service...")
    server = ServerThread(app)
    server.start()
