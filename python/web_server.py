# -*- coding: utf-8 -*-

"""

OLED Web Canvas - USB即插即用画布控制

插上ESP8266 → 自动检测串口 → 启动Web服务 → 弹出浏览器

浏览器中可以打字、画画、传图片 → 点发送推送到OLED屏幕

"""

import http.server

import json

import os

import serial

import serial.tools.list_ports

import sys

import threading

import time

import webbrowser

BAUD_RATE = 9600

HTTP_PORT = 8077

BITMAP_SIZE = 1024

# ============================================================

# 串口管理

# ============================================================

def find_esp_port():

    ports = serial.tools.list_ports.comports()

    for p in ports:

        desc = (p.description or "").lower()

        mfr = (p.manufacturer or "").lower()

        if any(k in desc for k in ["ch340","ch341","cp210","ftdi","usb-serial","usb serial","silicon labs"]):

            return p.device

        if any(k in mfr for k in ["wch","silicon labs","ftdi"]):

            return p.device

    if len(ports) == 1:

        return ports[0].device

    return None

def send_text_command(port, command):

    try:

        ser = serial.Serial(port, BAUD_RATE, timeout=1)

        time.sleep(0.1)

        data = (command + "\n").encode("utf-8")

        ser.write(data)

        time.sleep(0.1)

        ser.close()

        return True

    except Exception as e:

        print(f"[串口] 文本发送失败: {e}")

        return False

def send_bitmap(port, xbm_bytes):

    """发送位图: BITMAP命令 + 握手R + 1024字节数据 + 确认K"""

    try:

        ser = serial.Serial(port, BAUD_RATE, timeout=5)

        time.sleep(0.1)

        ser.reset_input_buffer()

        time.sleep(0.1)

        ser.write(b"BITMAP\n")

        ser.flush()

        resp = ser.read(1)

        if resp != b'R':

            ser.close()

            print(f"[串口] 未收到Ready: {resp!r}")

            return False

        chunk = 64

        for i in range(0, len(xbm_bytes), chunk):

            ser.write(xbm_bytes[i:i+chunk])

            ser.flush()

            time.sleep(0.01)

        resp = ser.read(1)

        ser.close()

        ok = resp == b'K'

        if not ok:

            print(f"[串口] 位图确认: {resp!r}")

        return ok

    except Exception as e:

        print(f"[串口] 位图发送失败: {e}")

        return False

def send_diff(port, prev_bytes, curr_bytes):

    """发送差分帧: DIFF命令 + 握手R + 变化数量 + 变化数据 + 确认K"""

    # 计算差分

    changes = []

    for i in range(len(curr_bytes)):

        if prev_bytes[i] != curr_bytes[i]:

            changes.append((i, curr_bytes[i]))

    if not changes:

        return True  # 没变化，跳过

    n = len(changes)

    # 差分数据: 每组3字节 [index_lo][index_hi][value]

    diff_data = bytearray()

    for idx, val in changes:

        diff_data.append(idx & 0xFF)

        diff_data.append((idx >> 8) & 0xFF)

        diff_data.append(val)

    try:

        ser = serial.Serial(port, BAUD_RATE, timeout=5)

        time.sleep(0.05)

        ser.reset_input_buffer()

        time.sleep(0.05)

        ser.write(b"DIFF\n")

        ser.flush()

        resp = ser.read(1)

        if resp != b'R':

            ser.close()

            print(f"[串口] DIFF未收到Ready: {resp!r}")

            return False

        # 发送变化数量 (2字节小端)

        ser.write(bytes([n & 0xFF, (n >> 8) & 0xFF]))

        ser.flush()

        # 发送差分数据

        chunk = 64

        for i in range(0, len(diff_data), chunk):

            ser.write(diff_data[i:i+chunk])

            ser.flush()

            time.sleep(0.01)

        resp = ser.read(1)

        ser.close()

        ok = resp == b'K'

        if not ok:

            print(f"[串口] DIFF确认: {resp!r}")

        return ok

    except Exception as e:

        print(f"[串口] DIFF发送失败: {e}")

        return False

# ============================================================

# HTML

# ============================================================

HTML_PAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web.html')

def load_html_page():
    with open(HTML_PAGE_PATH, 'r', encoding='utf-8') as f:
        return f.read()

# ============================================================
# HTTP 服务
# ============================================================

esp_port = None

AGENTS_FLAG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.agents_enabled')

def get_agents_enabled():

    try:

        with open(AGENTS_FLAG_FILE, 'r') as f:

            return f.read().strip() == '1'

    except FileNotFoundError:

        return True

def set_agents_enabled(enabled):

    with open(AGENTS_FLAG_FILE, 'w') as f:

        f.write('1' if enabled else '0')

class OLEDHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):

        pass

    def do_GET(self):

        if self.path == '/' or self.path == '/index.html':

            self.send_response(200)

            self.send_header('Content-Type', 'text/html; charset=utf-8')

            self.end_headers()

            self.wfile.write(load_html_page().encode('utf-8'))

        elif self.path == '/api/status':

            self.send_json({"port": esp_port})

        elif self.path == '/api/agents_status':

            self.send_json({"enabled": get_agents_enabled()})

        else:

            self.send_response(404)

            self.end_headers()

    def do_POST(self):

        global esp_port

        length = int(self.headers.get('Content-Length', 0))

        body = self.rfile.read(length)

        try:

            data = json.loads(body)

        except Exception:

            self.send_json({"ok": False, "error": "invalid json"}, 400)

            return

        if self.path == '/api/agents_toggle':

            enabled = data.get('enabled', True)

            set_agents_enabled(enabled)

            self.send_json({"ok": True, "enabled": enabled})

        elif self.path == '/api/send_text':

            cmd = data.get("command", "")

            if not cmd:

                self.send_json({"ok": False, "error": "empty command"}, 400)

                return

            if not esp_port:

                esp_port = find_esp_port()

            if not esp_port:

                self.send_json({"ok": False, "error": "未检测到ESP8266"})

                return

            ok = send_text_command(esp_port, cmd)

            self.send_json({"ok": ok})

        elif self.path == '/api/send_diff':

            prev_arr = data.get("prev", [])

            curr_arr = data.get("curr", [])

            if len(prev_arr) != BITMAP_SIZE or len(curr_arr) != BITMAP_SIZE:

                self.send_json({"ok": False, "error": "data length mismatch"}, 400)

                return

            if not esp_port:

                esp_port = find_esp_port()

            if not esp_port:

                self.send_json({"ok": False, "error": "\u672a\u68c0\u6d4b\u5230ESP8266"})

                return

            ok = send_diff(esp_port, bytes(prev_arr), bytes(curr_arr))

            self.send_json({"ok": ok})

        elif self.path == '/api/send_bitmap':

            byte_arr = data.get("data", [])

            if len(byte_arr) != BITMAP_SIZE:

                self.send_json({"ok": False, "error": f"data length {len(byte_arr)} != {BITMAP_SIZE}"}, 400)

                return

            if not esp_port:

                esp_port = find_esp_port()

            if not esp_port:

                self.send_json({"ok": False, "error": "未检测到ESP8266"})

                return

            ok = send_bitmap(esp_port, bytes(byte_arr))

            self.send_json({"ok": ok})

        else:

            self.send_response(404)

            self.end_headers()

    def send_json(self, obj, code=200):

        self.send_response(code)

        self.send_header('Content-Type', 'application/json')

        self.end_headers()

        self.wfile.write(json.dumps(obj).encode('utf-8'))

def main():

    global esp_port

    print("=" * 50)

    print("  OLED Web Canvas")

    print("=" * 50)

    esp_port = find_esp_port()

    if esp_port:

        print(f"[OK] 检测到ESP8266: {esp_port}")

    else:

        print("[!] 未检测到ESP8266")

    server = http.server.HTTPServer(('127.0.0.1', HTTP_PORT), OLEDHandler)

    server.socket.setsockopt(__import__('socket').SOL_SOCKET, __import__('socket').SO_REUSEADDR, 1)

    url = f"http://127.0.0.1:{HTTP_PORT}"

    print(f"[OK] Web服务已启动: {url}")

    threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    print("[OK] 正在打开浏览器...")

    print("\n按 Ctrl+C 退出")

    try:

        server.serve_forever()

    except KeyboardInterrupt:

        print("\n已退出")

        server.server_close()

if __name__ == '__main__':

    main()

