# safe_demo_debug.py
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
        return resp.status

count = 0
while True:
    try:
        for ch in itertools.cycle(chars):
            evt = {
                "type": "KEY",
                "key": ch,
                "window": "Win11 Notepad",
                "ts": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }
            status = post(evt)
            if count < 10:
                print("sent", ch, "status", status)
                count += 1
            time.sleep(0.15)
    except Exception as e:
        print("send error:", repr(e))
        time.sleep(2)
