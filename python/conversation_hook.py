"""
============================================================
 AI Agent 对话摘要 Hook - 自动推送到 OLED 屏幕
============================================================

功能：
    接收对话内容，生成符合屏幕字数限制的标题和摘要，推送到 OLED 屏幕。
    不截断、不加"..."，要求大模型直接输出符合限制的完整文字。

屏幕容量限制：
    黄色区域（上）：中文 10 字 / 英文 20 字符（单行）
    蓝色区域（下）：中文 10 字/行 × 3 行 = 30 字
                    英文 20 字符/行 × 3 行 = 60 字符

用法 1：手动输入标题和摘要（自动检查字数）
    python conversation_hook.py "标题" "摘要内容"

用法 2：传入对话内容，输出 Prompt 让大模型生成摘要
    python conversation_hook.py --prompt "对话内容..."
    这会输出一个 Prompt，你可以发给 ChatGPT/Claude 让它生成摘要，
    然后再用方式 1 发送到屏幕。

用法 3：直接从 stdin 读取对话内容（管道模式）
    echo "对话内容" | python conversation_hook.py --stdin

============================================================
"""

import os
import serial
import sys
import time


# ============================================================
# 配置区
# ============================================================
SERIAL_PORT = 'COM3'
BAUD_RATE = 9600

# 屏幕容量
TITLE_MAX = 10        # 黄色区域：最多 10 个中文字（或 20 个英文字母）
BODY_MAX_PER_LINE = 10  # 蓝色区域：每行最多 10 个中文字
BODY_MAX_LINES = 3      # 蓝色区域：最多 3 行
BODY_MAX_TOTAL = BODY_MAX_PER_LINE * BODY_MAX_LINES  # 总共 30 个中文字

AGENTS_FLAG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.agents_enabled')

def is_agents_enabled():
    """检查Agents开关文件是否存在且内容为1"""
    try:
        with open(AGENTS_FLAG_FILE, 'r') as f:
            return f.read().strip() == '1'
    except FileNotFoundError:
        # 文件不存在默认开启
        return True


# ============================================================
# Prompt 模板 - 要求大模型生成符合屏幕限制的摘要
# ============================================================
SUMMARY_PROMPT = """你是一个信息压缩专家。请根据下面的对话内容，生成两个东西：

1. **标题**（显示在小屏幕上黄色区域）：
   - 严格不超过 {title_max} 个中文字（或 {title_max_en} 个英文字母）
   - 要简洁概括这次对话的核心主题
   - 不能有标点符号

2. **摘要**（显示在小屏幕蓝色区域）：
   - 严格不超过 {body_total} 个中文字（或 {body_total_en} 个英文字母）
   - 分成最多 {body_lines} 行，每行不超过 {body_per_line} 个中文字
   - 用换行符分隔每一行
   - 内容要完整表达对话的关键结论，不能省略号结尾
   - 不能有标点符号

请严格按以下格式输出，不要加任何其他文字：
标题：xxx
摘要：第一行
第二行
第三行

注意：每个字都要算清楚，宁可少写也不能超限。如果内容复杂，请精炼概括，确保完整。

对话内容：
{conversation}
"""


def get_char_width(char):
    """判断一个字符的显示宽度：中文=2，英文=1"""
    if ('\u4e00' <= char <= '\u9fff' or
        '\u3000' <= char <= '\u303f' or
        '\uff00' <= char <= '\uffef' or
        ord(char) > 0x7F):
        return 2
    return 1


def get_text_width(text):
    """计算文本总显示宽度"""
    return sum(get_char_width(c) for c in text)


def check_and_warn(text, max_width, label):
    """检查文本是否超宽，超宽则警告"""
    width = get_text_width(text)
    if width > max_width:
        cn_limit = max_width // 2
        print(f"[警告] {label} 超出屏幕！当前 {width} 宽度（约{width//2}个中文字），限制 {max_width} 宽度（{cn_limit}个中文字）")
        print(f"  内容：{text}")
        print(f"  建议：精简到 {cn_limit} 个中文字以内")
        return False
    return True


def send_to_screen(title, body_lines):
    """
    将标题和摘要发送到 OLED 屏幕

    Args:
        title (str): 标题（黄色区域，单行）
        body_lines (list): 摘要行列表（蓝色区域，最多3行）
    """
    # 检查Agents开关
    if not is_agents_enabled():
        print("[跳过] Agents开关已关闭，不发送到屏幕")
        return False

    # 检查标题
    check_and_warn(title, TITLE_MAX * 2, "标题")

    # 检查每行摘要
    for i, line in enumerate(body_lines):
        check_and_warn(line, BODY_MAX_PER_LINE * 2, f"摘要第{i+1}行")

    # 用竖线分隔，蓝色区域用换行
    body_text = chr(0x1E).join(body_lines)
    command = chr(0x1C) + title + chr(0x1F) + body_text

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(1.5)
        data = (command + '\n').encode('utf-8')
        ser.write(data)
        ser.close()

        # 创建标记文件，表示已调用
        marker_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".hook_called")
        with open(marker_file, "w") as f:
            f.write(str(time.time()))
        print(f"[成功] 已推送到屏幕")
        print(f"  黄色区域（标题）: {title} ({get_text_width(title)}宽度)")
        for i, line in enumerate(body_lines):
            print(f"  蓝色区域第{i+1}行: {line} ({get_text_width(line)}宽度)")
        return True
    except Exception as e:
        print(f"[失败] 无法连接屏幕: {e}")
        return False


def parse_ai_response(response_text):
    """
    解析大模型返回的摘要结果

    Expected format:
        标题：xxx
        摘要：第一行
        第二行
        第三行
    """
    lines = response_text.strip().split('\n')

    title = ""
    body_lines = []

    in_summary = False
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("标题：") or line.startswith("标题:"):
            title = line.split("：", 1)[-1].split(":", 1)[-1].strip()
            in_summary = False
        elif line.startswith("摘要：") or line.startswith("摘要:"):
            first_body = line.split("：", 1)[-1].split(":", 1)[-1].strip()
            if first_body:
                body_lines.append(first_body)
            in_summary = True
        elif in_summary:
            body_lines.append(line)

    # 确保不超过3行
    body_lines = body_lines[:BODY_MAX_LINES]

    return title, body_lines


def generate_prompt(conversation_text):
    """生成让大模型总结的 Prompt"""
    return SUMMARY_PROMPT.format(
        title_max=TITLE_MAX,
        title_max_en=TITLE_MAX * 2,
        body_total=BODY_MAX_TOTAL,
        body_total_en=BODY_MAX_TOTAL * 2,
        body_lines=BODY_MAX_LINES,
        body_per_line=BODY_MAX_PER_LINE,
        conversation=conversation_text
    )


# ============================================================
# 主入口
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] != "--prompt" and sys.argv[1] != "--stdin":
        # 模式 1: 手动输入标题和摘要
        # python conversation_hook.py "标题" "摘要第一行" "摘要第二行"
        title = sys.argv[1]
        body_lines = sys.argv[2:]
        send_to_screen(title, body_lines)

    elif len(sys.argv) == 2 and not sys.argv[1].startswith("--"):
        # 模式 1b: 竖线分隔
        # python conversation_hook.py "标题|第一行|第二行"
        parts = sys.argv[1].split("|")
        title = parts[0].strip()
        body_lines = [p.strip() for p in parts[1:] if p.strip()]
        if not body_lines:
            body_lines = ["..."]
        send_to_screen(title, body_lines)

    elif len(sys.argv) >= 2 and sys.argv[1] == "--prompt":
        # 模式 2: 生成 Prompt
        # python conversation_hook.py --prompt "对话内容..."
        conversation = " ".join(sys.argv[2:])
        prompt = generate_prompt(conversation)
        print(prompt)

    elif len(sys.argv) >= 2 and sys.argv[1] == "--stdin":
        # 模式 3: 从 stdin 读取
        conversation = sys.stdin.read()
        prompt = generate_prompt(conversation)
        print(prompt)

    else:
        print("=" * 55)
        print(" AI Agent 对话摘要 Hook - OLED 屏幕推送")
        print("=" * 55)
        print()
        print("模式 1: 手动发送（检查字数）")
        print('  python conversation_hook.py "标题" "摘要第一行" "第二行"')
        print('  python conversation_hook.py "标题|第一行|第二行"')
        print()
        print("模式 2: 生成 Prompt 让大模型总结")
        print('  python conversation_hook.py --prompt "这里粘贴对话内容"')
        print()
        print("模式 3: 管道输入")
        print('  echo "对话内容" | python conversation_hook.py --stdin')
        print()
        print("屏幕容量:")
        print(f"  标题（黄色区域）: 最多 {TITLE_MAX} 个中文字 / {TITLE_MAX*2} 个英文字母")
        print(f"  摘要（蓝色区域）: 每行 {BODY_MAX_PER_LINE} 个中文字 × {BODY_MAX_LINES} 行 = 共 {BODY_MAX_TOTAL} 个中文字")
        print()
        print("字数规则: 不截断、不加'...', 要求大模型直接输出符合限制的完整文字")
