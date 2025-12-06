from flask import Flask, jsonify, request, abort
import random
import string
import time
import json
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "keys.json")

COOLDOWN = 86400
SECRET = "G3N3SIS_HUB_2025"
LINKVERTISE_DOMAIN = "link-hub.net"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        f.write("{}")

def create_key():
    return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(24))

def clean_expired():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    now = time.time()
    clean = {}

    for ip in data:
        if now < data[ip]["exp"]:
            clean[ip] = data[ip]

    with open(DATA_FILE, "w") as f:
        json.dump(clean, f)

def blocked_ip(ip):
    bad_prefix = ["10.", "172.", "192.", "127."]
    for p in bad_prefix:
        if ip.startswith(p):
            return True
    return False

@app.route("/")
@app.route("/genesis")
def home():
    return "Genesis Hub online"

@app.route("/generar")
def generar():
    clean_expired()

    ip = request.remote_addr
    referer = request.headers.get("Referer", "")

    if blocked_ip(ip):
        return jsonify({"error": "Access denied"}), 403

    if LINKVERTISE_DOMAIN not in referer:
        return jsonify({"error": "You must come from Linkvertise"}), 403

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    now = time.time()

    if ip in data:
        restantes = int((data[ip]["exp"] - now) / 3600)
        if restantes > 0:
            return jsonify({"error": f"Wait {restantes} hours"}), 403

    key = create_key()

    data[ip] = {
        "key": key,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "exp": now + COOLDOWN
    }

    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

    return jsonify({"key": key})

@app.route("/validar/<key>")
def validar(key):
    clean_expired()

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    for ip in data:
        if data[ip]["key"] == key:
            return jsonify({"valid": True})

    return jsonify({"valid": False})

@app.route("/admin/<s>")
def admin(s):
    if s != SECRET:
        abort(404)

    with open(DATA_FILE, "r") as f:
        return jsonify(json.load(f))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)

