import os, glob
from .crypto import decrypt_line

LOG_DIR = "logs"

def view_latest():
    files = sorted(glob.glob(os.path.join(LOG_DIR, "keylog-*.txt.enc")))
    if not files:
        print("No logs yet")
        return
    with open(files[-1], "rb") as f:
        for line in f:
            print(decrypt_line(line.strip()))
if __name__ == "__main__":
    view_latest()
