from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os, json, time, random, string, hashlib

app = Flask(__name__, static_folder='.')
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

# ========== NUEVAS FUNCIONES AGREGADAS ==========
def get_real_ip():
    """OBTIENE LA IP REAL DEL USUARIO (NUEVO)"""
    ip_headers = ['X-Real-IP', 'X-Forwarded-For', 'CF-Connecting-IP']
    for header in ip_headers:
        ip = request.headers.get(header)
        if ip:
            if ',' in ip:
                return ip.split(',')[0].strip()
            return ip
    return request.remote_addr

def get_unique_user_id():
    """CREA UN ID ÚNICO POR USUARIO (NUEVO)"""
    ip = get_real_ip()
    user_agent = request.headers.get('User-Agent', '')
    return hashlib.md5(f"{ip}{user_agent[:50]}".encode()).hexdigest()
# ========== FIN DE NUEVAS FUNCIONES ==========

def generate_key():
    parts = []
    for _ in range(3):
        parts.append(''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3)) + ''.join(random.choices('0123456789', k=2)))
    return '-'.join(parts)

def mark_linkvertise_completed(user_id):
    try:
        with open(LINKVERTISE_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    data[user_id] = {
        "completed": True,
        "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": time.time()
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
        if time.time() - data[user_id].get("timestamp", 0) < 86400:
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

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)

@app.route("/linkvertise")
@app.route("/linkvertise/")
@app.route("/linkvertise-success")
@app.route("/linkvertise-success/")
def handle_linkvertise():
    user_id = get_unique_user_id()
    mark_linkvertise_completed(user_id)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>✅ Linkvertise Completed</title>
        <style>
            body {{
                background: #000;
                color: #fff;
                font-family: Arial;
                text-align: center;
                padding: 50px;
            }}
            .success {{
                color: #0f0;
                font-size: 24px;
                margin: 20px 0;
            }}
        </style>
        <script>
            setTimeout(function() {{
                window.location.href = "{YOUR_WEBSITE}";
            }}, 3000);
        </script>
    </head>
    <body>
        <div class="success">✅ Linkvertise Completed!</div>
        <p>Redirecting to Genesis Hub V2...</p>
    </body>
    </html>
    """

@app.route("/check-linkvertise", methods=["GET"])
def check_linkvertise():
    user_id = get_unique_user_id()
    completed = check_linkvertise_completed(user_id)
    
    return jsonify({
        "completed": completed,
        "message": "Linkvertise completed" if completed else "Linkvertise required"
    })

@app.route("/generate-key", methods=["POST"])
def generate_key_endpoint():
    clean_keys()
    
    user_id = get_unique_user_id()
    ip = get_real_ip()
    
    if not check_linkvertise_completed(user_id):
        return jsonify({
            "success": False,
            "message": "Complete Linkvertise first",
            "error_code": "LINKVERTISE_REQUIRED"
        }), 403
    
    current_time = time.time()
    
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    # VERIFICAR POR USER_ID EN LUGAR DE IP (CORRECCIÓN)
    user_has_key = False
    user_key_expires = 0
    
    for key_data in data.values():
        if key_data.get("user_id") == user_id:
            user_has_key = True
            user_key_expires = key_data.get("expires", 0)
            break
    
    if user_has_key and current_time < user_key_expires:
        remaining = user_key_expires - current_time
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
        "user_agent": request.headers.get('User-Agent', ''),
        "user_id": user_id,
        "linkvertise_completed": True,
        "used_in_roblox": False
    }
    
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    return jsonify({
        "success": True,
        "key": key,
        "created": data[ip]["created"],
        "expires_in": COOLDOWN
    })

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
                "used_in_roblox": info.get("used_in_roblox", False)
            })
    
    return jsonify({"exists": False})

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
                    
                    return jsonify({"success": True, "valid": True})
                else:
                    return jsonify({"success": True, "valid": True, "message": "Already used"})
            else:
                return jsonify({"success": False, "error": "Expired"}), 410
    
    return jsonify({"success": False, "error": "Invalid"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print(f"🚀 Genesis Hub V2 running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
