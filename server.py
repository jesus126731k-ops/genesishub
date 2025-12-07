from flask import Flask, jsonify, request, send_from_directory, redirect
from flask_cors import CORS
import os, json, time, random, string, hashlib
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='.')
CORS(app)

DATA_FILE = "keys.json"
LINKVERTISE_FILE = "linkvertise_tracking.json"
COOLDOWN = 86400  # 24 horas
SECRET = "G3N3SIS_HUB_2025"

LINKVERTISE_URL = "https://link-hub.net/1457789/3pNxakfWICZQ"
YOUR_WEBSITE = "https://genesishub-v2.onrender.com"

# Crear archivos si no existen
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
        # Verificar si la completación es reciente (últimos 7 días)
        if time.time() - data[user_id].get("timestamp", 0) < (7 * 86400):
            return data[user_id].get("completed", False)
    return False

def clean_keys():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    current_time = time.time()
    cleaned = {}
    
    for ip, info in data.items():
        # Mantener la clave si no ha expirado
        if current_time < info.get("expires", 0):
            cleaned[ip] = info
        # También mantener si el usuario_id coincide (para recuperación)
        elif info.get("user_id"):
            user_id = info.get("user_id")
            # Buscar otras claves del mismo usuario
            for other_ip, other_info in data.items():
                if other_info.get("user_id") == user_id and current_time < other_info.get("expires", 0):
                    cleaned[ip] = info
                    break
    
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
            body {background:#000;color:#fff;font-family:Arial;text-align:center;padding:100px 20px;}
            .success {color:#0f0;font-size:28px;margin:30px 0;}
            .redirect {color:#ff6600;font-size:18px;margin:20px 0;}
            .button {display:inline-block;background:#ff6600;color:white;padding:15px 30px;border-radius:10px;text-decoration:none;margin:20px 0;font-weight:bold;}
        </style>
        <script>
            setTimeout(function() {
                window.location.href = "''' + YOUR_WEBSITE + '''";
            }, 3000);
        </script>
    </head>
    <body>
        <div class="success">✅ ¡LINKVERTISE COMPLETADO!</div>
        <div class="redirect">Redirigiendo a Genesis Hub en 3 segundos...</div>
        <a href="''' + YOUR_WEBSITE + '''" class="button">Click aquí si no eres redirigido</a>
    </body>
    </html>
    '''

@app.route("/check-linkvertise", methods=["GET"])
def check_linkvertise():
    user_id = get_unique_user_id()
    completed = check_linkvertise_completed(user_id)
    
    # Si ya completó Linkvertise alguna vez, siempre retornar verdadero
    if completed:
        return jsonify({"completed": True, "permanent": True, "user_id": user_id})
    
    return jsonify({"completed": False, "permanent": False, "user_id": user_id})

@app.route("/generate-key", methods=["POST"])
def generate_key_endpoint():
    clean_keys()
    
    user_id = get_unique_user_id()
    ip = get_real_ip()
    
    # VERIFICAR SI YA TIENE LINKVERTISE COMPLETADO (PERMANENTE)
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
    
    # BUSCAR CLAVE EXISTENTE DEL USUARIO (POR USER_ID)
    existing_key = None
    existing_key_data = None
    
    for key_data in data.values():
        if key_data.get("user_id") == user_id:
            if current_time < key_data.get("expires", 0):
                existing_key = key_data.get("key")
                existing_key_data = key_data
                break
    
    # SI YA TIENE CLAVE VÁLIDA, DEVOLVER ESA MISMA
    if existing_key and existing_key_data:
        remaining = existing_key_data.get("expires", 0) - current_time
        hours = int(remaining / 3600)
        minutes = int((remaining % 3600) / 60)
        
        return jsonify({
            "success": True,
            "key": existing_key,
            "created": existing_key_data.get("created"),
            "expires": existing_key_data.get("expires"),
            "expires_at": datetime.fromtimestamp(existing_key_data.get("expires", 0)).strftime('%Y-%m-%d %H:%M:%S'),
            "existing": True,
            "time_left": {
                "hours": hours,
                "minutes": minutes,
                "seconds": int(remaining % 60),
                "total_seconds": remaining
            },
            "message": f"Your key is still valid for {hours}h {minutes}m"
        })
    
    # SI NO TIENE CLAVE O EXPIRÓ, CREAR NUEVA
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
        "roblox_uses": 0,  # Contador de usos en Roblox
        "max_roblox_uses": 999,  # Usos ilimitados por 24 horas
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
            "seconds": 0,
            "total_seconds": COOLDOWN
        },
        "message": "New key generated successfully! Valid for 24 hours."
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
            
            # Verificar usos en Roblox
            roblox_uses = info.get("roblox_uses", 0)
            max_roblox_uses = info.get("max_roblox_uses", 999)
            
            return jsonify({
                "exists": True,
                "expired": expired,
                "created": info.get("created"),
                "used_in_roblox": info.get("used_in_roblox", False),
                "roblox_uses": roblox_uses,
                "max_roblox_uses": max_roblox_uses,
                "can_use_in_roblox": roblox_uses < max_roblox_uses,
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
                # Incrementar contador de usos
                current_uses = info.get("roblox_uses", 0)
                max_uses = info.get("max_roblox_uses", 999)
                
                if current_uses < max_uses:
                    info["roblox_uses"] = current_uses + 1
                    info["used_in_roblox"] = True
                    info["last_roblox_use"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    with open(DATA_FILE, "w") as f:
                        json.dump(keys_data, f, indent=2)
                    
                    return jsonify({
                        "success": True, 
                        "valid": True, 
                        "uses_left": max_uses - (current_uses + 1),
                        "message": "Key verified successfully"
                    })
                else:
                    return jsonify({"success": False, "error": "Maximum uses reached"}), 429
            else:
                return jsonify({"success": False, "error": "Key expired"}), 410
    
    return jsonify({"success": False, "error": "Invalid key"}), 404

@app.route("/get-existing-key", methods=["GET"])
def get_existing_key():
    user_id = get_unique_user_id()
    
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
                    "message": f"Your key expires in {hours}h {minutes}m"
                })
            else:
                # Clave expirada
                return jsonify({
                    "success": False,
                    "expired": True,
                    "message": "Your key has expired"
                })
    
    return jsonify({"success": False, "message": "No key found"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print("🚀 Genesis Hub V2 - Server Started")
    print(f"📱 Website: {YOUR_WEBSITE}")
    print("✅ Linkvertise completed = Permanent access")
    print("✅ 1 Key per user = 24 hours validity")
    print("✅ Unlimited Roblox uses within 24h")
    app.run(host="0.0.0.0", port=port, debug=False)
