# Keylogger with GUI (Educational Project)

This is an **educational keylogger** project originally inspired by [Shaun Halverson’s tutorial](https://www.youtube.com/watch?v=mDY3v2Xx-Q4&ab_channel=ShaunHalverson) and expanded to include:

- AES-based encryption using Python’s `cryptography` library  
- A Tkinter-based **GUI control panel**  
- Start/Stop logging controls  
- Encrypted log storage  
- Log viewer with **search, filter, and sorting**  
- Option to **combine typing** into readable words/sentences  
- Export decrypted logs to text files  

> ⚠️ **Disclaimer:**  
> This project is for **learning purposes only**.  
> Do not use keyloggers for malicious or unauthorized activities. Always obtain explicit consent before running monitoring software on any system.

---

## 🔍 Features

- **Encrypted Logging** – All keystrokes and active window titles are stored in `.enc` files.
- **GUI Control Panel** – Start/stop logging, browse logs, search, filter, and sort results.
- **Search & Filter** – Quickly find specific entries and filter by event type (`APP`, `KEY`, etc.).
- **Sorting** – Click column headers to sort by time, type, or detail.
- **Combine Typing** – Group individual keystrokes into complete words/sentences.
- **Export Decrypted Logs** – Save a decrypted copy of any log file.

---

## 🗂️ Files Included

- `modules/crypto.py` – Handles encryption/decryption.  
- `modules/keylogger.py` – Keylogging logic with optional character grouping.  
- `modules/gui.py` – Tkinter GUI for controlling the keylogger and viewing logs.  
- `logs/` – Directory where encrypted logs are stored.  
- `secret.key` / `salt.bin` – Encryption key and salt (generated after first run).  
- `README.md` – This documentation.  
- `LICENSE` – MIT License.  

---

## ▶️ How to Run

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/keylogger-educational.git
   cd keylogger-educational
2. **Create and activate a virtual environment (recommended):**
   ```bash
    python -m venv .venv
    source .venv/bin/activate   # macOS/Linux
    .venv\Scripts\activate      # Windows
3. **Install dependencies:**
   ```bash
    pip install pynput cryptography pywin32 psutil
4. **Install dependencies:**
   ```bash
    python -m modules.gui
5. **Using the GUI:**
- Enter a password and click Init Key (first-time setup).
- Click Start Logging to begin recording keystrokes.
- Select any .enc log from the left panel to view decrypted content. 
- Use the Search box, Type filter, and column sorting for analysis.
- Click Export Decrypted to save a plaintext copy.

## 🎓 Source Tutorial
Original tutorial for basic keylogging:
🔗 Shaun Halverson - Create a Keylogger in Python (YouTube)

This project extends that tutorial with encryption, GUI, and enhanced log management.

## 🤖 AI Assistance
Parts of the design, feature enhancements, and debugging process were developed with assistance from OpenAI’s ChatGPT. AI was used to:
- Suggest and refine the encryption and decryption flow
- Design the Tkinter GUI and event handling
- Implement search, filter, and sorting features
- Improve code readability and structure