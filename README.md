**中文** (**简体**, [繁體](C-README.md)

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
- │ └── DDOS-Attack_01.py → Attack code file
- │ └── DDOS-Attack_02.py → Quick version (skips ASCII art loading)
- │ └── DDOS-Attack_03.py → Version with spoofed source IP support (requires ROOT privileges)
- ├── Launcher/
- │ └── 01_UseWindows.bat → Windows launcher (installs dependencies and runs 01)
- │ └── 01_UsePython.py → Python launcher (installs dependencies and runs 01)
- │ └── 01_UseLinux → Linux launcher (installs dependencies and runs 01)
- ├── Art/
- │ └── Nameplate → DDoS ASCII art
- │ └── Figlet → Preview of figlet fonts generated in the code
- └── README.md → Introduction

---

## Environment Requirements

- **Python 3.6+** (recommended 3.9+)
- Operating System: Linux, Windows, macOS, Android (Termux)
- Dependencies: `git` for cloning the repository, `figlet` for generating ASCII art banners
