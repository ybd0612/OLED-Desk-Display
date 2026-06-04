"""
Codex Stop Hook - 对话结束时自动推送摘要到 OLED 屏幕

安装方法：
  1. 将此文件路径添加到 Codex 全局配置 ~/.codex/hooks.json
  2. 确保 Python 和 pyserial 已安装

hooks.json 示例：
{
  "stop": [
    {
      "command": "python",
      "args": ["C:\\你的项目路径\\pm\\hooks\\codex_stop_hook.py"],
      "timeout": 15
    }
  ]
}
"""
import subprocess
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
CONVERSATION_HOOK = os.path.join(PROJECT_DIR, 'python', 'conversation_hook.py')
DISPLAY_HOOK = os.path.join(PROJECT_DIR, 'python', 'display_hook.py')


def main():
    summary = ""
    try:
        summary = sys.stdin.read().strip()
    except:
        pass

    if summary:
        subprocess.run(['python', CONVERSATION_HOOK, summary],
                      capture_output=True, timeout=15)
    else:
        subprocess.run(['python', DISPLAY_HOOK, 'WAIT'],
                      capture_output=True, timeout=10)


if __name__ == '__main__':
    main()