from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os, json, time, random, string, hashlib
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='.')
CORS(app)

# Archivos de datos
KEYS_FILE = "keys.json"
LINKVERTISE_FILE = "linkvertise.json"
COOLDOWN = 86400  # 24 horas

LINKVERTISE_URL = "https://link-hub.net/1457789/3pNxakfWICZQ"
YOUR_WEBSITE = "https://genesishub-v2.onrender.com"

# Inicializar archivos
for file in [KEYS_FILE, LINKVERTISE_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)

def get_user_id():
    """Obtiene ID único del usuario"""
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    combined = f"{ip}{user_agent}"
    return hashlib.md5(combined.encode()).hexdigest()

def generate_key():
    """Genera una nueva key"""
    key_parts = []
    for _ in range(3):
        letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
        numbers = ''.join(random.choices('0123456789', k=2))
        key_parts.append(f"{letters}{numbers}")
    return '-'.join(key_parts)

def save_linkvertise_verification(user_id):
    """Guarda que el usuario completó Linkvertise"""
    try:
        with open(LINKVERTISE_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    current_time = time.time()
    
    # Guardar verificación
    data[user_id] = {
        "verified": True,
        "timestamp": current_time,
        "expires_at": current_time + COOLDOWN,
        "verified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(LINKVERTISE_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ LINKVERTISE VERIFICADO para usuario: {user_id}")
    return True

def check_linkvertise_verification(user_id):
    """Verifica si el usuario tiene Linkvertise válido"""
    try:
        with open(LINKVERTISE_FILE, "r") as f:
            data = json.load(f)
    except:
        return False
    
    if user_id in data:
        verification = data[user_id]
        current_time = time.time()
        
        if current_time < verification.get("expires_at", 0):
            return True
    
    return False

def save_key(user_id, key_data):
    """Guarda una key"""
    try:
        with open(KEYS_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    # Eliminar keys viejas del mismo usuario
    keys_to_delete = []
    for key, info in data.items():
        if info.get("user_id") == user_id:
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        del data[key]
    
    # Guardar nueva key
    data[key_data["key"]] = key_data
    
    with open(KEYS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    return True

def get_user_key(user_id):
    """Obtiene la key activa del usuario"""
    try:
        with open(KEYS_FILE, "r") as f:
            data = json.load(f)
    except:
        return None
    
    current_time = time.time()
    
    for key, info in data.items():
        if info.get("user_id") == user_id:
            if current_time < info.get("expires_at", 0):
                return info
    
    return None

def clean_expired_data():
    """Limpia datos expirados"""
    current_time = time.time()
    
    # Limpiar keys expiradas
    try:
        with open(KEYS_FILE, "r") as f:
            keys_data = json.load(f)
    except:
        keys_data = {}
    
    cleaned_keys = {}
    for key, info in keys_data.items():
        if current_time < info.get("expires_at", 0):
            cleaned_keys[key] = info
    
    with open(KEYS_FILE, "w") as f:
        json.dump(cleaned_keys, f, indent=2)
    
    # Limpiar verificaciones expiradas
    try:
        with open(LINKVERTISE_FILE, "r") as f:
            linkvertise_data = json.load(f)
    except:
        linkvertise_data = {}
    
    cleaned_linkvertise = {}
    for user_id, verification in linkvertise_data.items():
        if current_time < verification.get("expires_at", 0):
            cleaned_linkvertise[user_id] = verification
    
    with open(LINKVERTISE_FILE, "w") as f:
        json.dump(cleaned_linkvertise, f, indent=2)
    
    return True

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)

@app.route("/linkvertise-success")
def linkvertise_success():
    """Página a la que redirige Linkvertise después de verificación"""
    user_id = get_user_id()
    
    print(f"🔗 Usuario regresa de Linkvertise: {user_id}")
    
    # GUARDAR que completó Linkvertise
    save_linkvertise_verification(user_id)
    
    return f'''
    <html>
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="2;url={YOUR_WEBSITE}">
        <title>✅ Verificación Completada</title>
        <style>
            body {{ background: #000; color: #fff; font-family: Arial; text-align: center; padding: 100px 20px; }}
            .success {{ color: #0f0; font-size: 24px; margin: 20px 0; }}
            .redirect {{ color: #ff6600; font-size: 16px; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="success">✅ ¡VERIFICACIÓN COMPLETADA!</div>
        <div class="redirect">Redirigiendo a Genesis Hub...</div>
        <script>
            setTimeout(function() {{
                window.location.href = "{YOUR_WEBSITE}";
            }}, 2000);
        </script>
    </body>
    </html>
    '''

@app.route("/check-user-status", methods=["GET"])
def check_user_status():
    """Verifica el estado del usuario"""
    clean_expired_data()
    
    user_id = get_user_id()
    current_time = time.time()
    
    print(f"👤 Verificando usuario: {user_id}")
    
    # 1. Verificar si tiene key activa
    user_key = get_user_key(user_id)
    
    if user_key:
        remaining = user_key.get("expires_at", 0) - current_time
        
        if remaining > 0:
            return jsonify({
                "success": True,
                "has_active_key": True,
                "requires_linkvertise": False,
                "key": user_key.get("key"),
                "expires_at": user_key.get("expires_at_formatted"),
                "time_left": {
                    "total_seconds": remaining,
                    "hours": int(remaining / 3600),
                    "minutes": int((remaining % 3600) / 60),
                    "seconds": int(remaining % 60)
                },
                "message": "Tienes una key activa"
            })
    
    # 2. Verificar si tiene Linkvertise válido
    has_linkvertise = check_linkvertise_verification(user_id)
    
    if has_linkvertise:
        print(f"✅ Usuario tiene Linkvertise válido")
        return jsonify({
            "success": True,
            "has_active_key": False,
            "requires_linkvertise": False,
            "can_generate_key": True,
            "message": "Puedes generar una nueva key"
        })
    else:
        print(f"⚠️ Usuario necesita Linkvertise")
        return jsonify({
            "success": True,
            "has_active_key": False,
            "requires_linkvertise": True,
            "can_generate_key": False,
            "message": "Necesitas verificar primero"
        })

@app.route("/generate-key", methods=["POST"])
def generate_key_endpoint():
    """Genera una nueva key"""
    clean_expired_data()
    
    user_id = get_user_id()
    current_time = time.time()
    
    print(f"🔑 Usuario quiere generar key: {user_id}")
    
    # 1. Verificar Linkvertise
    has_linkvertise = check_linkvertise_verification(user_id)
    
    if not has_linkvertise:
        print(f"❌ Usuario no tiene Linkvertise")
        return jsonify({
            "success": False,
            "requires_linkvertise": True,
            "message": "Completa la verificación primero",
            "linkvertise_url": LINKVERTISE_URL
        }), 403
    
    # 2. Generar nueva key
    key = generate_key()
    expires_at = current_time + COOLDOWN
    
    key_data = {
        "key": key,
        "user_id": user_id,
        "created_at": current_time,
        "expires_at": expires_at,
        "expires_at_formatted": datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d %H:%M:%S"),
        "used_in_roblox": False,
        "roblox_uses": 0
    }
    
    # 3. Guardar key
    save_key(user_id, key_data)
    
    print(f"✅ Key generada: {key}")
    
    return jsonify({
        "success": True,
        "key": key,
        "expires_at": key_data["expires_at_formatted"],
        "time_left": {
            "hours": 24,
            "minutes": 0,
            "seconds": 0,
            "total_seconds": COOLDOWN
        },
        "message": "¡Key generada exitosamente! Válida por 24 horas."
    })

@app.route("/check-key/<key>", methods=["GET"])
def check_key(key):
    """Verifica si una key es válida"""
    clean_expired_data()
    
    try:
        with open(KEYS_FILE, "r") as f:
            keys_data = json.load(f)
    except:
        return jsonify({"error": "Error en base de datos"}), 500
    
    current_time = time.time()
    
    # Buscar key (case-insensitive)
    key_upper = key.upper()
    found_key = None
    
    for stored_key in keys_data.keys():
        if stored_key.upper() == key_upper:
            found_key = stored_key
            break
    
    if found_key and found_key in keys_data:
        key_info = keys_data[found_key]
        expires_at = key_info.get("expires_at", 0)
        
        if current_time >= expires_at:
            return jsonify({
                "exists": True,
                "expired": True,
                "message": "Key expirada"
            })
        
        # Verificar que el usuario tenga Linkvertise válido
        user_id = key_info.get("user_id")
        has_linkvertise = check_linkvertise_verification(user_id)
        
        if not has_linkvertise:
            return jsonify({
                "exists": True,
                "expired": False,
                "invalid_linkvertise": True,
                "message": "Key requiere verificación"
            })
        
        time_left = expires_at - current_time
        
        return jsonify({
            "exists": True,
            "expired": False,
            "key": found_key,
            "expires_at": key_info.get("expires_at_formatted"),
            "time_left": {
                "total_seconds": time_left,
                "hours": int(time_left / 3600),
                "minutes": int((time_left % 3600) / 60),
                "seconds": int(time_left % 60)
            },
            "can_use_in_roblox": True,
            "message": "Key válida"
        })
    
    return jsonify({
        "exists": False,
        "message": "Key no encontrada"
    })

@app.route("/verify-roblox", methods=["GET"])
def verify_roblox():
    """Verifica key para Roblox"""
    key = request.args.get('key')
    
    if not key:
        return jsonify({"success": False, "error": "No key provided"}), 400
    
    clean_expired_data()
    
    try:
        with open(KEYS_FILE, "r") as f:
            keys_data = json.load(f)
    except:
        return jsonify({"success": False, "error": "DB error"}), 500
    
    current_time = time.time()
    
    # Buscar key
    key_upper = key.upper()
    found_key = None
    
    for stored_key in keys_data.keys():
        if stored_key.upper() == key_upper:
            found_key = stored_key
            break
    
    if found_key and found_key in keys_data:
        key_info = keys_data[found_key]
        
        if current_time < key_info.get("expires_at", 0):
            # Verificar Linkvertise
            user_id = key_info.get("user_id")
            if not check_linkvertise_verification(user_id):
                return jsonify({"success": False, "error": "Verification required"}), 403
            
            # Actualizar usos
            key_info["used_in_roblox"] = True
            key_info["roblox_uses"] = key_info.get("roblox_uses", 0) + 1
            key_info["last_roblox_use"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(KEYS_FILE, "w") as f:
                json.dump(keys_data, f, indent=2)
            
            return jsonify({
                "success": True,
                "valid": True,
                "message": "Key verificada exitosamente"
            })
        else:
            return jsonify({"success": False, "error": "Key expired"}), 410
    
    return jsonify({"success": False, "error": "Invalid key"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print("=" * 60)
    print("🚀 GENESIS HUB V2 - SISTEMA DEFINITIVO")
    print("=" * 60)
    print("📋 SISTEMA GARANTIZADO:")
    print("   1. Linkvertise se GUARDA por 24 horas")
    print("   2. 1 Linkvertise = 1 Key (24h)")
    print("   3. Key expira = Nuevo Linkvertise")
    print("   4. Keys funcionan con mayúsculas/minúsculas")
    print("=" * 60)
    print(f"🌐 URL: {YOUR_WEBSITE}")
    print(f"🔗 Linkvertise: {LINKVERTISE_URL}")
    print(f"🔧 Puerto: {port}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=False)
