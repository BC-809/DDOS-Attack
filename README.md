[中文](README-Chinese.md)

# DDOS-Attack – Distributed Denial of Service Simulation Tool

## Strict Legal & Ethical Warning

- **This project is for educational purposes only!** It is intended to help security researchers, network administrators, and students understand the principles of DDoS attacks in order to design better defense strategies.

- **Launching an attack against any server, network, or device that you do not personally own, without authorization, is a serious criminal offense and will be severely punished by law.**

- **Please ensure that you only run this code in an isolated, controlled laboratory environment (e.g., local virtual machines, private test networks) that you fully control.** The author assumes no responsibility for any misuse.

---

## Project Description

- `DDOS-Attack` is a Python‑based DDoS simulation script that sends UDP flood packets to a specified IP address and port.

---

## Key Features
- Clean command‑line interactive interface
- Customizable target IP, port, and total traffic volume
- Automatic reachability check before launching the attack (avoids useless attacks)
- Retains an ASCII art startup screen (requires `figlet` support)

---

## Project Structure
- ├── DDOS/
- │ └── DDOS-Attack_01.py → Main attack code
- │ └── DDOS-Attack_02.py → Lightweight version (no art fonts)
- │ └── DDOS-Attack_03.py → Source‑IP spoofing version (requires ROOT privileges)
- ├── Launcher/
- │ └── 01_UseWindows.bat → Windows runner (installs dependencies and launches 01)
- │ └── 01_UsePython.py → Python runner (installs dependencies and launches 01)
- │ └── 01_UseLinux → Linux runner (installs dependencies and launches 01)
- ├── Art/
- │ └── Nameplate → DDoS ASCII art
- │ └── Figlet → Preview of figlet fonts used in the code
- └── README.md → This file

---

## Requirements

- **Python 3.6+** (3.9+ recommended)
- Operating system: Linux, Windows, macOS, Android (Termux)
- Required tools: `git` (to clone the repository), `figlet` (for the ASCII art banner)

## License

- This repository is released under the `GPLv3` open source license.
