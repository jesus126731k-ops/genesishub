from flask import Flask, jsonify, send_from_directory, request, abort
import random, string, time, json, os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "keys.json")

COOLDOWN = 86400
SECRET = "G3N3SIS_HUB_2025"
LINKVERTISE = "link-hub.net/1457789/3pNxakfWICZQ"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def new_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))

def clean_keys():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    now = time.time()
    data = {ip:v for ip,v in data.items() if now < v["exp"]}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

@app.route("/")
@app.route("/genesis")
def home():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/generate_key")
def generate_key():
    clean_keys()
    ip = request.remote_addr
    refer = request.referrer or ""

    if LINKVERTISE not in refer:
        return jsonify({"error":"Access denied"}),403

    with open(DATA_FILE,"r") as f:
        data = json.load(f)

    now = time.time()
    if ip in data:
        remain = int((data[ip]["exp"]-now)/3600)
        return jsonify({"error":f"Wait {remain}h"}),403

    key = new_key()
    data[ip] = {
        "key":key,
        "time":time.strftime("%Y-%m-%d %H:%M:%S"),
        "exp":now+COOLDOWN
    }

    with open(DATA_FILE,"w") as f:
        json.dump(data,f)

    return jsonify({"key":key})

@app.route("/validate/<key>")
def validate(key):
    clean_keys()
    with open(DATA_FILE,"r") as f:
        data=json.load(f)
    for v in data.values():
        if v["key"]==key and time.time()<v["exp"]:
            return jsonify({"valid":True})
    return jsonify({"valid":False})

@app.route("/admin/<s>")
def admin(s):
    if s!=SECRET:
        abort(404)
    with open(DATA_FILE,"r") as f:
        return jsonify(json.load(f))

if __name__=="__main__":
    app.run(host="0.0.0.0",port=3000)

