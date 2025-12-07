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

# ========== FUNCIONES MEJORADAS PARA ROBLOX ==========
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
    """Genera key de 15 caracteres que ROBLOX PUEDE VERIFICAR"""
    key_parts = []
    for _ in range(3):
        # 3 letras + 2 números = 5 caracteres por segmento
        letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
        numbers = ''.join(random.choices('0123456789', k=2))
        key_parts.append(f"{letters}{numbers}")
    
    key = '-'.join(key_parts)
    
    # Verificar que NO exista ya
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

def mark_linkvertise_completed(user_id):
    try:
        with open(LINKVERTISE_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    data[user_id] = {
        "completed": True,
        "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": time.time(),
        "expires_at": time.time() + 86400  # 24 horas
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
        user_data = data[user_id]
        current_time = time.time()
        
        # Verificar si está completado y no ha expirado (24h)
        if user_data.get("completed") and current_time < user_data.get("expires_at", 0):
            return True
    
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

# ========== RUTAS PRINCIPALES ==========
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)

# ========== PÁGINA DE LINKVERTISE (DISEÑO RESTAURADO) ==========
@app.route("/linkvertise")
@app.route("/linkvertise/")
@app.route("/linkvertise-success")
@app.route("/linkvertise-success/")
def handle_linkvertise():
    user_id = get_unique_user_id()
    mark_linkvertise_completed(user_id)
    
    html_content = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>✅ Linkvertise Completed - Genesis Hub V2</title>
        <style>
            body {{
                background: #000;
                color: #fff;
                font-family: 'Segoe UI', Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                padding: 20px;
                text-align: center;
            }}
            
            .container {{
                background: #1a1a1a;
                padding: 40px;
                border-radius: 15px;
                border: 2px solid #00ff00;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 10px 30px rgba(0, 255, 0, 0.2);
            }}
            
            .success {{
                color: #00ff00;
                font-size: 28px;
                margin-bottom: 20px;
                font-weight: bold;
            }}
            
            .message {{
                color: #ccc;
                font-size: 18px;
                margin: 20px 0;
                line-height: 1.5;
            }}
            
            .countdown {{
                color: #ff6600;
                font-size: 20px;
                margin: 30px 0;
                font-weight: bold;
            }}
            
            .button {{
                display: inline-block;
                background: linear-gradient(135deg, #ff6600, #ff3300);
                color: white;
                padding: 15px 30px;
                border-radius: 10px;
                text-decoration: none;
                font-weight: bold;
                font-size: 18px;
                margin-top: 20px;
                transition: all 0.3s ease;
            }}
            
            .button:hover {{
                transform: translateY(-3px);
                box-shadow: 0 10px 20px rgba(255, 102, 0, 0.4);
            }}
            
            .note {{
                color: #888;
                font-size: 14px;
                margin-top: 30px;
                font-style: italic;
            }}
        </style>
        <script>
            let seconds = 5;
            const countdownElement = document.getElementById('countdown');
            
            function updateCountdown() {{
                countdownElement.textContent = 'Redirigiendo en ' + seconds + ' segundos...';
                seconds--;
                
                if (seconds < 0) {{
                    window.location.href = "{YOUR_WEBSITE}";
                }} else {{
                    setTimeout(updateCountdown, 1000);
                }}
            }}
            
            // Iniciar cuenta regresiva
            updateCountdown();
            
            // También redirigir después de 5 segundos
            setTimeout(function() {{
                window.location.href = "{YOUR_WEBSITE}";
            }}, 5000);
        </script>
    </head>
    <body>
        <div class="container">
            <div class="success">✅ ¡LINKVERTISE COMPLETADO!</div>
            
            <div class="message">
                ¡Gracias por apoyar Genesis Hub V2!<br>
                Tu verificación ha sido registrada exitosamente.
            </div>
            
            <div class="message">
                Ahora puedes regresar y generar tu key.
            </div>
            
            <div class="countdown" id="countdown">
                Redirigiendo en 5 segundos...
            </div>
            
            <a href="{YOUR_WEBSITE}" class="button">
                🚀 REGRESAR A GENESIS HUB
            </a>
            
            <div class="note">
                Si no eres redirigido automáticamente, haz click en el botón.
            </div>
        </div>
    </body>
    </html>
    '''
    
    return html_content

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
    
    # 1. VERIFICAR LINKVERTISE
    if not check_linkvertise_completed(user_id):
        return jsonify({
            "success": False,
            "message": "Complete Linkvertise first",
            "error_code": "LINKVERTISE_REQUIRED"
        }), 403
    
    current_time = time.time()
    
    # 2. CARGAR DATOS
    data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
        except:
            data = {}
    
    # 3. VERIFICAR SI YA TIENE UNA KEY ACTIVA (POR USER_ID)
    user_has_active_key = False
    remaining_time = 0
    
    for key_info in data.values():
        if key_info.get("user_id") == user_id:
            if current_time < key_info.get("expires", 0):
                user_has_active_key = True
                remaining_time = key_info.get("expires", 0) - current_time
                break
    
    if user_has_active_key and remaining_time > 0:
        hours = int(remaining_time / 3600)
        minutes = int((remaining_time % 3600) / 60)
        seconds = int(remaining_time % 60)
        return jsonify({
            "success": False,
            "message": f"Wait {hours}h {minutes}m {seconds}s",
            "time_remaining": remaining_time
        }), 429
    
    # 4. GENERAR NUEVA KEY
    key = generate_key()
    
    # 5. GUARDAR KEY
    data[ip] = {
        "key": key,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "expires": current_time + COOLDOWN,
        "ip": ip,
        "user_agent": request.headers.get('User-Agent', ''),
        "user_id": user_id,
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
        "expires_in": COOLDOWN,
        "expires_at": data[ip]["expires"],
        "message": "Key generated successfully!"
    })

@app.route("/check-key/<key>", methods=["GET"])
def check_key(key):
    """VERIFICACIÓN PARA ROBLOX - CRÍTICO"""
    clean_keys()
    
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        return jsonify({"error": "Database error"}), 500
    
    current_time = time.time()
    
    for info in data.values():
        if info.get("key") == key:
            expired = current_time >= info.get("expires", 0)
            
            return jsonify({
                "exists": True,
                "expired": expired,
                "created": info.get("created"),
                "expires_at": info.get("expires"),
                "used_in_roblox": info.get("used_in_roblox", False),
                "user_id": info.get("user_id"),
                "message": "Key is valid" if not expired else "Key expired"
            })
    
    return jsonify({
        "exists": False,
        "message": "Key not found"
    })

@app.route("/verify-roblox", methods=["POST"])
def verify_roblox():
    """MARCA UNA KEY COMO USADA EN ROBLOX"""
    data = request.get_json()
    
    if not data or 'key' not in data:
        return jsonify({"success": False, "error": "No key provided"}), 400
    
    key = data['key']
    clean_keys()
    
    keys_data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                keys_data = json.load(f)
        except:
            return jsonify({"success": False, "error": "Database error"}), 500
    
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
                        "message": "Key already used in Roblox"
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

# ========== ENDPOINTS DE DIAGNÓSTICO ==========
@app.route("/api-status", methods=["GET"])
def api_status():
    """Verifica que la API esté funcionando"""
    return jsonify({
        "status": "online",
        "service": "Genesis Hub V2",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "keys_active": sum(1 for info in json.load(open(DATA_FILE)).values() if time.time() < info.get("expires", 0)) if os.path.exists(DATA_FILE) else 0
    })

@app.route("/key-info/<key>", methods=["GET"])
def key_info(key):
    """Información detallada de una key"""
    clean_keys()
    
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        return jsonify({"error": "Database error"}), 500
    
    current_time = time.time()
    
    for info in data.values():
        if info.get("key") == key:
            remaining = info.get("expires", 0) - current_time
            hours = int(remaining / 3600) if remaining > 0 else 0
            minutes = int((remaining % 3600) / 60) if remaining > 0 else 0
            
            return jsonify({
                "found": True,
                "key": key,
                "created": info.get("created"),
                "expires_in": f"{hours}h {minutes}m",
                "expired": remaining <= 0,
                "used_in_roblox": info.get("used_in_roblox", False),
                "user_id": info.get("user_id")
            })
    
    return jsonify({"found": False, "key": key})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print(f"🚀 Genesis Hub V2 - Roblox Ready")
    print(f"🌐 URL: {YOUR_WEBSITE}")
    print(f"🔗 Linkvertise: {LINKVERTISE_URL}")
    print(f"🔑 Key Format: ABC12-XYZ34-PQR56")
    app.run(host="0.0.0.0", port=port, debug=False)
