@echo off
chcp 65001 >nul 2>&1
title OLED Web Canvas

echo ========================================
echo   OLED Web Canvas
echo ========================================
echo.

:SCAN
echo [scan] Detecting ESP8266...

python -c "import serial.tools.list_ports; ports=[p for p in serial.tools.list_ports.comports() if any(k in (p.description or '').lower() for k in ['ch340','ch341','cp210','ftdi','usb-serial','usb serial','silicon labs'])]; print(ports[0].device if ports else '')" > "%temp%\esp_port.txt" 2>nul
set /p ESP_PORT=<"%temp%\esp_port.txt"
del "%temp%\esp_port.txt" >nul 2>&1

if "%ESP_PORT%"=="" (
    echo [wait] ESP8266 not found, retry in 5s...
    timeout /t 5 /nobreak >nul
    goto SCAN
)

echo [ok] Found %ESP_PORT%
echo [start] Launching Web server...

python "%~dp0python\web_server.py"

echo.
echo [exit] Web server stopped.
pause
