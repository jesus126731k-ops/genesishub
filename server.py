from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os, json, time, random, string, hashlib

app = Flask(__name__)
CORS(app)

DATA_FILE = "keys.json"
LINKVERTISE_FILE = "linkvertise_tracking.json"
COOLDOWN = 86400
SECRET = "G3N3SIS_HUB_2025"
LINKVERTISE_URL = "https://link-hub.net/1457789/3pNxakfWICZQ"
YOUR_WEBSITE = "https://genesishub-v2.onrender.com"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(LINKVERTISE_FILE):
    with open(LINKVERTISE_FILE, "w") as f:
        json.dump({}, f)

def generate_key():
    parts = []
    for _ in range(4):
        parts.append(''.join(random.choices(string.ascii_uppercase + string.digits, k=6)))
    return '-'.join(parts)

def get_user_id(ip, user_agent):
    return hashlib.md5(f"{ip}{user_agent[:50]}".encode()).hexdigest()

def mark_linkvertise_completed(user_id, ip):
    try:
        with open(LINKVERTISE_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    data[user_id] = {
        "ip": ip,
        "completed": True,
        "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "last_check": time.time()
    }
    
    with open(LINKVERTISE_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    return True

def check_linkvertise_completed(user_id):
    try:
        with open(LINKVERTISE_FILE, "r") as f:
            data = json.load(f)
    except:
        return False
    
    if user_id in data:
        if time.time() - data[user_id].get("last_check", 0) < 3600:
            return data[user_id].get("completed", False)
    
    return False

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

# ========== ENDPOINTS FALTANTES ==========

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(".", "favicon.ico", mimetype='image/vnd.microsoft.icon')

@app.route("/genesis")
def genesis():
    return send_from_directory(".", "index.html")

@app.route("/linkvertise-success")
def linkvertise_success():
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    user_id = get_user_id(ip, user_agent)
    
    mark_linkvertise_completed(user_id, ip)
    
    return f"""
    <html>
    <head>
        <meta http-equiv="refresh" content="3;url={YOUR_WEBSITE}">
        <title>Redirecting...</title>
        <style>
            body {{ background: #000; color: #fff; font-family: Arial; text-align: center; padding: 50px; }}
            .success {{ color: #00ff00; font-size: 24px; }}
        </style>
    </head>
    <body>
        <div class="success">✓ Linkvertise completed! Redirecting...</div>
        <p>You will be redirected in 3 seconds...</p>
        <script>
            setTimeout(function() {{
                window.location.href = "{YOUR_WEBSITE}";
            }}, 3000);
        </script>
    </body>
    </html>
    """

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)

@app.route("/check-linkvertise", methods=["GET"])
def check_linkvertise():
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    user_id = get_user_id(ip, user_agent)
    
    completed = check_linkvertise_completed(user_id)
    
    return jsonify({
        "completed": completed,
        "linkvertise_url": LINKVERTISE_URL if not completed else None,
        "redirect_url": f"{YOUR_WEBSITE}/linkvertise-success"
    })

@app.route("/can-generate", methods=["GET"])
def can_generate():
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    user_id = get_user_id(ip, user_agent)
    
    if not check_linkvertise_completed(user_id):
        return jsonify({
            "can_generate": False,
            "reason": "Complete Linkvertise first",
            "linkvertise_url": LINKVERTISE_URL,
            "redirect_url": f"{YOUR_WEBSITE}/linkvertise-success"
        })
    
    clean_keys()
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    if ip in data:
        remaining = data[ip]["expires"] - time.time()
        if remaining > 0:
            hours = int(remaining / 3600)
            minutes = int((remaining % 3600) / 60)
            return jsonify({
                "can_generate": False,
                "reason": f"Wait {hours}h {minutes}m",
                "time_remaining": remaining
            })
    
    return jsonify({"can_generate": True})

@app.route("/generate-key", methods=["POST"])
def generate_key_endpoint():
    clean_keys()
    
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    user_id = get_user_id(ip, user_agent)
    
    if not check_linkvertise_completed(user_id):
        return jsonify({
            "success": False,
            "message": "Complete Linkvertise first: " + LINKVERTISE_URL,
            "error_code": "LINKVERTISE_REQUIRED"
        }), 403
    
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
            return jsonify({
                "success": False,
                "message": f"Wait {hours}h {minutes}m",
                "time_remaining": remaining
            }), 429
    
    key = generate_key()
    data[ip] = {
        "key": key,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "expires": current_time + COOLDOWN,
        "ip": ip,
        "user_agent": user_agent,
        "linkvertise_completed": True,
        "used_in_roblox": False,
        "roblox_used_at": None
    }
    
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    return jsonify({
        "success": True,
        "key": key,
        "created": data[ip]["created"],
        "expires_in": COOLDOWN
    })

@app.route("/verify-roblox", methods=["POST"])
def verify_roblox():
    data = request.get_json()
    
    if not data or 'key' not in data:
        return jsonify({"success": False, "error": "No key"}), 400
    
    key = data['key']
    clean_keys()
    
    try:
        with open(DATA_FILE, "r") as f:
            keys_data = json.load(f)
    except:
        return jsonify({"success": False, "error": "DB error"}), 500
    
    current_time = time.time()
    
    for ip, info in keys_data.items():
        if info.get("key") == key:
            if current_time < info.get("expires", 0):
                if not info.get("used_in_roblox", False):
                    info["used_in_roblox"] = True
                    info["roblox_used_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    with open(DATA_FILE, "w") as f:
                        json.dump(keys_data, f, indent=2)
                    
                    return jsonify({
                        "success": True,
                        "valid": True,
                        "message": "Key verified for Roblox"
                    })
                else:
                    return jsonify({
                        "success": True,
                        "valid": True,
                        "message": "Key already used"
                    })
            else:
                return jsonify({
                    "success": False,
                    "valid": False,
                    "error": "Key expired"
                }), 410
    
    return jsonify({
        "success": False,
        "valid": False,
        "error": "Invalid key"
    }), 404

@app.route("/check-key/<key>", methods=["GET"])
def check_key(key):
    clean_keys()
    
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        return jsonify({"error": "DB error"}), 500
    
    current_time = time.time()
    
    for info in data.values():
        if info.get("key") == key:
            expired = current_time >= info.get("expires", 0)
            return jsonify({
                "exists": True,
                "expired": expired,
                "created": info.get("created"),
                "expires_at": info.get("expires"),
                "used_in_roblox": info.get("used_in_roblox", False)
            })
    
    return jsonify({"exists": False})

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
    
    try:
        with open(LINKVERTISE_FILE, "r") as f:
            linkvertise_data = json.load(f)
    except:
        linkvertise_data = {}
    
    return jsonify({
        "total_keys": len(data),
        "active_keys": active,
        "expired_keys": expired,
        "linkvertise_completed": len(linkvertise_data),
        "keys": data,
        "linkvertise_users": linkvertise_data
    })

if __name__ == "__main__":
    print(f"Genesis Hub V2 - Server Running")
    print(f"Website: {YOUR_WEBSITE}")
    print(f"Linkvertise: {LINKVERTISE_URL}")
    app.run(host="0.0.0.0", port=3000, debug=False)
