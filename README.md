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

## 🗂️ Project Structure

keylogger/
├─ startup.py
├─ modules/
│  ├─ gui_ctk.py
│  ├─ keylogger.py
│  └─ crypto.py
├─ logs/
├─ requirements.txt
└─ README.md

---

## 🗂️ Project Structure
- Python 3.10+
- Windows/macOS/Linux
- Linux GUI needs Tk runtime: sudo apt-get install -y python3-tk

---

## ▶️ How to Run

### 1) Clone
git clone https://github.com/<your-username>/keylogger.git
cd keylogger

### 2) Virtual env
python -m venv .venv
### macOS/Linux:
source .venv/bin/activate
### Windows:
.venv\Scripts\activate

## 3) Install deps
python -m pip install --upgrade pip
pip install -r requirements.txt
### Linux only (Tk):
sudo apt-get update && sudo apt-get install -y python3-tk

### 4) Run GUI
python startup.py

---

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