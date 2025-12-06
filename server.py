from flask import Flask, jsonify, send_from_directory, request, abort
import random, string, time, json, os

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys.json")
COOLDOWN = 86400
SECRET = "G3N3SIS_HUB_2025"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def gk():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=24))

def cl():
    with open(DATA_FILE, "r") as f:
        d = json.load(f)
    t = time.time()
    n = {i:o for i,o in d.items() if t < o["e"]}
    with open(DATA_FILE, "w") as f:
        json.dump(n, f)

@app.route("/")
@app.route("/genesis")
def i():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "index.html")

@app.route("/generar")
def g():
    cl()
    ip = request.remote_addr
    t = time.time()
    with open(DATA_FILE, "r") as f:
        d = json.load(f)
    if ip in d:
        r = int((d[ip]["e"] - t) / 3600)
        return jsonify({"e": f"{r}h"})
    k = gk()
    d[ip] = {
        "k": k,
        "t": time.strftime("%Y-%m-%d %H:%M:%S"),
        "e": t + COOLDOWN,
        "i": ip
    }
    with open(DATA_FILE, "w") as f:
        json.dump(d, f)
    return jsonify({"k": k, "t": d[ip]["t"]})

@app.route("/validar/<k>")
def v(k):
    cl()
    with open(DATA_FILE, "r") as f:
        d = json.load(f)
    for o in d.values():
        if o["k"] == k and time.time() < o["e"]:
            return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route("/x/<s>")
def x(s):
    if s != SECRET:
        abort(404)
    with open(DATA_FILE, "r") as f:
        return jsonify(json.load(f))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
