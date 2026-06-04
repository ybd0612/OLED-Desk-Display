"""
Codex Stop Hook - OLED Screen Backup
Simple extraction when AGENTS.md instruction is missed.
"""

import subprocess
import sys
import os
import json
import re
import serial
import time
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
LOG_FILE = os.path.join(SCRIPT_DIR, 'hook_debug.log')
SERIAL_PORT = 'COM3'
BAUD_RATE = 9600
SEP_ZONE = chr(0x1F)
SEP_LINE = chr(0x1E)


def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        safe = str(msg).encode('utf-8', errors='replace').decode('utf-8')
    except:
        safe = repr(msg)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f'[{ts}] {safe}\n')


def read_stdin():
    raw_bytes = sys.stdin.buffer.read()
    for enc in ['utf-8', 'gbk', 'gb2312', 'cp936', 'latin-1']:
        try:
            return raw_bytes.decode(enc)
        except:
            continue
    return raw_bytes.decode('utf-8', errors='replace')


def truncate_cjk(text, max_width):
    w = 0
    for i, c in enumerate(text):
        cw = 2 if ord(c) > 0x7F else 1
        if w + cw > max_width:
            return text[:i]
        w += cw
    return text


def extract_summary(message):
    """Simple extraction: first heading + first 3 bullet points"""
    lines = message.split('\n')
    clean = []
    for line in lines:
        t = line.strip()
        if not t or t.startswith('```') or re.match(r'^-{3,}$', t):
            continue
        t = re.sub(r'^#{1,6}\s+', '', t)
        t = t.replace('**', '').replace('*', '')
        t = re.sub(r'^[-*+]\s+', '', t)
        if t:
            clean.append(t)
    
    if not clean:
        return "AI Agent", ["STANDBY"]
    
    title = clean[0]
    body = clean[1:4] if len(clean) > 1 else ["OK"]
    return title, body


def main():
    raw = read_stdin().strip()
    if not raw:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            time.sleep(1.5)
            ser.write(b'WAIT\n')
            ser.close()
        except:
            pass
        return

    summary = ""
    try:
        data = json.loads(raw)
        summary = data.get('last_assistant_message', '')
    except:
        summary = raw

    if not summary:
        return

    title, body = extract_summary(summary)
    title = truncate_cjk(title, 20)
    body = [truncate_cjk(l, 20) for l in body]
    
    body_text = SEP_LINE.join(body)
    command = title + SEP_ZONE + body_text + '\n'
    
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(1.5)
        ser.write(command.encode('utf-8'))
        ser.close()
        log(f"Backup hook: title='{title}' body={body}")
    except Exception as e:
        log(f"Error: {e}")


if __name__ == '__main__':
    main()