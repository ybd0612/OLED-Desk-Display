# 🖥️ AI Agent Desktop OLED Display — Beginner Guide

> A small OLED screen for your desk that shows your AI Agent status in real-time (Working / Success / Failed).
> 
> No programming experience needed — just follow the steps below!

**[中文版本](README.md)** | **[Technical Documentation](docs/项目文档.md)**

---

## What You Need

| Item | Description | Price |
|------|-------------|-------|
| ESP8266 Board | With built-in 0.96" OLED screen ([Buy on Taobao](https://e.tb.cn/h.RhEO5NmkXbNigtq?tk=HTlngZy42Jn) / search "ESP8266 OLED board" on AliExpress) | ~$3-5 |
| Micro USB Data Cable | For connecting to PC (make sure it supports data, not just charging) | ~$1 |
| A Computer | Windows or Mac | - |

---

## Step 1: Download the Project

1. Click the green **Code** button at the top of this page → **Download ZIP**
2. Extract to any folder on your computer (e.g. Desktop)
3. Remember the folder path for later steps

---

## Step 2: Install Arduino IDE

### 2.1 Download Arduino IDE

Open: **https://www.arduino.cc/en/software**

1. Click **Windows Win 10 and newer** (for Windows 10/11)
2. For Mac, select the macOS version
3. Double-click to install, click Next through the wizard

### 2.2 Add ESP8266 Support

1. Open Arduino IDE
2. Click **File** → **Preferences**
3. Find **Additional Boards Manager URLs** field
4. Paste this URL:
   ```
   http://arduino.esp8266.com/stable/package_esp8266com_index.json
   ```
5. Click **OK**

### 2.3 Install ESP8266 Package

1. Click the **"Puzzle Piece" icon** in the left sidebar (Boards Manager)
2. Search: `esp8266`
3. Find **esp8266 by ESP8266 Community**, click **Install**
4. Wait until it shows **Installed** (may take 1-2 minutes)

---

## Step 3: Install Display Library

1. Click the **"Bookshelf" icon** in the left sidebar (Library Manager)
2. Search: `U8g2`
3. Find **U8g2 by oliver**, click **Install**
4. If prompted to install dependencies, click **"Install all"**

---

## Step 4: Upload Program to Board

### 4.1 Connect Board to PC

Plug the Micro USB cable from the board to your computer.

> ⚠️ Some cables only support charging! If your PC doesn't detect the board, try a different cable.

### 4.2 Verify Connection

1. Right-click **"This PC"** → **Manage** → **Device Manager**
2. Expand **"Ports (COM & LPT)"**
3. You should see something like **USB-SERIAL CH340 (COM3)**
4. Note the **COM number** (e.g., COM3) — you'll need it later

### 4.3 Configure Board Settings

In Arduino IDE top dropdown menus:

1. **Board**: Select **Generic ESP8266 Module**
2. **Port**: Select the **COM port** you found above

### 4.4 Upload Code

1. Open `arduino/sketch_jun4a/sketch_jun4a.ino` from the extracted project folder
2. Click the **👉 Upload arrow** in the top-left
3. Wait for `Done uploading.` — you're done! 🎉

> During upload, the board's LED will blink rapidly — this is normal.

---

## Step 5: Install Python

### 5.1 Install Python

1. Open **https://www.python.org/downloads/**
2. Click **Download Python 3.x.x**
3. **Important: Check "Add Python to PATH"** during installation!
4. Click Install

### 5.2 Install Dependencies

Open Command Prompt (`Win + R` → `cmd` → Enter), navigate to the project folder, type:

```bash
pip install -r requirements.txt
```

### 5.3 Configure COM Port

Open `python/display_hook.py` with Notepad, find:

```python
SERIAL_PORT = 'COM3'
```

Change `COM3` to your actual COM number, save.

> 💡 If you want the conversation summary hook, also update the same line in `python/conversation_hook.py`.

---

## Step 6: Start Using! 🎉

Open Command Prompt, navigate to the project folder, then:

```bash
# 🟡 Standby (shows: Ybond + STANDBY)
python python/display_hook.py WAIT

# 🟢 Success (shows: Ybond + SUCCESS)
python python/display_hook.py SUCCESS

# 🔴 Failed (shows: Ybond + FAIL)
python python/display_hook.py FAIL

# ✏️ Custom text (yellow zone | blue zone)
python python/display_hook.py "Ybond|Hello"

# ✏️ Single line (shows in blue zone)
python python/display_hook.py hello
```

---

## Advanced: Conversation Summary Hook

Push title and summary to screen after each conversation:

```bash
# Title + multi-line summary (one arg per line)
python python/conversation_hook.py "Project Done" "Code uploaded" "Tests passed" "Docs written"

# Title + summary (single line)
python python/conversation_hook.py "Project Done" "Code uploaded" 
```

> 💡 Title max: 10 Chinese chars / 20 English chars. Summary max: 3 lines, each 10 Chinese / 20 English chars. No truncation — keep text within limits.
>
> When triggered by Hook, the screen flashes white/black 3 times before showing text — so you won't miss it. Manual sends via display_hook.py won't flash.

---

## Customize Default Text

Open `arduino/sketch_jun4a/sketch_jun4a.ino`, find:

```cpp
const char* DEF_TOP = "Ybond";      // Yellow zone text
const char* DEF_BOT = "STANDBY";    // Blue zone text
```

Change to whatever you want, then re-upload.

---

## FAQ

### Q: Upload error "COM port busy"
**A:** Close Arduino IDE Serial Monitor if open. Only one program can use the serial port at a time.

### Q: Upload succeeded but screen is blank
**A:** Make sure your board has a built-in OLED screen. If not, you need to wire SCL→D6 and SDA→D5.

### Q: Python says "Cannot connect to hardware"
**A:** Check your COM number, close Serial Monitor, or reconnect the USB cable.

### Q: Chinese characters not showing
**A:** Make sure you uploaded the latest code from `arduino/sketch_jun4a/sketch_jun4a.ino`.

### Q: Compilation hangs forever
**A:** U8g2 library not installed. Go to Library Manager and install it.

---

## Project Files

| File | Purpose |
|------|---------|
| `arduino/sketch_jun4a/sketch_jun4a.ino` | Program to upload to the board (one-time) |
| `python/display_hook.py` | Run on PC to send messages to screen (daily use) |
| `python/conversation_hook.py` | Conversation summary hook |
| `hooks/codex_stop_hook.py` | Codex auto-trigger hook on conversation end |
| `AGENTS.md` | Codex hook configuration file |
| `requirements.txt` | Python dependencies |
| `docs/项目文档.md` | Technical details and development log |

---

## More Info

- [中文版本 (Chinese Version)](README.md)
- [Technical Documentation](docs/项目文档.md)