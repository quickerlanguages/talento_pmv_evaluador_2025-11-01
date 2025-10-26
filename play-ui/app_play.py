\
from flask import Flask, render_template, request, jsonify
import os, json, time, uuid, argparse

app = Flask(__name__, template_folder="templates")

BACKEND_DB = os.environ.get("BACKEND_DB", "./backend/talento_READY_2025-09-14.db")
SESS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sessions"))
os.makedirs(SESS_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.after_request
def add_cache_headers(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp

@app.post("/submit")
def submit():
    payload = request.json or {}
    session_id = payload.get("sesion_id") or int(time.time())
    rec = {
        "id": str(uuid.uuid4()),
        "sesion_id": session_id,
        "ts": time.time(),
        "answers": payload.get("answers", []),
        "meta": {"agent": request.headers.get("User-Agent", "")}
    }
    out = os.path.join(SESS_DIR, f"session_{session_id}.jsonl")
    with open(out, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return jsonify({"ok": True, "stored": out})

@app.get("/health")
def health():
    ok = os.path.exists(BACKEND_DB)
    return {"status":"ok" if ok else "no-db","db": BACKEND_DB}, 200 if ok else 503

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=False)

if __name__ == "__main__":
    main()
