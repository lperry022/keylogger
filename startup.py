# startup.py
import os, json, threading
from receiver_http import start_http_server, incoming_events
from modules.gui_ctk import App

os.makedirs("logs", exist_ok=True)

def append_to_log(evt: dict):
    with open("logs/http-demo.log", "a", encoding="utf-8") as f:
        f.write(json.dumps(evt) + "\n")

if __name__ == "__main__":
    threading.Thread(target=start_http_server, args=("0.0.0.0", 5050), daemon=True).start()
    app = App()
    app.attach_event_queue(incoming_events, log_fn=append_to_log)
    # optional: also feed local demo into same queue
    try: app.logger.set_ui_queue(incoming_events)
    except: pass
    app.mainloop()
