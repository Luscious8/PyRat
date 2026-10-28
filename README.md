# 🐍 Python Reverse Shell & C2 Agent

A lightweight, Python-based Reverse Shell and Command & Control (C2) framework designed for educational purposes, Red Team operations, and authorized penetration testing. This project demonstrates core post-exploitation techniques including stealthy persistence, file transfer, and remote command execution.

## ⚠️ Legal Disclaimer
**This tool is strictly for educational and authorized testing purposes only.** The author is not responsible for any misuse or damage caused by this program. Using this tool against targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state, and federal laws.

---

## 🏗️ Architecture Overview

This project uses a **Reverse Shell** architecture. This means the Victim (Client) initiates the connection outbound to the Attacker (Listener). This approach bypasses inbound firewall rules and NAT restrictions, which typically block incoming connections.

**The Flow:**
1. **Attacker:** Starts a listener on their machine and waits for incoming connections.
2. **Victim:** Executes `client.py`.
3. **Persistence:** The client silently modifies a Registry key on the victim's machine, ensuring the script runs again after a reboot.
4. **Connection:** The victim's machine establishes a TCP connection to the attacker's configured IP and Port.
5. **C2 Session:** Once the connection is established, the attacker sends commands, and the victim's machine returns the output.

---

## ⚙️ How It Works (Deep Dive)

### 1. Persistence (`install` function)
When the script is executed for the first time, it calls the `install()` function:
- It creates a hidden folder named `regky` inside the current user's directory (`C:\Users\<User>\`).
- It copies itself into this folder, renaming the file to `setup.exe`.
- It adds an entry to the `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` registry key.
- **Result:** Every time the user logs into Windows, the script will automatically execute in the background without requiring Administrator privileges.

### 2. Main Loop (`do_work` function)
- The script enters a continuous loop.
- It attempts to connect to the attacker's IP and Port (configured by the user).
- If the attacker's machine is offline, it waits 10 seconds and tries again (Auto-Reconnect).
- Once connected, it waits to receive commands.

### 3. Command Handling
When the attacker sends a command, the script parses it:
- **Normal Commands (`dir`, `ipconfig`):** Uses `subprocess.Popen` to execute the command and sends the output back to the attacker.
- **Screenshot (`pic`):** Uses the `PIL` (Pillow) library to capture the victim's screen and save it.
- **File Transfer (`download` / `upload`):** Transfers files between the attacker and the victim using custom EOF markers (`EOFEOFX`).
- **Directory Change (`cd`):** Changes the current working directory.
- **Connection Close (`quit`):** Terminates the current session.

---

## ✨ Features

- **Stealthy Persistence:** Establishes persistence via the HKCU registry without requiring Administrator privileges.
- **Auto-Reconnect:** Automatically attempts to reconnect if the network drops or the listener goes offline.
- **Screenshot Capability:** Captures the victim's screen.
- **File Transfer:** Safe upload/download using custom EOF markers.
- **Interactive Shell:** Provides full command prompt access.

---

## 🚀 Prerequisites

- **Python 3.x** (installed on both Client and Listener machines).
- For the Screenshot feature: `pip install Pillow`

---

## 🛠️ Usage Guide

**Step 1: Configure**
Open `client.py` and edit the connection variables to match your listener's IP:
```python
CONNECT_HOST = "YOUR_IP_HERE" # Replace with your listener's IP
CONNECT_PORT = 666            # Replace with your desired port
