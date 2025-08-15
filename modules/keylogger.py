# keylogger.py — SAFE portfolio sender (no capture)
# Modes:
#   demo   : emit synthetic key events
#   replay : read a text file and stream its characters as events
#
# Usage (Windows VM):
#   py keylogger.py 192.168.77.129 5050 --mode demo --window "Windows VM" --rate 8
#   py keylogger.py 192.168.77.129 5050 --mode replay --file C:\path\sample.txt --rate 10

import argparse, json, time, datetime, itertools, urllib.request, pathlib, sys

def _post(url: str, evt: dict):
    data = json.dumps(evt).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        resp.read()

def _now():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def run_demo(url: str, window: str, rate: float):
    chars = list("HELLO_DEMO_123 ") + ["[Enter]"]
    delay = 1.0 / max(rate, 0.1)
    print(f"[demo] sending to {url} @ ~{rate} keys/sec  window={window}")
    shown = 0
    while True:
        try:
            for ch in itertools.cycle(chars):
                evt = {"type":"KEY","key":ch,"window":window,"ts":_now()}
                _post(url, evt)
                if shown < 10:
                    print("sent:", ch); shown += 1
                time.sleep(delay)
        except Exception as e:
            print("[demo] post failed:", e, "— retrying in 1s")
            time.sleep(1)

def run_replay(url: str, window: str, path: str, rate: float):
    p = pathlib.Path(path)
    if not p.exists():
        print(f"[replay] file not found: {p}"); sys.exit(1)
    text = p.read_text(encoding="utf-8", errors="ignore")
    # stream characters; treat newline as Enter
    delay = 1.0 / max(rate, 0.1)
    print(f"[replay] {p} -> {url} @ ~{rate} chars/sec window={window}")
    i = 0
    while True:
        try:
            for ch in text:
                key = "[Enter]" if ch == "\n" else ch
                evt = {"type":"KEY","key":key,"window":window,"ts":_now()}
                _post(url, evt)
                if i < 10:
                    print("sent:", repr(key)); i += 1
                time.sleep(delay)
        except Exception as e:
            print("[replay] post failed:", e, "— retrying in 1s")
            time.sleep(1)

def main(argv=None):
    ap = argparse.ArgumentParser(description="SAFE sender for GUI demo (no real capture).")
    ap.add_argument("host", help="Receiver host (Kali eth1 IP), e.g. 192.168.77.129")
    ap.add_argument("port", nargs="?", type=int, default=5050, help="Receiver port (default 5050)")
    ap.add_argument("--mode", choices=["demo","replay"], default="demo")
    ap.add_argument("--file", help="Path to text file for --mode replay")
    ap.add_argument("--rate", type=float, default=6.0, help="Events per second (default 6)")
    ap.add_argument("--window", default="Windows VM", help="Window label to show in GUI")
    args = ap.parse_args(argv)

    url = f"http://{args.host}:{args.port}/event"
    if args.mode == "replay":
        if not args.file:
            ap.error("--file is required when --mode replay")
        run_replay(url, args.window, args.file, args.rate)
    else:
        run_demo(url, args.window, args.rate)

if __name__ == "__main__":
    main()
