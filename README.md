[<简体中文>](README-Chinese.md)

# DDOS-Attack - Distributed Denial of Service Attack Simulation Tool

## Strict Legal & Ethical Warning

- **This project is for educational purposes only!** It is designed to help security researchers, network administrators, and students understand the principles of DDoS attacks in order to better design defense strategies.

- **Unauthorized attacks against any server, network, or device that you do not personally own are serious criminal offenses and will be punished by law.**

- **Please ensure that you only run this code in a completely controlled, isolated lab environment (such as a local virtual machine or a self-built test network).** The author assumes no responsibility for any misuse.

---

## Project Introduction

- `DDOS-Attack` is a Python-based DDoS simulation script capable of sending UDP flood packets to a specified IP address and port.

---

## Key Features
- Simple command-line interactive interface
- Customizable target IP, port, and number of packets to send
- Automatic target reachability check before attack (to avoid ineffective attacks)
- Retains ASCII art startup banner (requires `figlet` support)

---

## Project Structure
- ├── DDOS/
- │ └── Chinese/
- │ └── DDOS-Attack_01_c.py → Attack code file, Chinese version
- │ └── DDOS-Attack_02_c.py → Quick version (skips ASCII art loading), Chinese
- │ └── DDOS-Attack_03_c.py → Version with spoofed source IP (requires ROOT privileges), Chinese
- │ └── English/
- │ └── DDOS-Attack_01_e.py → Attack code file, English version
- │ └── DDOS-Attack_02_e.py → Quick version (skips ASCII art loading), English
- │ └── DDOS-Attack_03_e.py → Version with spoofed source IP (requires ROOT privileges), English
- ├── Launcher/
- │ └── 01_UseWindows.bat → Windows launcher (installs required files and runs 01)
- │ └── 01_UsePython.py → Python Android launcher (installs required files at runtime and launches 01)
- │ └── 01_UseLinux → Linux launcher (installs required files and runs 01)
- ├── Art/
- │ └── Figlet_DDOS-Attack → Preview of figlet fonts generated in the code(DDOS-Attack)
- │ └── Figlet_AttackStarting → Preview of figlet fonts generated in the code(AttackStarting)
- └── README.md → English introduction
- └── README–Chinepse.md → Chinese introduction
- └── LICENSE → License
- └── Nameplate → BC-809-Nameplate

---

## Environment Requirements

- **Python 3.6+** (recommended 3.9+)
- Operating System: Linux, Windows, macOS, Android (Termux)
- Dependencies: `git` for cloning the repository, `figlet` for generating ASCII art banners

## License
- This repository uses `GPLv3` as its open-source license.
