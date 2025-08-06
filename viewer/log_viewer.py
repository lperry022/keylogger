import os
import tkinter as tk
from tkinter import ttk, messagebox
from cryptography.fernet import Fernet
from decryptor import get_decryption_key  # shared password/key logic

LOG_DIR = "logs"

class LogViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Encrypted Log Viewer")

        self.logs = []
        self.sort_asc = True

        self.file_var = tk.StringVar()
        self.file_dropdown = ttk.Combobox(root, textvariable=self.file_var, state="readonly")
        self.file_dropdown.pack(padx=10, pady=5)

        refresh_btn = ttk.Button(root, text="🔁 Refresh Logs", command=self.refresh_files)
        refresh_btn.pack(padx=10, pady=5)

        sort_btn = ttk.Button(root, text="⇅ Toggle Sort", command=self.toggle_sort)
        sort_btn.pack(padx=10, pady=5)

        view_btn = ttk.Button(root, text="🔓 View Logs", command=self.view_logs)
        view_btn.pack(padx=10, pady=5)

        self.text = tk.Text(root, wrap="word", height=25, width=100)
        self.text.pack(padx=10, pady=10)

        self.refresh_files()

    def refresh_files(self):
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        files = sorted(os.listdir(LOG_DIR), reverse=not self.sort_asc)
        enc_files = [f for f in files if f.endswith(".enc")]
        self.file_dropdown['values'] = enc_files
        if enc_files:
            self.file_var.set(enc_files[0])
        else:
            self.file_var.set("")

    def toggle_sort(self):
        self.sort_asc = not self.sort_asc
        self.refresh_files()

    def view_logs(self):
        filename = self.file_var.get()
        if not filename:
            messagebox.showwarning("No File", "Please select a log file.")
            return

        path = os.path.join(LOG_DIR, filename)

        try:
            key = get_decryption_key()
            fernet = Fernet(key)
            self.text.delete(1.0, tk.END)

            with open(path, "rb") as f:
                for line in f:
                    try:
                        decrypted = fernet.decrypt(line).decode().strip()
                        self.text.insert(tk.END, decrypted + "\n")
                    except Exception as e:
                        self.text.insert(tk.END, f"[!] Decryption error: {e}\n")

        except Exception as e:
            messagebox.showerror("Decryption Failed", f"Error: {e}")

def run_viewer():
    root = tk.Tk()
    app = LogViewerApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_viewer()
