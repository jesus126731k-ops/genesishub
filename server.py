from flask import Flask, jsonify, send_from_directory, request, abort
import random, string, time, json, os

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys.json")
COOLDOWN = 86400
SECRET = "G3N3SIS_HUB_2025"
LINKVERTISE_DOMAIN = "https://link-hub.net/1457789/3pNxakfWICZQ"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def generate_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=24))

def clean_expired():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    now = time.time()
    data = {ip: v for ip, v in data.items() if now < v["expire"]}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

@app.route("/")
@app.route("/genesis")
def home():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "index.html")

@app.route("/generate")
def generate():
    clean_expired()
    ip = request.remote_addr
    referer = request.headers.get("Referer", "")

    if LINKVERTISE_DOMAIN not in referer:
        return jsonify({"error": "Access denied, verify Linkvertise first"}), 403

    now = time.time()
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    if ip in data:
        remaining = int((data[ip]["expire"] - now) / 3600)
        return jsonify({"error": f"Key already generated. Try again in {remaining}h"}), 429

    key = generate_key()
    data[ip] = {
        "key": key,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "expire": now + COOLDOWN,
        "ip": ip
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)
    return jsonify({"key": key, "timestamp": data[ip]["timestamp"]})

@app.route("/validate/<key>")
def validate(key):
    clean_expired()
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    for record in data.values():
        if record["key"] == key and time.time() < record["expire"]:
            return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route("/admin/<secret>")
def admin(secret):
    if secret != SECRET:
        abort(404)
    with open(DATA_FILE, "r") as f:
        return jsonify(json.load(f))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
