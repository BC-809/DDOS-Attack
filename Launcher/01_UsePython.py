import subprocess
import sys
import os

def run_cmd(command):
    print(f"[CMD] {command}")
    result = subprocess.run(command, shell=True, text=True)
    return result.returncode

def main():
    print("=" * 40)
    print(" DDOS-Attack Setup (Termux)")
    print(" WARNING: Lab use only!")
    print("=" * 40)
    input("Press Enter to continue...")

    # 检查 Python 版本
    if sys.version_info < (3, 6):
        print("[!] Need Python 3.6+")
        sys.exit(1)
    print(f"[*] Python {sys.version} ready.")

    # 安装 git 和 figlet (使用 pkg)
    print("[*] Installing git and figlet...")
    run_cmd("pkg install git figlet -y")

    # 克隆仓库
    if not os.path.exists("DDOS-Attack"):
        print("[*] Cloning repository...")
        run_cmd("git clone https://github.com/BC-809/DDOS-Attack.git")
    else:
        print("[*] Repo already exists, pulling latest...")
        os.chdir("DDOS-Attack")
        run_cmd("git pull")
        os.chdir("..")

    os.chdir("DDOS-Attack")

    # 运行攻击脚本（英文版 01）
    print("[*] Starting attack script...")
    run_cmd("python DDOS/English/DDOS-Attack_01_e.py")

if __name__ == "__main__":
    main()
