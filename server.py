from flask import Flask, jsonify, request, send_from_directory, redirect
from flask_cors import CORS
import os, json, time, random, string, hashlib
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='.')
CORS(app)

# ARCHIVOS DE DATOS
DATA_FILE = "keys.json"
LINKVERTISE_FILE = "linkvertise_tracking.json"
COOLDOWN = 86400  # 24 horas en segundos
SECRET = "G3N3SIS_HUB_2025"

LINKVERTISE_URL = "https://link-hub.net/1457789/3pNxakfWICZQ"
YOUR_WEBSITE = "https://genesishub-v2.onrender.com"

# Crear archivos si no existen
for file in [DATA_FILE, LINKVERTISE_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
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

def mark_linkvertise_completed(user_id, for_key=None):
    try:
        with open(LINKVERTISE_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    linkvertise_id = f"{user_id}_{for_key}" if for_key else user_id
    
    data[linkvertise_id] = {
        "completed": True,
        "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": time.time(),
        "user_id": user_id,
        "for_key": for_key,
        "ip": get_real_ip()
    }
    
    with open(LINKVERTISE_FILE, "w") as f:
        json.dump(data, f, indent=2)
    return True

def check_linkvertise_for_user_key(user_id, key=None):
    try:
        with open(LINKVERTISE_FILE, "r") as f:
            data = json.load(f)
    except:
        return False
    
    # Buscar Linkvertise para esta key específica
    if key:
        linkvertise_id = f"{user_id}_{key}"
        if linkvertise_id in data:
            linkvertise_data = data[linkvertise_id]
            # Linkvertise es válido por 24h (misma duración que la key)
            if time.time() - linkvertise_data.get("timestamp", 0) < COOLDOWN:
                return linkvertise_data.get("completed", False)
    
    # Buscar Linkvertise general del usuario (para backward compatibility)
    if user_id in data:
        user_data = data[user_id]
        if time.time() - user_data.get("timestamp", 0) < COOLDOWN:
            return user_data.get("completed", False)
    
    return False

def get_user_active_key(user_id):
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        return None
    
    current_time = time.time()
    
    # Buscar todas las keys del usuario
    user_keys = []
    for key_data in data.values():
        if key_data.get("user_id") == user_id:
            user_keys.append(key_data)
    
    # Ordenar por fecha de creación (más reciente primero)
    user_keys.sort(key=lambda x: x.get("created", ""), reverse=True)
    
    # Encontrar key activa (no expirada)
    for key_data in user_keys:
        if current_time < key_data.get("expires", 0):
            return key_data
    
    return None

def save_key(key_data):
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    # Usar IP como clave principal
    ip = key_data.get("ip") or get_real_ip()
    data[ip] = key_data
    
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    return True

def clean_expired_data():
    try:
        with open(DATA_FILE, "r") as f:
            keys_data = json.load(f)
    except:
        keys_data = {}
    
    try:
        with open(LINKVERTISE_FILE, "r") as f:
            linkvertise_data = json.load(f)
    except:
        linkvertise_data = {}
    
    current_time = time.time()
    
    # Limpiar keys expiradas
    cleaned_keys = {}
    for ip, key_info in keys_data.items():
        if current_time < key_info.get("expires", 0):
            cleaned_keys[ip] = key_info
    
    # Limpiar Linkvertise expirados (más de 24h)
    cleaned_linkvertise = {}
    for link_id, link_info in linkvertise_data.items():
        if current_time - link_info.get("timestamp", 0) < COOLDOWN:
            cleaned_linkvertise[link_id] = link_info
    
    # Guardar datos limpios
    with open(DATA_FILE, "w") as f:
        json.dump(cleaned_keys, f, indent=2)
    
    with open(LINKVERTISE_FILE, "w") as f:
        json.dump(cleaned_linkvertise, f, indent=2)
    
    expired_keys = len(keys_data) - len(cleaned_keys)
    expired_links = len(linkvertise_data) - len(cleaned_linkvertise)
    
    return expired_keys, expired_links

# ========== RUTAS DEL SERVIDOR ==========

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)

@app.route("/linkvertise-success")
def linkvertise_success():
    user_id = get_unique_user_id()
    
    # Obtener key si ya existe una pendiente
    try:
        with open(DATA_FILE, "r") as f:
            keys_data = json.load(f)
    except:
        keys_data = {}
    
    pending_key = None
    for key_data in keys_data.values():
        if key_data.get("user_id") == user_id and key_data.get("pending_linkvertise", False):
            pending_key = key_data.get("key")
            break
    
    # Marcar Linkvertise completado PARA ESTA KEY
    mark_linkvertise_completed(user_id, pending_key)
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="3;url={YOUR_WEBSITE}">
        <title>✅ Verification Completed</title>
        <style>
            body {{
                background: #000;
                color: #fff;
                font-family: Arial;
                text-align: center;
                padding: 100px 20px;
            }}
            .success {{
                color: #0f0;
                font-size: 28px;
                margin: 30px 0;
            }}
            .redirect {{
                color: #ff6600;
                font-size: 18px;
                margin: 20px 0;
            }}
            .button {{
                display: inline-block;
                background: #ff6600;
                color: white;
                padding: 15px 30px;
                border-radius: 10px;
                text-decoration: none;
                margin: 20px 0;
                font-weight: bold;
            }}
        </style>
        <script>
            setTimeout(function() {{
                window.location.href = "{YOUR_WEBSITE}";
            }}, 3000);
        </script>
    </head>
    <body>
        <div class="success">✅ VERIFICATION COMPLETED!</div>
        <div class="redirect">Redirecting to Genesis Hub in 3 seconds...</div>
        <a href="{YOUR_WEBSITE}" class="button">Click here if not redirected</a>
    </body>
    </html>
    '''

@app.route("/check-user-status", methods=["GET"])
def check_user_status():
    clean_expired_data()
    
    user_id = get_unique_user_id()
    current_time = time.time()
    
    # 1. Verificar si tiene key activa
    active_key = get_user_active_key(user_id)
    
    if active_key:
        # Tiene key activa
        remaining = active_key.get("expires", 0) - current_time
        
        if remaining > 0:
            return jsonify({
                "success": True,
                "has_active_key": True,
                "requires_linkvertise": False,
                "key": active_key.get("key"),
                "expires_at": active_key.get("expires_at_formatted", ""),
                "time_left": {
                    "total_seconds": remaining,
                    "hours": int(remaining / 3600),
                    "minutes": int((remaining % 3600) / 60),
                    "seconds": int(remaining % 60)
                },
                "message": f"You have an active key for {int(remaining/3600)}h {int((remaining%3600)/60)}m"
            })
    
    # 2. No tiene key activa o expiró
    # Verificar si ya completó Linkvertise recientemente
    has_recent_linkvertise = False
    try:
        with open(LINKVERTISE_FILE, "r") as f:
            linkvertise_data = json.load(f)
    except:
        linkvertise_data = {}
    
    # Buscar Linkvertise del usuario en las últimas 24h
    for link_id, link_info in linkvertise_data.items():
        if link_info.get("user_id") == user_id:
            if current_time - link_info.get("timestamp", 0) < 300:  # 5 minutos de gracia
                has_recent_linkvertise = True
                break
    
    if has_recent_linkvertise:
        # Acaba de completar Linkvertise, puede generar key
        return jsonify({
            "success": True,
            "has_active_key": False,
            "requires_linkvertise": False,
            "can_generate_key": True,
            "message": "Verification completed. Ready to generate key."
        })
    else:
        # Necesita Linkvertise
        return jsonify({
            "success": True,
            "has_active_key": False,
            "requires_linkvertise": True,
            "can_generate_key": False,
            "message": "Verification required for new key"
        })

@app.route("/generate-key", methods=["POST"])
def generate_key_endpoint():
    clean_expired_data()
    
    user_id = get_unique_user_id()
    ip = get_real_ip()
    current_time = time.time()
    
    # 1. Verificar si ya tiene key activa
    active_key = get_user_active_key(user_id)
    if active_key and current_time < active_key.get("expires", 0):
        remaining = active_key.get("expires", 0) - current_time
        hours = int(remaining / 3600)
        minutes = int((remaining % 3600) / 60)
        
        return jsonify({
            "success": True,
            "key": active_key.get("key"),
            "created": active_key.get("created"),
            "expires": active_key.get("expires"),
            "expires_at": active_key.get("expires_at_formatted", ""),
            "existing": True,
            "time_left": {
                "hours": hours,
                "minutes": minutes,
                "seconds": int(remaining % 60),
                "total_seconds": remaining
            },
            "message": f"You already have an active key for {hours}h {minutes}m"
        })
    
    # 2. Verificar si completó Linkvertise recientemente (últimos 5 minutos)
    has_valid_linkvertise = False
    try:
        with open(LINKVERTISE_FILE, "r") as f:
            linkvertise_data = json.load(f)
    except:
        linkvertise_data = {}
    
    for link_id, link_info in linkvertise_data.items():
        if link_info.get("user_id") == user_id:
            if current_time - link_info.get("timestamp", 0) < 300:  # 5 minutos
                has_valid_linkvertise = True
                break
    
    if not has_valid_linkvertise:
        return jsonify({
            "success": False,
            "requires_linkvertise": True,
            "message": "Complete verification first",
            "linkvertise_url": LINKVERTISE_URL
        }), 403
    
    # 3. Generar NUEVA key
    key = generate_key()
    expires_at = current_time + COOLDOWN
    
    key_data = {
        "key": key,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "expires": expires_at,
        "ip": ip,
        "user_agent": request.headers.get('User-Agent', ''),
        "user_id": user_id,
        "used_in_roblox": False,
        "roblox_uses": 0,
        "max_roblox_uses": 99999,
        "expires_at_formatted": datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S'),
        "linkvertise_completed": True
    }
    
    save_key(key_data)
    
    # Marcar Linkvertise como usado para ESTA key
    mark_linkvertise_completed(user_id, key)
    
    return jsonify({
        "success": True,
        "key": key,
        "created": key_data["created"],
        "expires": expires_at,
        "expires_at": key_data["expires_at_formatted"],
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
    clean_expired_data()
    
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
            
            if expired:
                return jsonify({
                    "exists": True,
                    "expired": True,
                    "message": "Key expired (24h)",
                    "key": key
                })
            
            # Key válida
            time_left = expires_at - current_time
            hours_left = int(time_left / 3600)
            minutes_left = int((time_left % 3600) / 60)
            seconds_left = int(time_left % 60)
            
            # Verificar Linkvertise para esta key
            user_id = info.get("user_id")
            has_linkvertise = check_linkvertise_for_user_key(user_id, key)
            
            if not has_linkvertise:
                return jsonify({
                    "exists": True,
                    "expired": False,
                    "invalid_linkvertise": True,
                    "message": "Key requires verification",
                    "key": key
                })
            
            roblox_uses = info.get("roblox_uses", 0)
            max_roblox_uses = info.get("max_roblox_uses", 99999)
            
            return jsonify({
                "exists": True,
                "expired": False,
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
                "message": "Key valid"
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
    
    clean_expired_data()
    
    try:
        with open(DATA_FILE, "r") as f:
            keys_data = json.load(f)
    except:
        return jsonify({"success": False, "error": "DB error"}), 500
    
    current_time = time.time()
    
    for ip, info in keys_data.items():
        if info.get("key") == key:
            if current_time < info.get("expires", 0):
                # Verificar Linkvertise
                user_id = info.get("user_id")
                if not check_linkvertise_for_user_key(user_id, key):
                    return jsonify({"success": False, "error": "Verification required"}), 403
                
                # Incrementar usos
                current_uses = info.get("roblox_uses", 0)
                info["roblox_uses"] = current_uses + 1
                info["used_in_roblox"] = True
                info["last_roblox_use"] = time.strftime("%Y-%m-%d %H:%M:%S")
                
                with open(DATA_FILE, "w") as f:
                    json.dump(keys_data, f, indent=2)
                
                return jsonify({
                    "success": True, 
                    "valid": True, 
                    "uses_left": 99999 - (current_uses + 1),
                    "message": "Key verified successfully"
                })
            else:
                return jsonify({"success": False, "error": "Key expired"}), 410
    
    return jsonify({"success": False, "error": "Invalid key"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print("🚀 Genesis Hub V2 - Sistema Definitivo")
    print("📌 REGLAS:")
    print("   1. 1 Linkvertise = 1 Key (24h)")
    print("   2. Key expira = Nuevo Linkvertise obligatorio")
    print("   3. 1 Key activa por usuario")
    print("   4. Roblox: Usos ilimitados mientras key esté activa")
    print(f"🌐 URL: {YOUR_WEBSITE}")
    print(f"🔗 Linkvertise: {LINKVERTISE_URL}")
    app.run(host="0.0.0.0", port=port, debug=False)
