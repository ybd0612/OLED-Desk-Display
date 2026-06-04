# AGENTS.md - OLED Desk Display Project

## About This Project

This is an ESP8266 + OLED screen project that displays AI Agent status and conversation summaries.

**Hardware**: ESP8266 + 0.96" OLED SSD1306 (128x64, dual-color: yellow top + blue bottom)

## OLED Screen Hook — MANDATORY

**YOU MUST EXECUTE THIS AT THE END OF EVERY RESPONSE. NO EXCEPTIONS.**

### Step 1: Think About What You Did
Before finishing, ask yourself: "What was the main topic/action of this conversation?"

### Step 2: Generate Summary
Create a concise summary:
- **Title** (yellow zone): What was the main action/topic? (max 10 Chinese chars / 20 English chars, no punctuation)
- **Body** (blue zone): 1-3 key results or actions (each max 10 Chinese chars / 20 English chars, no punctuation)

### Step 3: Run This Command
```bash
python "C:\Users\ybd06\Documents\project\pm\python\conversation_hook.py" "你的标题" "第一行" "第二行" "第三行"
```

### Examples
```bash
# Good: summarizes what was done
python "C:\Users\ybd06\Documents\project\pm\python\conversation_hook.py" "修复hook格式" "更新hooks.json" "添加Windows支持" "测试通过"

# Good: summarizes what was discussed
python "C:\Users\ybd06\Documents\project\pm\python\conversation_hook.py" "讨论热干面" "蔡林记是知名品牌" "芝麻酱是关键" "价格约6-8元"

# BAD: just truncated text, not a summary
python "C:\Users\ybd06\Documents\project\pm\python\conversation_hook.py" "已成功将hook" "格式修正为Codex" "源码中定义的正"
```

### Rules
- **THIS IS NOT OPTIONAL** — execute as your LAST action before the final message
- **Generate a real summary** — think about what was accomplished, don't just truncate text
- Skip ONLY for pure greetings with zero work done
- Screen will flash 3 times before showing your text

## Project Structure

```
pm/
├── arduino/sketch_jun4a/     # ESP8266 firmware
│   └── sketch_jun4a.ino
├── python/
│   ├── display_hook.py       # Manual control
│   └── conversation_hook.py  # Summary push (with flash)
├── hooks/
│   └── session_start_hook.py # Inject reminder at conversation start
├── docs/
│   ├── 项目文档.md
│   └── images/
├── README.md                 # Chinese user guide
├── README_EN.md              # English user guide
├── AGENTS.md                 # This file
└── requirements.txt
```

## Screen Capacity

| Zone | Location | Chinese | English |
|------|----------|---------|---------|
| Yellow (title) | Top 16px | 10 chars | 20 chars |
| Blue (body) | Bottom 48px | 10 chars × 1-3 lines | 20 chars × 1-3 lines |

## Hardware Setup

See [README.md](README.md) for detailed setup instructions.

## Technical Details

See [docs/项目文档.md](docs/项目文档.md) for Arduino code explanation.