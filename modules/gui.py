import os
import glob
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import font as tkfont
from datetime import datetime

from .crypto import set_password_for_new_key, encrypt_line, decrypt_line
from .keylogger import KeyloggerService

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Keylogger Control Panel")
        self.geometry("1000x640")

        # state for table
        self.base_rows = []      # [(ts, kind, detail)]
        self.sort_by = "time"    # "time" | "type" | "detail"
        self.sort_asc = True

        # --- top controls
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="Password (for new key):").pack(side="left")
        self.pw_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.pw_var, show="*", width=22).pack(side="left", padx=6)
        ttk.Button(top, text="Init Key", command=self.init_key).pack(side="left", padx=6)

        self.start_btn = ttk.Button(top, text="Start Logging", command=self.start_logging)
        self.start_btn.pack(side="left", padx=6)
        self.stop_btn = ttk.Button(top, text="Stop Logging", command=self.stop_logging, state="disabled")
        self.stop_btn.pack(side="left", padx=6)

        self.combine_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text="Combine typing", variable=self.combine_var).pack(side="left", padx=6)

        ttk.Button(top, text="Refresh Files", command=self.refresh_files).pack(side="left", padx=12)

        # --- search / filter row
        sf = ttk.Frame(self)
        sf.pack(fill="x", padx=10, pady=(0, 8))

        ttk.Label(sf, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(sf, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=6)
        search_entry.bind("<KeyRelease>", lambda e: self._refresh_table())

        ttk.Label(sf, text="Type:").pack(side="left", padx=(12, 0))
        self.type_var = tk.StringVar(value="All")
        ttk.Combobox(sf, textvariable=self.type_var, values=["All", "APP", "KEY", "TEXT", "ERR"],
                     state="readonly", width=6).pack(side="left", padx=6)
        self.type_var.trace_add("write", lambda *_: self._refresh_table())

        ttk.Button(sf, text="Clear", command=self._clear_filters).pack(side="left", padx=6)

        # --- body: file list + actions + table
        mid = ttk.Frame(self)
        mid.pack(fill="both", expand=True, padx=10, pady=8)

        left = ttk.Frame(mid)
        left.pack(side="left", fill="y")

        ttk.Label(left, text="Encrypted logs").pack(anchor="w")
        self.file_list = tk.Listbox(left, height=24, width=40)
        self.file_list.pack(side="left", fill="y")
        file_scroll = ttk.Scrollbar(left, orient="vertical", command=self.file_list.yview)
        file_scroll.pack(side="left", fill="y")
        self.file_list.configure(yscrollcommand=file_scroll.set)
        self.file_list.bind("<<ListboxSelect>>", lambda e: self.view_selected())

        btns = ttk.Frame(mid)
        btns.pack(side="left", fill="y", padx=10)
        ttk.Button(btns, text="View Selected", command=self.view_selected).pack(fill="x", pady=4)
        ttk.Button(btns, text="Export Decrypted...", command=self.export_selected).pack(fill="x", pady=4)

        # --- viewer (sortable table)
        right = ttk.Frame(mid)
        right.pack(side="left", fill="both", expand=True)
        ttk.Label(right, text="Decrypted preview").pack(anchor="w")

        self.viewer = ttk.Treeview(
            right,
            columns=("time", "type", "detail"),
            show="headings",
            height=25
        )
        # headings + sort handlers
        self.viewer.heading("time", text="Time", command=lambda: self._set_sort("time"))
        self.viewer.heading("type", text="Type", command=lambda: self._set_sort("type"))
        self.viewer.heading("detail", text="Detail", command=lambda: self._set_sort("detail"))

        self.viewer.column("time", width=180, anchor="w")
        self.viewer.column("type", width=70, anchor="center")
        self.viewer.column("detail", width=640, anchor="w")
        self.viewer.pack(fill="both", expand=True)

        # zebra + APP highlight
        default_font = tkfont.nametofont("TkDefaultFont")
        app_font = default_font.copy()
        app_font.configure(weight="bold")
        self.viewer.tag_configure("odd", background="#f7f7f7")
        self.viewer.tag_configure("app", font=app_font)
        self.viewer.tag_configure("match", background="#fff7cc")  # highlight search matches

        # --- status bar
        self.status = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w").pack(fill="x", padx=10, pady=(0, 8))

        # services
        self.logger = KeyloggerService(self._on_keylog, combine=True, idle_ms=800)
        self.refresh_files()

    # ----- key / crypto
    def init_key(self):
        try:
            set_password_for_new_key(self.pw_var.get())
            self.status.set("Key initialized (or already present).")
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
            self.logger.combine = self.combine_var.get()
            self.logger.start()
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.status.set("Logging started.")
        except Exception as e:
            messagebox.showerror("Start failed", str(e))

    def stop_logging(self):
        self.logger.stop()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status.set("Logging stopped.")

    # ----- files
    def refresh_files(self):
        self.file_list.delete(0, tk.END)
        files = sorted(glob.glob(os.path.join(LOG_DIR, "keylog-*.txt.enc")))
        for f in files:
            self.file_list.insert(tk.END, os.path.basename(f))
        self.status.set(f"Found {len(files)} encrypted log(s).")

    def _selected_path(self):
        sel = self.file_list.curselection()
        if not sel:
            return None
        fname = self.file_list.get(sel[0])
        return os.path.join(LOG_DIR, fname)

    # ----- table build/filter/sort
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
        if not path:
            return
        try:
            rows = []
            with open(path, "rb") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        plaintext = decrypt_line(line)
                        rows.append(self._parse_line(plaintext))
                    except Exception as e:
                        rows.append(("", "ERR", f"decrypt error: {e}"))
            self.base_rows = rows
            self._refresh_table()
            self.status.set(f"Viewed: {os.path.basename(path)} — {len(rows)} entries")
        except Exception as e:
            messagebox.showerror("View failed", str(e))

    def _clear_filters(self):
        self.search_var.set("")
        self.type_var.set("All")
        self._refresh_table()

    def _set_sort(self, field):
        if self.sort_by == field:
            self.sort_asc = not self.sort_asc
        else:
            self.sort_by, self.sort_asc = field, True
        self._refresh_table()

    def _refresh_table(self):
        # filter by type
        tfilter = self.type_var.get()
        rows = [r for r in self.base_rows if tfilter == "All" or r[1] == tfilter]

        # search
        q = self.search_var.get().strip().lower()
        matches = set()
        if q:
            for i, r in enumerate(rows):
                if q in (r[0].lower() + " " + r[1].lower() + " " + r[2].lower()):
                    matches.add(i)
            rows = [r for i, r in enumerate(rows) if i in matches]

        # sort
        key_funcs = {
            "time": lambda r: r[0],
            "type": lambda r: r[1],
            "detail": lambda r: r[2].lower(),
        }
        rows.sort(key=key_funcs[self.sort_by], reverse=not self.sort_asc)

        # render
        for r in self.viewer.get_children():
            self.viewer.delete(r)

        for i, (ts, kind, detail) in enumerate(rows):
            tags = []
            if kind == "APP":
                tags.append("app")
            if q:
                # tag entire row if it matched search
                tags.append("match")
            if i % 2:
                tags.append("odd")
            self.viewer.insert("", "end", values=(ts, kind, detail), tags=tuple(tags))

    # ----- export
    def export_selected(self):
        path = self._selected_path()
        if not path:
            messagebox.showwarning("No file", "Select an encrypted log first.")
            return
        out = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=os.path.basename(path).replace(".enc", ""),
        )
        if not out:
            return
        try:
            with open(path, "rb") as f_in, open(out, "w", encoding="utf-8") as f_out:
                for line in f_in:
                    line = line.strip()
                    if not line:
                        continue
                    f_out.write(decrypt_line(line) + "\n")
            self.status.set(f"Exported to: {out}")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
