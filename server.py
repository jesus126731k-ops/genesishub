from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os, json, time, random, string

app = Flask(__name__)
CORS(app)

DATA_FILE = "keys.json"
COOLDOWN = 86400
SECRET = "G3N3SIS_HUB_2025"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def generate_key():
    parts = []
    for _ in range(4):
        parts.append(''.join(random.choices(string.ascii_uppercase + string.digits, k=6)))
    return '-'.join(parts)

def clean_keys():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    current_time = time.time()
    cleaned = {ip: info for ip, info in data.items() if current_time < info.get("expires", 0)}
    
    with open(DATA_FILE, "w") as f:
        json.dump(cleaned, f, indent=2)
    
    return len(data) - len(cleaned)

@app.route("/")
@app.route("/genesis")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)

@app.route("/generate-key", methods=["POST"])
def generate_key_endpoint():
    clean_keys()
    
    ip = request.remote_addr
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]
    
    current_time = time.time()
    
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    if ip in data:
        remaining = data[ip]["expires"] - current_time
        if remaining > 0:
            hours = int(remaining / 3600)
            minutes = int((remaining % 3600) / 60)
            seconds = int(remaining % 60)
            
            return jsonify({
                "success": False,
                "message": f"Wait {hours}h {minutes}m {seconds}s",
                "time_remaining": remaining,
                "error_code": "COOLDOWN"
            }), 429
    
    key = generate_key()
    data[ip] = {
        "key": key,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "expires": current_time + COOLDOWN,
        "ip": ip,
        "user_agent": request.headers.get('User-Agent', 'Unknown')
    }
    
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    return jsonify({
        "success": True,
        "key": key,
        "created": data[ip]["created"],
        "expires_in": COOLDOWN,
        "message": "Key generated"
    })

@app.route("/validate/<key>", methods=["GET"])
def validate(key):
    clean_keys()
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    current_time = time.time()
    for info in data.values():
        if info.get("key") == key and current_time < info.get("expires", 0):
            return jsonify({"valid": True, "created": info.get("created")})
    
    return jsonify({"valid": False})

@app.route("/admin/<secret>", methods=["GET"])
def admin(secret):
    if secret != SECRET:
        return jsonify({"error": "Unauthorized"}), 403
    
    clean_keys()
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    current_time = time.time()
    active = sum(1 for info in data.values() if current_time < info.get("expires", 0))
    expired = len(data) - active
    
    return jsonify({
        "total": len(data),
        "active": active,
        "expired": expired,
        "keys": data
    })

if __name__ == "__main__":
    print("Genesis Hub V2 - Key Generator")
    print("Server: http://0.0.0.0:3000")
    app.run(host="0.0.0.0", port=3000, debug=False)
