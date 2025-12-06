from flask import Flask, jsonify, send_from_directory, request, abort
import random, string, time, json, os

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys.json")
COOLDOWN = 86400
SECRET = "G3N3SIS_HUB_2025"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def generate_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=24))

def clean_keys():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    now = time.time()
    data = {ip:info for ip, info in data.items() if now < info["e"]}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

@app.route("/")
@app.route("/genesis")
def home():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "index.html")

@app.route("/generar")
def generar():
    clean_keys()
    ip = request.remote_addr
    now = time.time()
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    if ip in data:
        remaining_hours = int((data[ip]["e"] - now)/3600)
        return jsonify({"e": f"{remaining_hours}h"})
    key = generate_key()
    data[ip] = {"k": key, "t": time.strftime("%Y-%m-%d %H:%M:%S"), "e": now + COOLDOWN, "i": ip}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)
    return jsonify({"k": key, "t": data[ip]["t"]})

@app.route("/validar/<key>")
def validar(key):
    clean_keys()
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    for info in data.values():
        if info["k"] == key and time.time() < info["e"]:
            return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route("/x/<s>")
def x(s):
    if s != SECRET:
        abort(404)
    with open(DATA_FILE, "r") as f:
        return jsonify(json.load(f))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
