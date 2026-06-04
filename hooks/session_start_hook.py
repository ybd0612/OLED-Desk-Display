"""
Session Start Hook - Inject OLED reminder at the beginning of each conversation.
Outputs a system message to remind the model to push summary to OLED at the end.
"""

import json
import sys

def main():
    # This system message will be injected into the conversation
    system_message = """⚠️ OLED SCREEN REMINDER:
You have an OLED screen connected via serial (COM3).
At the END of this conversation, you MUST run:
python "C:\\Users\\ybd06\\Documents\\project\\pm\\python\\conversation_hook.py" "标题" "第一行" "第二行" "第三行"
- Title: max 10 Chinese chars / 20 English chars (what was done)
- Body: 1-3 lines, each max 10 Chinese chars / 20 English chars (key results)
This is MANDATORY. Do not forget."""
    
    output = {
        "continue": True,
        "systemMessage": system_message,
        "suppressOutput": False
    }
    
    print(json.dumps(output))


if __name__ == "__main__":
    main()