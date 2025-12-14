from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os, json, time, random, string, hashlib
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='.')
CORS(app)

# Archivos de datos
DATA_FILE = "keys.json"
LINKVERTISE_FILE = "linkvertise_tracking.json"
USER_KEYS_FILE = "user_keys.json"
COOLDOWN = 86400  # 24 horas en segundos
SECRET = "G3N3SIS_HUB_2025"

# URLs
LINKVERTISE_URL = "https://link-hub.net/1457789/3pNxakfWICZQ"
YOUR_WEBSITE = "https://genesishub-v2.onrender.com"

# Inicializar archivos
for file in [DATA_FILE, LINKVERTISE_FILE, USER_KEYS_FILE]:
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

def get_user_id():
    user_id_header = request.headers.get('X-User-ID')
    if user_id_header and len(user_id_header) >= 16:
        return user_id_header
    
    ip = get_real_ip()
    user_agent = request.headers.get('User-Agent', '')
    browser_info = request.headers.get('Accept-Language', '')
    
    combined = f"{ip}{user_agent[:100]}{browser_info}"
    user_id = hashlib.sha256(combined.encode()).hexdigest()[:32]
    
    return user_id

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
    
    current_time = time.time()
    expires_at = current_time + COOLDOWN  # Expira en 24 horas
    
    # ID único para esta verificación
    verification_id = f"{user_id}_{int(current_time)}"
    
    data[verification_id] = {
        "user_id": user_id,
        "completed": True,
        "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": current_time,
        "expires_at": expires_at,
        "for_key": for_key,
        "ip": get_real_ip(),
        "type": "linkvertise_verification"
    }
    
    with open(LINKVERTISE_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Linkvertise registrado para {user_id} - Expira: {datetime.fromtimestamp(expires_at).strftime('%H:%M:%S')}")
    return True

def check_linkvertise_for_user(user_id, require_active=True):
    try:
        with open(LINKVERTISE_FILE, "r") as f:
            data = json.load(f)
    except:
        return False
    
    current_time = time.time()
    
    # Buscar todas las verificaciones para este usuario
    valid_verifications = []
    
    for verification_id, verification_data in data.items():
        if verification_data.get("user_id") == user_id:
            expires_at = verification_data.get("expires_at", 0)
            
            # Si la verificación aún es válida (no ha expirado)
            if current_time < expires_at:
                valid_verifications.append({
                    "id": verification_id,
                    "timestamp": verification_data.get("timestamp", 0),
                    "expires_at": expires_at,
                    "for_key": verification_data.get("for_key")
                })
    
    # Ordenar por fecha (más reciente primero)
    valid_verifications.sort(key=lambda x: x["timestamp"], reverse=True)
    
    if valid_verifications:
        latest = valid_verifications[0]
        hours_left = (latest["expires_at"] - current_time) / 3600
        print(f"✅ Usuario {user_id} tiene Linkvertise válido por {hours_left:.1f} horas")
        return True
    
    print(f"❌ Usuario {user_id} NO tiene Linkvertise válido")
    return False

def get_user_active_key(user_id):
    try:
        with open(USER_KEYS_FILE, "r") as f:
            user_keys = json.load(f)
    except:
        user_keys = {}
    
    if user_id in user_keys:
        key_data = user_keys[user_id]
        current_time = time.time()
        
        if current_time < key_data.get("expires", 0):
            return key_data
    
    return None

def save_user_key(user_id, key_data):
    try:
        with open(USER_KEYS_FILE, "r") as f:
            user_keys = json.load(f)
    except:
        user_keys = {}
    
    user_keys[user_id] = key_data
    
    with open(USER_KEYS_FILE, "w") as f:
        json.dump(user_keys, f, indent=2)
    
    save_key_to_global(key_data)
    return True

def save_key_to_global(key_data):
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    key = key_data.get("key")
    if key:
        data[key] = key_data
    
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    return True

def clean_expired_data():
    current_time = time.time()
    
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
    
    try:
        with open(USER_KEYS_FILE, "r") as f:
            user_keys_data = json.load(f)
    except:
        user_keys_data = {}
    
    # Limpiar keys expiradas
    cleaned_keys = {}
    expired_keys = []
    for key, key_info in keys_data.items():
        if current_time < key_info.get("expires", 0):
            cleaned_keys[key] = key_info
        else:
            expired_keys.append(key)
    
    # Limpiar verificaciones Linkvertise expiradas
    cleaned_linkvertise = {}
    expired_verifications = []
    for verification_id, verification_data in linkvertise_data.items():
        expires_at = verification_data.get("expires_at", 0)
        if current_time < expires_at:
            cleaned_linkvertise[verification_id] = verification_data
        else:
            expired_verifications.append(verification_id)
    
    # Limpiar user keys expiradas
    cleaned_user_keys = {}
    expired_users = []
    for user_id, key_data in user_keys_data.items():
        if current_time < key_data.get("expires", 0):
            cleaned_user_keys[user_id] = key_data
        else:
            expired_users.append(user_id)
    
    # Guardar datos limpios
    with open(DATA_FILE, "w") as f:
        json.dump(cleaned_keys, f, indent=2)
    
    with open(LINKVERTISE_FILE, "w") as f:
        json.dump(cleaned_linkvertise, f, indent=2)
    
    with open(USER_KEYS_FILE, "w") as f:
        json.dump(cleaned_user_keys, f, indent=2)
    
    print(f"🧹 Limpieza: {len(expired_keys)} keys, {len(expired_verifications)} verificaciones, {len(expired_users)} usuarios")
    return len(cleaned_keys), len(cleaned_linkvertise), len(cleaned_user_keys)

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)

@app.route("/linkvertise-success")
def linkvertise_success():
    user_id = get_user_id()
    
    print(f"🎯 Linkvertise COMPLETADO por: {user_id}")
    
    # Marcar como completado
    mark_linkvertise_completed(user_id)
    
    # Pequeña espera para asegurar guardado
    time.sleep(0.5)
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="4;url={YOUR_WEBSITE}">
        <title>✅ Verification Completed</title>
        <style>
            body {{
                background: #000;
                color: #fff;
                font-family: Arial, sans-serif;
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
            .info {{
                color: #aaa;
                font-size: 14px;
                margin-top: 30px;
            }}
        </style>
        <script>
            setTimeout(function() {{
                window.location.href = "{YOUR_WEBSITE}";
            }}, 4000);
        </script>
    </head>
    <body>
        <div class="success">✅ VERIFICATION COMPLETED!</div>
        <div class="redirect">Redirecting to Genesis Hub in 4 seconds...</div>
        <a href="{YOUR_WEBSITE}" class="button">Click here if not redirected</a>
        <div class="info">Verification valid for 24 hours</div>
    </body>
    </html>
    '''

@app.route("/check-user-status", methods=["GET"])
def check_user_status():
    clean_expired_data()
    
    user_id = get_user_id()
    current_time = time.time()
    
    print(f"👤 Verificando estado usuario: {user_id}")
    
    # 1. Verificar si tiene key activa
    active_key = get_user_active_key(user_id)
    
    if active_key:
        remaining = active_key.get("expires", 0) - current_time
        
        if remaining > 0:
            print(f"🔑 Key activa encontrada: {active_key.get('key')} ({int(remaining/3600)}h restantes)")
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
                "message": f"Active key: {int(remaining/3600)}h {int((remaining%3600)/60)}m remaining"
            })
    
    # 2. Verificar Linkvertise
    has_linkvertise = check_linkvertise_for_user(user_id)
    
    if has_linkvertise:
        print(f"✅ Usuario puede generar nueva key (Linkvertise válido)")
        return jsonify({
            "success": True,
            "has_active_key": False,
            "requires_linkvertise": False,
            "can_generate_key": True,
            "message": "Verification completed. Ready to generate key."
        })
    else:
        print(f"⚠️ Usuario necesita Linkvertise")
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
    
    user_id = get_user_id()
    ip = get_real_ip()
    current_time = time.time()
    
    print(f"🔑 Solicitud generar key para: {user_id}")
    
    # Verificar si ya tiene key activa
    active_key = get_user_active_key(user_id)
    if active_key and current_time < active_key.get("expires", 0):
        remaining = active_key.get("expires", 0) - current_time
        hours = int(remaining / 3600)
        minutes = int((remaining % 3600) / 60)
        
        print(f"⚠️ Usuario ya tiene key activa")
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
            "message": f"Active key available for {hours}h {minutes}m"
        })
    
    # Verificar Linkvertise
    has_linkvertise = check_linkvertise_for_user(user_id)
    
    if not has_linkvertise:
        print(f"❌ Usuario no completó Linkvertise")
        return jsonify({
            "success": False,
            "requires_linkvertise": True,
            "message": "Complete verification first",
            "linkvertise_url": LINKVERTISE_URL
        }), 403
    
    # Generar nueva key
    key = generate_key()
    expires_at = current_time + COOLDOWN
    
    print(f"✅ Generando nueva key: {key}")
    
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
        "linkvertise_completed": True,
        "linkvertise_timestamp": current_time
    }
    
    # Guardar key
    save_user_key(user_id, key_data)
    
    # Marcar Linkvertise para esta key específica
    mark_linkvertise_completed(user_id, key)
    
    print(f"💾 Key guardada exitosamente para {user_id}")
    
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
    
    print(f"🔍 Verificando key: {key}")
    
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        return jsonify({"error": "DB error"}), 500
    
    current_time = time.time()
    
    # Buscar key (case-insensitive)
    normalized_input = key.upper()
    stored_key = None
    
    for stored_key_name in data.keys():
        if stored_key_name.upper() == normalized_input:
            stored_key = stored_key_name
            break
    
    if stored_key:
        info = data[stored_key]
        expires_at = info.get("expires", 0)
        expired = current_time >= expires_at
        
        if expired:
            print(f"⏰ Key expirada: {stored_key}")
            return jsonify({
                "exists": True,
                "expired": True,
                "message": "Key expired (24h)",
                "key": stored_key
            })
        
        time_left = expires_at - current_time
        hours_left = int(time_left / 3600)
        minutes_left = int((time_left % 3600) / 60)
        seconds_left = int(time_left % 60)
        
        print(f"✅ Key válida: {stored_key} ({hours_left}h {minutes_left}m restantes)")
        
        # Verificar Linkvertise para el usuario de esta key
        user_id = info.get("user_id")
        has_linkvertise = check_linkvertise_for_user(user_id)
        
        if not has_linkvertise:
            print(f"⚠️ Key sin Linkvertise válido")
            return jsonify({
                "exists": True,
                "expired": False,
                "invalid_linkvertise": True,
                "message": "Key requires verification",
                "key": stored_key
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
            "key": stored_key,
            "expires_at": info.get("expires_at_formatted", ""),
            "time_left": {
                "total_seconds": time_left,
                "hours": hours_left,
                "minutes": minutes_left,
                "seconds": seconds_left
            },
            "message": "Key valid"
        })
    
    print(f"❌ Key no encontrada: {key}")
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
    
    print(f"🎮 Verificación Roblox para key: {key}")
    
    try:
        with open(DATA_FILE, "r") as f:
            keys_data = json.load(f)
    except:
        return jsonify({"success": False, "error": "DB error"}), 500
    
    current_time = time.time()
    
    # Buscar key
    normalized_input = key.upper()
    actual_key = None
    
    for stored_key in keys_data.keys():
        if stored_key.upper() == normalized_input:
            actual_key = stored_key
            break
    
    if actual_key and actual_key in keys_data:
        info = keys_data[actual_key]
        expires_at = info.get("expires", 0)
        
        if current_time < expires_at:
            user_id = info.get("user_id")
            
            # Verificar Linkvertise
            if not check_linkvertise_for_user(user_id):
                print(f"❌ Verificación Roblox fallida: Linkvertise no válido")
                return jsonify({"success": False, "error": "Verification required"}), 403
            
            # Registrar uso
            current_uses = info.get("roblox_uses", 0)
            info["roblox_uses"] = current_uses + 1
            info["used_in_roblox"] = True
            info["last_roblox_use"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            with open(DATA_FILE, "w") as f:
                json.dump(keys_data, f, indent=2)
            
            print(f"✅ Verificación Roblox exitosa, usos: {current_uses + 1}")
            
            return jsonify({
                "success": True, 
                "valid": True, 
                "uses_left": 99999 - (current_uses + 1),
                "message": "Key verified successfully"
            })
        else:
            print(f"❌ Key expirada: {actual_key}")
            return jsonify({"success": False, "error": "Key expired"}), 410
    
    print(f"❌ Key inválida: {key}")
    return jsonify({"success": False, "error": "Invalid key"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print("=" * 60)
    print("🚀 GENESIS HUB V2 - SISTEMA DEFINITIVO")
    print("=" * 60)
    print("📋 REGLAS DEL SISTEMA:")
    print("   1. 1 Linkvertise = 1 Key (24 horas)")
    print("   2. Key expira = Linkvertise expira")
    print("   3. Nueva key requiere nuevo Linkvertise")
    print("   4. 1 usuario = 1 key activa simultánea")
    print("   5. Roblox: Usos ilimitados con key activa")
    print("=" * 60)
    print(f"🌐 URL: {YOUR_WEBSITE}")
    print(f"🔗 Linkvertise: {LINKVERTISE_URL}")
    print(f"🔧 Puerto: {port}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=False)
