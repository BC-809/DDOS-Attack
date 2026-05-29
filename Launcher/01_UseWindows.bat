@echo off
title DDOS-Attack Environment Setup & Run
echo ================================================================
echo  DDOS-Attack Educational Setup & Run
echo  WARNING: Use only in isolated lab with your own devices!
echo ================================================================
pause

:: 1. Install Python
echo [*] Installing Python 3.12...
winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements
echo [*] Python installation done. Please restart this script if needed.

:: 2. Install Git
echo [*] Installing Git...
winget install Git.Git --accept-source-agreements --accept-package-agreements

:: 3. Install Chocolatey (for figlet)
echo [*] Installing Chocolatey...
powershell -NoProfile -ExecutionPolicy Bypass -Command "[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"

:: 4. Install figlet via Chocolatey
echo [*] Installing figlet...
choco install figlet -y

:: 5. Clone the repository
echo [*] Cloning DDOS-Attack repository...
git clone https://github.com/BC-809/DDOS-Attack.git
cd DDOS-Attack

:: 6. Add firewall rule (adjust Python path if needed)
echo [*] Adding firewall rule for Python...
set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
netsh advfirewall firewall add rule name="Python DDoS Test" dir=out action=allow program="%PYTHON_EXE%" enable=yes

:: 7. Run the attack script
echo.
echo ================================================================
echo  Setup complete! Launching DDOS-Attack script...
echo ================================================================
python DDOS/DDOS-Attack_01.py

:: If the above command fails, try using the full Python path:
:: "%PYTHON_EXE%" 01/DDOS-Attack_01.py

pause
