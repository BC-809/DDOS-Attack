Tutorial: Running a DDoS Simulation on Android with Termux + Kali Linux (via proot-distro)

🚨 Strict Legal & Ethical Warning

This guide is for educational purposes only. It demonstrates how to set up a testing environment to understand how DDOS tools work so you can better defend against them.

Launching a DDOS attack against any network, server, or website you do not own and have explicit written permission to test is a serious crime.

Only run these commands and scripts on your own isolated lab environment (e.g. a local virtual machine).

---

1. Environment Setup

1.1. Install Termux

1. Download the APK: Open your phone browser and go to the F-Droid website to download the latest Termux APK. Do not install from Google Play – that version is outdated and broken.
2. Install: Tap the downloaded APK file. If prompted, allow installation from unknown sources.

1.2. Initialise Termux

Open Termux and run:

```bash
pkg update && pkg upgrade -y
```

If the download speed is very slow, switch to a faster mirror:

```bash
termux-change-repo
```

In the graphical menu, select Mirrors in China (or choose a mirror close to your location), then OK.

2. Install Kali Linux (Debian) inside Termux

2.1. Install proot-distro

This tool lets you run Linux distributions without rooting your device.

```bash
pkg install proot-distro -y
```

2.2. Install Debian

Kali Linux is based on Debian. We install Debian first, then turn it into a Kali‑like environment.

```bash
proot-distro install debian
```

2.3. Start and prepare Kali (Debian)

1. Log in:
   ```bash
   proot-distro login debian
   ```
   Your prompt should change to something like root@localhost:~#.
2. Update and install essential tools:
   ```bash
   apt update && apt full-upgrade -y
   apt install python3 git figlet -y
   ```

Note: You may see harmless errors related to pipewire or kali-desktop-xfce. These are caused by Termux’s limited permissions and can be ignored. They do not affect Python or git.

3. Run the DDoS Simulation Script

3.1. Clone the script repository

```bash
git clone https://github.com/BC-809/DDOS-Attack.git
```

3.2. Execute the script

```bash
cd DDOS-Attack
python3 01/DDOS-Attack_01.py
```

If the figlet banner looks broken, install the figlet package (you may have already done this):

```bash
apt install figlet -y
```

3.3. How to use the script

1. When prompted with IP Target :, enter the IP address of a device you own and have permission to test (e.g. a virtual machine on your local network).
2. The script will start sending packets and print status messages.
3. To stop the script, press Ctrl + C (on Termux, the Ctrl key is available on the extra keys bar).

4. Troubleshooting

· “figlet: inaccessible or not found”: install figlet with apt install figlet -y.
· Font / banner looks garbled: This usually happens when the terminal is too narrow. Rotate your phone to landscape mode, or edit the script to use a smaller font (figlet -f small).
· Repository errors (404): Run termux-change-repo and pick a different mirror, or manually edit your sources list.

5. Quick Reference – Start the environment next time

After you have installed everything, next time you just need:

```bash
proot-distro login debian
cd /root/DDOS-Attack
python3 01/DDOS-Attack_01.py
```

---

Never use these techniques against unauthorised targets.
Understanding attack vectors is the first step to building better defences. Use this knowledge responsibly.
