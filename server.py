from flask import Flask, jsonify, request, send_from_directory, abort
import os, json, time, random, string

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "keys.json")

SECRET = "G3N3SIS_HUB_2025"
COOLDOWN = 86400

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def generate_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=25))

def clean_expired():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    now = time.time()
    cleaned = {}

    for ip, info in data.items():
        if now < info["expires"]:
            cleaned[ip] = info

    with open(DATA_FILE, "w") as f:
        json.dump(cleaned, f)

@app.route("/")
@app.route("/genesis")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/generate")
def generate():
    clean_expired()

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    now = time.time()

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    if ip in data:
        remaining = int((data[ip]["expires"] - now) / 3600)
        return jsonify({
            "status": "cooldown",
            "hours_left": remaining
        })

    key = generate_key()

    data[ip] = {
        "key": key,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "expires": now + COOLDOWN,
        "ip": ip
    }

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

    return jsonify({
        "status": "ok",
        "key": key
    })

@app.route("/validate/<string:user_key>")
def validate(user_key):
    clean_expired()

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    for info in data.values():
        if info["key"] == user_key:
            if time.time() < info["expires"]:
                return jsonify({"valid": True})
            else:
                return jsonify({"valid": False})

    return jsonify({"valid": False})

@app.route("/admin/<string:secret>")
def admin(secret):
    if secret != SECRET:
        abort(403)

    with open(DATA_FILE, "r") as f:
        return jsonify(json.load(f))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
