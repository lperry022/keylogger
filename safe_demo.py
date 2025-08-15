# sender_safe_demo.py  — synthetic demo sender (no deps)
import json, time, itertools, datetime, sys, urllib.request

HOST = sys.argv[1] if len(sys.argv) > 1 else "192.168.77.129"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5050
URL  = f"http://{HOST}:{PORT}/event"

chars = list("HELLO_DEMO_123")

def post(evt):
    data = json.dumps(evt).encode("utf-8")
    req = urllib.request.Request(URL, data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=5) as resp:
        resp.read()

while True:
    try:
        for ch in itertools.cycle(chars):
            evt = {
                "type": "KEY",
                "key": ch,
                "window": "Notepad.exe",
                "ts": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }
            post(evt)
            time.sleep(0.15)
    except Exception:
        time.sleep(1)
