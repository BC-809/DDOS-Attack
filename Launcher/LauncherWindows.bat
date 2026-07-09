@echo off
setlocal enabledelayedexpansion
title DDOS-Attack Environment Setup

:: Check for administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo This script requires Administrator privileges. Please run as Administrator.
    pause
    exit /b 1
)

echo ================================================================
echo  DDOS-Attack Educational Setup
echo  WARNING: Use only in isolated lab with your own devices!
echo ================================================================
pause

:: 1. Install Python
echo [*] Installing Python 3.12...
winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements
if %errorlevel% neq 0 (
    echo [!] Python installation failed. Please install manually and re-run this script.
    pause
    exit /b 1
)
echo [*] Python installation finished.

:: Refresh PATH to include Python
for /f "delims=" %%i in ('where python 2^>nul') do set PYTHON_EXE=%%i
if not defined PYTHON_EXE (
    echo [!] Python executable not found in PATH. Please restart the script or install Python manually.
    pause
    exit /b 1
)
echo [*] Python found: %PYTHON_EXE%

:: 2. Install Git
echo [*] Installing Git...
winget install Git.Git --accept-source-agreements --accept-package-agreements
if %errorlevel% neq 0 (
    echo [!] Git installation failed. Please install Git manually and re-run this script.
    pause
    exit /b 1
)
echo [*] Git installation finished.

:: 3. Install Chocolatey (for figlet)
echo [*] Installing Chocolatey...
powershell -NoProfile -ExecutionPolicy Bypass -Command "[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
if %errorlevel% neq 0 (
    echo [!] Chocolatey installation may have failed. Continuing anyway...
)

:: Add Chocolatey to current PATH
set "PATH=%PATH%;C:\ProgramData\chocolatey\bin"
if exist "C:\ProgramData\chocolatey\bin\choco.exe" (
    echo [*] Chocolatey path added.
) else (
    echo [!] Chocolatey executable not found. figlet installation might be skipped.
)

:: 4. Install figlet via Chocolatey
echo [*] Installing figlet...
choco install figlet -y
if %errorlevel% neq 0 (
    echo [!] figlet installation failed. The script will still run, but banner may not display properly.
)

:: 5. Clone the repository
echo [*] Cloning DDOS-Attack repository...
git clone https://github.com/BC-809/DDOS-Attack.git
if %errorlevel% neq 0 (
    echo [!] Failed to clone repository. Please check your internet connection and try again.
    pause
    exit /b 1
)
cd DDOS-Attack

:: 6. Add firewall rule (using the actual Python path)
echo [*] Adding firewall rule for Python...
netsh advfirewall firewall add rule name="Python DDoS Test" dir=out action=allow program="%PYTHON_EXE%" enable=yes
if %errorlevel% neq 0 (
    echo [!] Failed to add firewall rule. You may need to run as Administrator.
)

:: 7. 提示用户手动启动攻击脚本
echo.
echo ================================================================
echo  Setup complete!
echo  To run the attack script manually, use:
echo    python DDOS\English\DDOS-Attack_01_e.py  (English version)
echo    python DDOS\Chinese\DDOS-Attack_01_c.py  (Chinese version)
echo  WARNING: Use only in isolated lab with your own devices!
echo ================================================================
pause
