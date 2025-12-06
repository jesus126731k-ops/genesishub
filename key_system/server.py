from flask import Flask, request, jsonify, send_from_directory
import json, time, random, string, os

app = Flask(__name__)

DATA_FILE = "keys.json"

# Crear archivo si no existe
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def cargar_datos():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def guardar_datos(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generar_key():
    return "GEN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=25))

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(".", "favicon.ico")

@app.route("/generar")
def generar():
    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "unknown")
    datos = cargar_datos()

    ahora = int(time.time())

    if ip in datos:
        ultimo = datos[ip]["time"]
        if ahora - ultimo < 86400:
            restante = 86400 - (ahora - ultimo)
            horas = restante // 3600
            minutos = (restante % 3600) // 60
            return jsonify({"error": f"Ya generaste una key. Espera {horas}h {minutos}m."})

    key = generar_key()

    datos[ip] = {
        "key": key,
        "time": ahora,
        "user_agent": ua
    }

    guardar_datos(datos)

    return jsonify({"key": key})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3333)
