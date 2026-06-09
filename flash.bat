@echo off
chcp 65001 >nul 2>&1
title Flash OLED Firmware

echo ========================================
echo   One-click Arduino Flash
echo ========================================
echo.

set CLI="C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe"
set SKETCH=%~dp0arduino\sketch_jun4a\sketch_jun4a.ino
set FQBN=esp8266:esp8266:generic
set PORT=COM3

echo [1/3] Compiling... (first time may take 2-3 minutes)
%CLI% compile --fqbn %FQBN% "%SKETCH%"
if errorlevel 1 (
    echo.
    echo [FAIL] Compile failed!
    pause
    exit /b 1
)
echo [OK] Compiled

echo.
echo [2/3] Uploading to %PORT%...
%CLI% upload -p %PORT% --fqbn %FQBN% "%SKETCH%"
if errorlevel 1 (
    echo.
    echo [FAIL] Upload failed! Check USB connection.
    pause
    exit /b 1
)

echo.
echo [3/3] Done!
echo [OK] Firmware uploaded to %PORT%
echo.
echo You can now run start_oled_canvas.bat
pause
