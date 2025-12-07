from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os, json, time, random, string, hashlib

app = Flask(__name__)
CORS(app)

DATA_FILE = "keys.json"
LINKVERTISE_FILE = "linkvertise_tracking.json"
COOLDOWN = 86400
SECRET = "G3N3SIS_HUB_2025"

# TUS LINKS REALES
LINKVERTISE_URL = "https://link-hub.net/1457789/3pNxakfWICZQ"
YOUR_WEBSITE = "https://genesishub-v2.onrender.com"

# Inicializar archivos
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(LINKVERTISE_FILE):
    with open(LINKVERTISE_FILE, "w") as f:
        json.dump({}, f)

def generate_key():
    """Genera key de 15 caracteres: ABC12-XYZ34-PQR56"""
    key_parts = []
    
    for _ in range(3):
        letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
        numbers = ''.join(random.choices('0123456789', k=2))
        key_parts.append(f"{letters}{numbers}")
    
    key = '-'.join(key_parts)
    
    # Verificar unicidad
    if not is_key_already_used(key):
        return key
    else:
        return generate_key()

def is_key_already_used(key):
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
            
            for info in data.values():
                if info.get("key") == key:
                    return True
        return False
    except:
        return False

def get_user_id(ip, user_agent):
    return hashlib.md5(f"{ip}{user_agent[:50]}".encode()).hexdigest()

def mark_linkvertise_completed(user_id, ip):
    data = {}
    if os.path.exists(LINKVERTISE_FILE):
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
    if not os.path.exists(LINKVERTISE_FILE):
        return False
    
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
    if not os.path.exists(DATA_FILE):
        return 0
    
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

@app.route("/linkvertise-success")
def linkvertise_success():
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    user_id = get_user_id(ip, user_agent)
    
    mark_linkvertise_completed(user_id, ip)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Linkvertise Success</title>
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
    </head>
    <body>
        <div class="success">✓ Linkvertise Completed!</div>
        <p>Redirecting to Genesis Hub V2...</p>
        <script>
            setTimeout(function() {{
                window.location.href = "{YOUR_WEBSITE}";
            }}, 2000);
        </script>
    </body>
    </html>
    """
    return html

@app.route("/check-linkvertise", methods=["GET"])
def check_linkvertise():
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    user_id = get_user_id(ip, user_agent)
    
    completed = check_linkvertise_completed(user_id)
    
    return jsonify({
        "completed": completed,
        "linkvertise_url": LINKVERTISE_URL if not completed else None
    })

@app.route("/can-generate", methods=["GET"])
def can_generate():
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    user_id = get_user_id(ip, user_agent)
    
    if not check_linkvertise_completed(user_id):
        return jsonify({
            "can_generate": False,
            "reason": "Complete Linkvertise first"
        })
    
    clean_keys()
    data = {}
    if os.path.exists(DATA_FILE):
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
                "reason": f"Wait {hours}h {minutes}m"
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
            "message": "Complete Linkvertise first"
        }), 403
    
    current_time = time.time()
    
    data = {}
    if os.path.exists(DATA_FILE):
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
                "message": f"Wait {hours}h {minutes}m"
            }), 429
    
    key = generate_key()
    data[ip] = {
        "key": key,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "expires": current_time + COOLDOWN,
        "ip": ip,
        "user_agent": user_agent,
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
    
    data = {}
    if os.path.exists(DATA_FILE):
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

@app.route("/verify-roblox", methods=["POST"])
def verify_roblox():
    data = request.get_json()
    
    if not data or 'key' not in data:
        return jsonify({"success": False, "error": "No key"}), 400
    
    key = data['key']
    clean_keys()
    
    keys_data = {}
    if os.path.exists(DATA_FILE):
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
                        "valid": True
                    })
                else:
                    return jsonify({
                        "success": True,
                        "valid": True,
                        "message": "Already used"
                    })
            else:
                return jsonify({
                    "success": False,
                    "error": "Expired"
                }), 410
    
    return jsonify({
        "success": False,
        "error": "Invalid"
    }), 404

@app.route("/admin/<secret>", methods=["GET"])
def admin(secret):
    if secret != SECRET:
        return jsonify({"error": "Unauthorized"}), 403
    
    clean_keys()
    data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
        except:
            data = {}
    
    current_time = time.time()
    active = sum(1 for info in data.values() if current_time < info.get("expires", 0))
    
    linkvertise_data = {}
    if os.path.exists(LINKVERTISE_FILE):
        try:
            with open(LINKVERTISE_FILE, "r") as f:
                linkvertise_data = json.load(f)
        except:
            linkvertise_data = {}
    
    return jsonify({
        "total_keys": len(data),
        "active_keys": active,
        "expired_keys": len(data) - active,
        "linkvertise_completed": len(linkvertise_data)
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print(f"Starting Genesis Hub V2 on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)

