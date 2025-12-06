from flask import Flask, jsonify, request, send_from_directory, abort
import os, json, time, random, string

app = Flask(__name__)

# Archivos y configuración
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys.json")
COOLDOWN = 86400  # 24 horas en segundos
SECRET = "G3N3SIS_HUB_2025"

# Crear archivo si no existe
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

# Generar key aleatoria
def generate_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=24))

# Limpiar llaves expiradas
def clean_keys():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    current_time = time.time()
    data = {ip: info for ip, info in data.items() if current_time < info["expires"]}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Servir página principal
@app.route("/")
@app.route("/genesis")
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "index.html")

# Generar nueva key
@app.route("/generate")
def generate():
    clean_keys()
    ip = request.remote_addr
    current_time = time.time()

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    # Verificar cooldown
    if ip in data:
        remaining = int((data[ip]["expires"] - current_time) / 3600)
        return jsonify({"error": f"Wait {remaining}h to generate another key"})

    key = generate_key()
    data[ip] = {
        "key": key,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "expires": current_time + COOLDOWN,
        "ip": ip
    }

    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

    return jsonify({"key": key, "created": data[ip]["created"]})

# Validar key
@app.route("/validate/<key>")
def validate(key):
    clean_keys()
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    for info in data.values():
        if info["key"] == key and time.time() < info["expires"]:
            return jsonify({"valid": True})
    return jsonify({"valid": False})

# Endpoint para ver todas las keys (solo con SECRET)
@app.route("/keys/<secret>")
def all_keys(secret):
    if secret != SECRET:
        abort(404)
    with open(DATA_FILE, "r") as f:
        return jsonify(json.load(f))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
