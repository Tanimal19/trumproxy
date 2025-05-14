from flask import Flask, request
from trumproxy import proxy_instance

app = Flask(__name__)

@app.route("/pause", methods=["POST"])
def pause():
    proxy_instance.pause_proxy()
    return "Proxy paused"

@app.route("/resume", methods=["POST"])
def resume():
    proxy_instance.resume_proxy()
    return "Proxy resumed"

@app.route("/delay", methods=["POST"])
def delay():
    ip = request.json["ip"]
    seconds = int(request.json["seconds"])
    proxy_instance.set_delay_for_ip(ip, seconds)
    return f"Set delay {seconds}s for {ip}"
