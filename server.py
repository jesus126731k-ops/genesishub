from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os, json, time, random, string, hashlib

app = Flask(__name__, static_folder='.')
CORS(app)

DATA_FILE = "keys.json"
LINKVERTISE_FILE = "linkvertise_tracking.json"
COOLDOWN = 86400  # 24 horas
SECRET = "G3N3SIS_HUB_2025"

# TUS LINKS REALES
LINKVERTISE_URL = "https://link-hub.net/1457789/3pNxakfWICZQ"
YOUR_WEBSITE = "https://genesishub-v2.onrender.com"

# Inicializar archivos si no existen
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(LINKVERTISE_FILE):
    with open(LINKVERTISE_FILE, "w") as f:
        json.dump({}, f)

# ========== GENERADOR DE KEYS (15 CARACTERES) ==========
def generate_key():
    """Genera key de 15 caracteres en formato: ABC12-XYZ34-PQR56"""
    key_parts = []
    
    for _ in range(3):  # 3 segmentos
        # 3 letras aleatorias mayúsculas
        letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
        # 2 números aleatorios
        numbers = ''.join(random.choices('0123456789', k=2))
        # Combinar: ABC12
        key_parts.append(f"{letters}{numbers}")
    
    # Unir con guiones: ABC12-XYZ34-PQR56
    key = '-'.join(key_parts)
    
    # Verificar que sea única
    if not is_key_already_used(key):
        return key
    else:
        # Si ya existe, generar otra
        return generate_key()

def is_key_already_used(key):
    """Verifica si una key ya existe en la base de datos"""
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
    """Crea un ID único para cada usuario"""
    return hashlib.md5(f"{ip}{user_agent[:50]}".encode()).hexdigest()

def mark_linkvertise_completed(user_id, ip):
    """Marca Linkvertise como completado para un usuario"""
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
        "last_check": time.time(),
        "timestamp": time.time()
    }
    
    with open(LINKVERTISE_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    return True

def check_linkvertise_completed(user_id):
    """Verifica si el usuario completó Linkvertise (válido por 24h)"""
    if not os.path.exists(LINKVERTISE_FILE):
        return False
    
    try:
        with open(LINKVERTISE_FILE, "r") as f:
            data = json.load(f)
    except:
        return False
    
    if user_id in data:
        user_data = data[user_id]
        # Verificar si completó y es menor a 24 horas
        if user_data.get("completed") and (time.time() - user_data.get("timestamp", 0)) < 86400:
            return True
    
    return False

def clean_keys():
    """Elimina keys expiradas"""
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

# ========== RUTAS DE LA API ==========
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)

@app.route("/linkvertise-success")
def linkvertise_success():
    """Página de éxito de Linkvertise - FUNCIONAL"""
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    user_id = get_user_id(ip, user_agent)
    
    # Marcar como completado
    mark_linkvertise_completed(user_id, ip)
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>✅ Linkvertise Completed - Genesis Hub V2</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                background: #000;
                color: #fff;
                font-family: 'Segoe UI', Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                background: rgba(20, 20, 20, 0.95);
                padding: 40px;
                border-radius: 20px;
                border: 2px solid #ff6600;
                max-width: 600px;
                width: 100%;
                text-align: center;
                box-shadow: 0 10px 30px rgba(255, 102, 0, 0.3);
            }
            
            .success-icon {
                font-size: 80px;
                color: #00ff00;
                margin-bottom: 20px;
                animation: pulse 1.5s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }
            
            h1 {
                color: #00ff00;
                font-size: 2.5rem;
                margin-bottom: 20px;
                background: linear-gradient(90deg, #00ff00, #00cc00);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .message {
                color: #ccc;
                font-size: 1.2rem;
                margin-bottom: 30px;
                line-height: 1.6;
            }
            
            .countdown {
                color: #ff6600;
                font-size: 1.5rem;
                margin: 30px 0;
                font-weight: bold;
            }
            
            .button {
                display: inline-block;
                background: linear-gradient(135deg, #ff6600, #ff3300);
                color: white;
                padding: 15px 40px;
                border-radius: 12px;
                text-decoration: none;
                font-weight: bold;
                font-size: 1.2rem;
                border: none;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-top: 20px;
            }
            
            .button:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 20px rgba(255, 102, 0, 0.4);
            }
            
            .note {
                color: #888;
                font-size: 0.9rem;
                margin-top: 30px;
                font-style: italic;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✅</div>
            <h1>LINKVERTISE COMPLETED!</h1>
            
            <div class="message">
                Thank you for supporting Genesis Hub V2!<br>
                Your Linkvertise completion has been recorded.
            </div>
            
            <div class="message">
                You can now return to the main page and<br>
                generate your key by clicking "CREATE YOUR KEY".
            </div>
            
            <div class="countdown" id="countdown">
                Redirecting in <span id="seconds">5</span> seconds...
            </div>
            
            <a href="/" class="button">
                🚀 RETURN TO GENESIS HUB
            </a>
            
            <div class="note">
                If you are not redirected automatically, click the button above.
            </div>
        </div>
        
        <script>
            let seconds = 5;
            const countdownElement = document.getElementById('seconds');
            
            function updateCountdown() {
                countdownElement.textContent = seconds;
                seconds--;
                
                if (seconds < 0) {
                    window.location.href = "/";
                } else {
                    setTimeout(updateCountdown, 1000);
                }
            }
            
            // Start countdown
            updateCountdown();
            
            // Also redirect after 5 seconds
            setTimeout(() => {
                window.location.href = "/";
            }, 5000);
            
            // Save completion in localStorage too
            localStorage.setItem('genesis_hub_linkvertise_completed', JSON.stringify({
                completed: true,
                timestamp: Date.now(),
                expires: Date.now() + (24 * 60 * 60 * 1000) // 24 hours
            }));
        </script>
    </body>
    </html>
    """
    
    return html_content

@app.route("/check-linkvertise", methods=["GET"])
def check_linkvertise():
    """Verifica estado de Linkvertise del usuario"""
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    user_id = get_user_id(ip, user_agent)
    
    completed = check_linkvertise_completed(user_id)
    
    return jsonify({
        "completed": completed,
        "message": "Linkvertise completed" if completed else "Linkvertise required"
    })

@app.route("/can-generate", methods=["GET"])
def can_generate():
    """Verifica si el usuario puede generar una key"""
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    user_id = get_user_id(ip, user_agent)
    
    # 1. Verificar Linkvertise
    if not check_linkvertise_completed(user_id):
        return jsonify({
            "can_generate": False,
            "reason": "Complete Linkvertise first",
            "linkvertise_url": LINKVERTISE_URL
        })
    
    # 2. Verificar cooldown (24h por IP)
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
                "reason": f"Wait {hours}h {minutes}m",
                "time_remaining": remaining
            })
    
    return jsonify({
        "can_generate": True,
        "message": "You can generate a key"
    })

@app.route("/generate-key", methods=["POST"])
def generate_key_endpoint():
    """Genera una nueva key para el usuario"""
    clean_keys()
    
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    user_id = get_user_id(ip, user_agent)
    
    # 1. Verificar Linkvertise
    if not check_linkvertise_completed(user_id):
        return jsonify({
            "success": False,
            "message": "You must complete Linkvertise first",
            "error_code": "LINKVERTISE_REQUIRED",
            "linkvertise_url": LINKVERTISE_URL
        }), 403
    
    current_time = time.time()
    
    # 2. Cargar datos existentes
    data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
        except:
            data = {}
    
    # 3. Verificar cooldown (1 key por IP cada 24h)
    if ip in data:
        remaining = data[ip]["expires"] - current_time
        if remaining > 0:
            hours = int(remaining / 3600)
            minutes = int((remaining % 3600) / 60)
            return jsonify({
                "success": False,
                "message": f"Wait {hours}h {minutes}m before generating another key",
                "time_remaining": remaining
            }), 429
    
    # 4. Generar key única
    key = generate_key()
    
    # 5. Guardar key
    data[ip] = {
        "key": key,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "expires": current_time + COOLDOWN,
        "ip": ip,
        "user_agent": user_agent,
        "linkvertise_completed": True,
        "used_in_roblox": False,
        "roblox_used_at": None,
        "user_id": user_id
    }
    
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    return jsonify({
        "success": True,
        "key": key,
        "created": data[ip]["created"],
        "expires_in": COOLDOWN,
        "message": "Key generated successfully! Valid for 24 hours."
    })

@app.route("/check-key/<key>", methods=["GET"])
def check_key(key):
    """Verifica una key (usado por Roblox)"""
    clean_keys()
    
    data = {}
    if os.path.exists(DATA_FILE):
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
                "message": "Key expired" if expired else "Key is valid"
            })
    
    return jsonify({
        "exists": False,
        "message": "Key not found"
    })

@app.route("/verify-roblox", methods=["POST"])
def verify_roblox():
    """Marca una key como usada en Roblox"""
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

@app.route("/admin/<secret>", methods=["GET"])
def admin(secret):
    """Panel de administración"""
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
        "linkvertise_completed": len(linkvertise_data),
        "server_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "key_format": "ABC12-XYZ34-PQR56 (15 characters)"
    })

# ========== EJECUCIÓN ==========
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print("=" * 60)
    print("🚀 GENESIS HUB V2 - SERVER STARTED")
    print("=" * 60)
    print(f"🌐 Website URL: {YOUR_WEBSITE}")
    print(f"🔗 Linkvertise: {LINKVERTISE_URL}")
    print(f"🔑 Key Format: ABC12-XYZ34-PQR56 (15 characters)")
    print(f"⏰ Cooldown: 24 hours per IP")
    print(f"🔧 Running on port: {port}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=False)
