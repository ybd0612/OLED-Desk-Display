"""
============================================================
 AI Agent 桌面状态显示器 - Python 控制脚本
============================================================

功能：
    通过 USB 串口向 ESP8266 OLED 屏幕发送显示指令。

依赖：
    pip install pyserial

串口配置：
    SERIAL_PORT: 在 Arduino IDE → 工具 → 端口 中查看
    BAUD_RATE:   9600（需与 Arduino 端一致）

用法：
    python display_hook.py WAIT            → 等待界面
    python display_hook.py SUCCESS         → 成功界面
    python display_hook.py FAIL            → 失败界面
    python display_hook.py "Ybond|你好"    → 自定义上下两行
    python display_hook.py hello           → 自定义单行（蓝色区域）

编码说明：
    数据以 UTF-8 编码发送，Arduino 端使用 U8g2 的 UTF-8 模式接收，
    支持中英文混排。

============================================================
"""

import serial
import sys
import time

# ============================================================
# 配置区（唯一需要修改的地方）
# ============================================================
SERIAL_PORT = 'COM3'   # Windows: 'COM3'  Mac: '/dev/cu.usbserial-xxx'
BAUD_RATE = 9600       # 波特率，需与 Arduino 端一致


def send_status(status):
    """
    通过串口发送状态指令到 Arduino 屏幕

    Args:
        status (str): 要发送的文本指令
            - 预设指令: "WAIT" / "SUCCESS" / "FAIL"
            - 自定义双行: "上行文字|下行文字"
            - 自定义单行: "任意文字"
    """
    try:
        # 打开串口连接
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        # 等待硬件初始化（ESP8266 重启后需要短暂稳定时间）
        time.sleep(1.5)

        # 将用户输入的 | 转为 0x1F 分隔符
        converted = status.replace('|', chr(0x1F))
        # 以 UTF-8 编码发送，末尾加换行符作为指令结束标记
        data = (converted + '\n').encode('utf-8')
        ser.write(data)
        ser.close()

        print(f"已成功发送: {status}")
    except Exception as e:
        print(f"无法连接到屏幕硬件: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # 无参数时默认发送 WAIT 指令
        current_status = "WAIT"
    else:
        # 支持带空格的参数（用引号包裹）
        # 例如: python display_hook.py "Ybond|你好"
        current_status = " ".join(sys.argv[1:])

    send_status(current_status)