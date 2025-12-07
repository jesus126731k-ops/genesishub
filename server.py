from flask import Flask, jsonify, request, send_from_directory, redirect
from flask_cors import CORS
import os, json, time, random, string, hashlib
from datetime import datetime, timedelta

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

def get_real_ip():
    ip_headers = ['X-Real-IP', 'X-Forwarded-For', 'CF-Connecting-IP']
    for header in ip_headers:
        ip = request.headers.get(header)
        if ip:
            if ',' in ip:
                return ip.split(',')[0].strip()
            return ip
    return request.remote_addr

def get_unique_user_id():
    ip = get_real_ip()
    user_agent = request.headers.get('User-Agent', '')
    return hashlib.md5(f"{ip}{user_agent[:50]}".encode()).hexdigest()

def generate_key():
    key_parts = []
    for _ in range(3):
        letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
        numbers = ''.join(random.choices('0123456789', k=2))
        key_parts.append(f"{letters}{numbers}")
    return '-'.join(key_parts)

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

@app.route("/linkvertise-success")
def linkvertise_success():
    user_id = get_unique_user_id()
    mark_linkvertise_completed(user_id)
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="3;url=''' + YOUR_WEBSITE + '''">
        <title>✅ Linkvertise Completed</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            body {
                background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
                color: #fff;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                text-align: center;
                padding: 20px;
            }
            
            .success-container {
                background: rgba(10, 10, 10, 0.95);
                padding: 50px 40px;
                border-radius: 20px;
                border: 2px solid #ff6600;
                max-width: 600px;
                width: 100%;
                box-shadow: 0 10px 40px rgba(255, 102, 0, 0.3);
            }
            
            .success-icon {
                font-size: 5rem;
                color: #00ff00;
                margin-bottom: 20px;
                animation: bounce 1s infinite alternate;
            }
            
            @keyframes bounce {
                0% { transform: translateY(0); }
                100% { transform: translateY(-10px); }
            }
            
            .success-title {
                font-size: 2.5rem;
                color: #ff6600;
                margin-bottom: 20px;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .success-message {
                font-size: 1.3rem;
                color: #ccc;
                margin-bottom: 30px;
                line-height: 1.6;
            }
            
            .countdown {
                font-size: 1.5rem;
                color: #ff9900;
                margin: 25px 0;
                padding: 15px;
                background: rgba(255, 153, 0, 0.1);
                border-radius: 10px;
                border: 1px solid #ff9900;
            }
            
            .redirect-button {
                display: inline-block;
                background: linear-gradient(135deg, #ff6600, #ff3300);
                color: white;
                padding: 16px 45px;
                border-radius: 12px;
                text-decoration: none;
                font-weight: bold;
                font-size: 1.2rem;
                margin-top: 20px;
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .redirect-button:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 25px rgba(255, 102, 0, 0.4);
            }
            
            .note {
                color: #888;
                font-size: 0.9rem;
                margin-top: 30px;
                font-style: italic;
            }
        </style>
        <script>
            let seconds = 3;
            function updateCountdown() {
                document.getElementById('countdown').textContent = seconds;
                seconds--;
                
                if (seconds < 0) {
                    window.location.href = "''' + YOUR_WEBSITE + '''";
                }
            }
            
            // Iniciar cuenta regresiva inmediatamente
            setInterval(updateCountdown, 1000);
            
            // Redirigir después de 3 segundos por seguridad
            setTimeout(function() {
                window.location.href = "''' + YOUR_WEBSITE + '''";
            }, 3000);
        </script>
    </head>
    <body>
        <div class="success-container">
            <div class="success-icon">✅</div>
            <h1 class="success-title">LINKVERTISE COMPLETED!</h1>
            <p class="success-message">
                Thank you for completing the verification.<br>
                You will be redirected to Genesis Hub V2 automatically.
            </p>
            <div class="countdown">
                Redirecting in <span id="countdown">3</span> seconds...
            </div>
            <a href="''' + YOUR_WEBSITE + '''" class="redirect-button">
                Click here if not redirected
            </a>
            <p class="note">
                Your key is ready to be generated on the next page.
            </p>
        </div>
    </body>
    </html>
    '''

@app.route("/check-linkvertise", methods=["GET"])
def check_linkvertise():
    user_id = get_unique_user_id()
    completed = check_linkvertise_completed(user_id)
    return jsonify({"completed": completed, "user_id": user_id})

@app.route("/generate-key", methods=["POST"])
def generate_key_endpoint():
    clean_keys()
    
    user_id = get_unique_user_id()
    ip = get_real_ip()
    
    if not check_linkvertise_completed(user_id):
        return jsonify({
            "success": False,
            "message": "Complete Linkvertise first",
            "linkvertise_url": LINKVERTISE_URL
        }), 403
    
    current_time = time.time()
    
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    # Verificar si ya tiene una clave válida
    user_has_key = False
    user_key_expires = 0
    user_key = None
    
    for key_data in data.values():
        if key_data.get("user_id") == user_id:
            user_has_key = True
            user_key_expires = key_data.get("expires", 0)
            user_key = key_data.get("key")
            break
    
    # Si tiene clave y no ha expirado, devolverla
    if user_has_key and current_time < user_key_expires:
        remaining = user_key_expires - current_time
        hours = int(remaining / 3600)
        minutes = int((remaining % 3600) / 60)
        
        return jsonify({
            "success": True,
            "key": user_key,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "expires": user_key_expires,
            "expires_at": datetime.fromtimestamp(user_key_expires).strftime('%Y-%m-%d %H:%M:%S'),
            "existing": True,
            "time_left": {
                "hours": hours,
                "minutes": minutes,
                "seconds": int(remaining % 60)
            },
            "message": f"Your existing key is still valid for {hours}h {minutes}m"
        })
    
    # Generar nueva clave
    key = generate_key()
    expires_at = current_time + COOLDOWN
    
    data[ip] = {
        "key": key,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "expires": expires_at,
        "ip": ip,
        "user_agent": request.headers.get('User-Agent', ''),
        "user_id": user_id,
        "linkvertise_completed": True,
        "used_in_roblox": False,
        "expires_at_formatted": datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    return jsonify({
        "success": True,
        "key": key,
        "created": data[ip]["created"],
        "expires": expires_at,
        "expires_at": data[ip]["expires_at_formatted"],
        "expires_in": COOLDOWN,
        "existing": False,
        "time_left": {
            "hours": 24,
            "minutes": 0,
            "seconds": 0
        },
        "message": "New key generated successfully!"
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
            expires_at = info.get("expires", 0)
            
            # Calcular tiempo restante
            time_left = expires_at - current_time
            hours_left = max(0, int(time_left / 3600))
            minutes_left = max(0, int((time_left % 3600) / 60))
            seconds_left = max(0, int(time_left % 60))
            
            return jsonify({
                "exists": True,
                "expired": expired,
                "created": info.get("created"),
                "used_in_roblox": info.get("used_in_roblox", False),
                "key": key,
                "expires_at": info.get("expires_at_formatted", ""),
                "time_left": {
                    "total_seconds": time_left,
                    "hours": hours_left,
                    "minutes": minutes_left,
                    "seconds": seconds_left
                },
                "message": "Key valid" if not expired else "Key expired"
            })
    
    return jsonify({
        "exists": False,
        "message": "Key not found"
    })

@app.route("/verify-roblox", methods=["GET"])
def verify_roblox():
    key = request.args.get('key')
    
    if not key:
        return jsonify({"success": False, "error": "No key"}), 400
    
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
                    
                    return jsonify({"success": True, "valid": True, "message": "Key verified successfully"})
                else:
                    return jsonify({"success": True, "valid": True, "message": "Key already used"})
            else:
                return jsonify({"success": False, "error": "Key expired"}), 410
    
    return jsonify({"success": False, "error": "Invalid key"}), 404

@app.route("/get-existing-key", methods=["GET"])
def get_existing_key():
    user_id = get_unique_user_id()
    ip = get_real_ip()
    
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        return jsonify({"success": False, "message": "No key found"})
    
    current_time = time.time()
    
    # Buscar clave por user_id
    for key_data in data.values():
        if key_data.get("user_id") == user_id:
            if current_time < key_data.get("expires", 0):
                # Calcular tiempo restante
                time_left = key_data.get("expires", 0) - current_time
                hours = int(time_left / 3600)
                minutes = int((time_left % 3600) / 60)
                seconds = int(time_left % 60)
                
                return jsonify({
                    "success": True,
                    "key": key_data.get("key"),
                    "expires_at": key_data.get("expires_at_formatted", ""),
                    "expired": False,
                    "time_left": {
                        "total_seconds": time_left,
                        "hours": hours,
                        "minutes": minutes,
                        "seconds": seconds
                    },
                    "message": f"Existing key found (expires in {hours}h {minutes}m)"
                })
    
    return jsonify({"success": False, "message": "No valid key found"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print("🚀 Genesis Hub V2 - Roblox Ready")
    print(f"📱 Website: {YOUR_WEBSITE}")
    print(f"🔗 Linkvertise: {LINKVERTISE_URL}")
    print(f"🌐 Server running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
