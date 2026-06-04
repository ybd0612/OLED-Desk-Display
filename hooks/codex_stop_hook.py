"""
Codex Stop Hook — 对话结束时自动推送摘要到 OLED 屏幕

Codex 在每次对话结束时会通过 stdin 传入对话摘要文本。
本脚本解析摘要，提取标题和摘要行，调用 conversation_hook.py 推送到屏幕。

hooks.json 配置（~/.codex/hooks.json）：
{
  "stop": [
    {
      "command": "python",
      "args": ["C:\\你的路径\\pm\\hooks\\codex_stop_hook.py"],
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
    # 从 stdin 读取 Codex 传入的摘要
    summary = ""
    try:
        summary = sys.stdin.read().strip()
    except Exception:
        pass

    if not summary:
        # 没有摘要内容，显示等待状态
        subprocess.run(
            ['python', DISPLAY_HOOK, 'WAIT'],
            capture_output=True, timeout=10
        )
        return

    # 解析摘要：期望格式为 "标题\n摘要第一行\n第二行\n第三行"
    # 或者纯文本（全部当作一行摘要）
    lines = [line.strip() for line in summary.split('\n') if line.strip()]

    if len(lines) >= 2:
        # 第一行作为标题，其余作为摘要行（最多3行）
        title = lines[0][:10]  # 截断到10个中文字符以内
        body_lines = lines[1:4]  # 最多3行
    elif len(lines) == 1:
        # 只有一行：拆分标题和摘要
        text = lines[0]
        if len(text) <= 10:
            title = text
            body_lines = ["OK"]
        else:
            # 前10字做标题，剩余做摘要
            title = text[:10]
            body_lines = [text[10:20]]  # 再取10字作为摘要
    else:
        title = "AI Agent"
        body_lines = ["STANDBY"]

    # 调用 conversation_hook.py 发送到屏幕
    args = ['python', CONVERSATION_HOOK, title] + body_lines
    subprocess.run(args, capture_output=True, timeout=15)


if __name__ == '__main__':
    main()