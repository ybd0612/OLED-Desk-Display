# AGENTS.md - OLED Desk Display Project

## About This Project

This is an ESP8266 + OLED screen project that displays AI Agent status and conversation summaries.

**Hardware**: ESP8266 + 0.96" OLED SSD1306 (128x64, dual-color: yellow top + blue bottom)

## OLED Screen Hook — MANDATORY

**At the END of every conversation, you MUST push a summary to the OLED screen.**

### Step 1: Generate Summary
- **Title** (yellow zone, max 10 Chinese chars / 20 English chars): Main topic/action
- **Body** (blue zone, exactly 3 lines, each max 10 Chinese chars / 20 English chars): Key results

### Step 2: Run This Command
```bash
python "C:\Users\ybd06\Documents\project\pm\python\conversation_hook.py" "标题" "第一行" "第二行" "第三行"
```

### Example
```bash
python "C:\Users\ybd06\Documents\project\pm\python\conversation_hook.py" "修复hook格式" "更新hooks.json" "添加Windows支持" "测试通过"
```

### Rules
- **MUST execute** — this is not optional
- Skip ONLY for pure greetings with zero work done
- Screen will flash 3 times before showing text
- All text must fit within limits — no "..." truncation

## Project Structure

```
pm/
├── arduino/sketch_jun4a/  # ESP8266 firmware
│   └── sketch_jun4a.ino
├── python/
│   ├── display_hook.py      # Manual control (python display_hook.py "text")
│   └── conversation_hook.py # Summary push (python conversation_hook.py "title" "line1" "line2")
├── hooks/
│   ├── session_start_hook.py  # Inject OLED reminder at conversation start
│   └── codex_stop_hook.py     # Backup: auto-extract summary at conversation end
├── docs/
│   ├── 项目文档.md           # Chinese technical docs
│   └── images/               # Product images
├── README.md                 # Chinese user guide
├── README_EN.md              # English user guide
├── AGENTS.md                 # This file
└── requirements.txt          # Python dependencies
```

## Screen Capacity

| Zone | Location | Chinese | English |
|------|----------|---------|---------|
| Yellow (title) | Top 16px | 10 chars | 20 chars |
| Blue (body) | Bottom 48px | 10 chars × 3 lines | 20 chars × 3 lines |

## Hardware Setup

See [README.md](README.md) for detailed hardware setup instructions.

## Technical Details

See [docs/项目文档.md](docs/项目文档.md) for Arduino code explanation and customization.