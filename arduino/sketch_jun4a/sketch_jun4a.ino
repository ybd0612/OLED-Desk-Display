/**
 * ============================================================
 *  AI Agent Desktop Status Display - Arduino Firmware
 * ============================================================
 *
 * Hardware: ESP8266 + 0.96" OLED SSD1306 (128x64, I2C, dual-color)
 * Screen: Top 16px yellow + Bottom 48px blue
 *
 * Wiring:
 *   SCL -> GPIO 12 (D6)
 *   SDA -> GPIO 14 (D5)
 *   VCC -> 3.3V, GND -> GND
 *
 * Serial: 9600 baud
 * Libraries: U8g2, Wire (built-in)
 *
 * Command format:
 *   Preset:  WAIT / SUCCESS / FAIL
 *   Custom:  "yellow_text|blue_line1\blue_line2\blue_line3"
 *   - "|" separates yellow zone and blue zone
 *   - "\" separates lines within blue zone (each line centered)
 *   - If no "\", auto-wrap by pixel width
 * ============================================================
 */

#include <Arduino.h>
#include <U8g2lib.h>
#include <Wire.h>

U8G2_SSD1306_128X64_NONAME_F_SW_I2C u8g2(U8G2_R0, /* clock=*/ 12, /* data=*/ 14, /* reset=*/ U8X8_PIN_NONE);

const int BAUD_RATE = 9600;
const int YELLOW_TOP = 0;
const int YELLOW_BOT = 16;
const int BLUE_TOP = 16;
const int BLUE_BOT = 64;
const int LINE_H = 14;
const int MAX_W = 124;
const int SCR_W = 128;
const int SCR_H = 64;
const int MAX_L = 3;

const char* DEF_TOP = "AI Agent";
const char* DEF_BOT = "STANDBY";

// 分隔符（ASCII 控制字符，用户不会手动输入）
const char SEP_ZONE = 0x1F;   // Unit Separator: 分隔上下区域
const char SEP_LINE = 0x1E;   // Record Separator: 分隔蓝色区域行
const char SEP_FLASH = 0x1C;  // File Separator: 标记闪烁前缀

// 位图模式
const char* CMD_BITMAP = "BITMAP";
const int BITMAP_SIZE = 1024;  // 128*64/8 = 1024 bytes

// 函数前置声明
void showCustom(String top, String bottom, bool shouldFlash = false);
void showBitmap();
void setup(void) {
  Serial.begin(BAUD_RATE);
  u8g2.begin();
  u8g2.enableUTF8Print();
  showWaiting();
}

void loop(void) {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == CMD_BITMAP) {
      showBitmap();
    } else if (cmd == "SUCCESS") {
      showSuccess();
    } else if (cmd == "FAIL") {
      showFail();
    } else if (cmd == "WAIT") {
      showWaiting();
    } else if (cmd.length() > 0 && cmd.charAt(0) == SEP_FLASH) {
      // Hook 触发：带闪烁
      String payload = cmd.substring(1);  // 去掉闪烁前缀
      int sep = payload.indexOf(SEP_ZONE);
      if (sep > 0) {
        showCustom(payload.substring(0, sep), payload.substring(sep + 1), true);
      } else {
        showCustom(DEF_TOP, payload, true);
      }
    } else if (cmd.indexOf(SEP_ZONE) > 0) {
      int sep = cmd.indexOf(SEP_ZONE);
      showCustom(cmd.substring(0, sep), cmd.substring(sep + 1));
    } else {
      showCustom(DEF_TOP, cmd);
    }
  }
}

/**
 * 位图模式：接收 1024 字节的 XBM 数据并全屏显示
 * 协议：Python 先发 "BITMAP\n"，再发 1024 字节原始位图数据
 */
void showBitmap() {
  uint8_t buf[BITMAP_SIZE];

  // 握手：告诉Python已准备好接收位图数据
  Serial.write('R');

  int received = 0;
  unsigned long start = millis();

  while (received < BITMAP_SIZE && (millis() - start) < 5000) {
    if (Serial.available() > 0) {
      int bytesRead = Serial.readBytes(buf + received, BITMAP_SIZE - received);
      received += bytesRead;
    }
  }

  if (received >= BITMAP_SIZE) {
    u8g2.clearBuffer();
    u8g2.drawXBM(0, 0, SCR_W, SCR_H, buf);
    u8g2.sendBuffer();
    Serial.write('K');  // OK
  } else {
    Serial.write('E');  // Error
  }
}

void showWaiting() {
  u8g2.clearBuffer();
  u8g2.drawFrame(0, 0, SCR_W, SCR_H);
  u8g2.setFont(u8g2_font_wqy12_t_gb2312);
  drawSingleLine(YELLOW_TOP, YELLOW_BOT, DEF_TOP);
  drawAutoWrap(BLUE_TOP, BLUE_BOT, DEF_BOT);
  u8g2.sendBuffer();
}

void showSuccess() {
  u8g2.clearBuffer();
  u8g2.drawFrame(0, 0, SCR_W, SCR_H);
  u8g2.setFont(u8g2_font_wqy12_t_gb2312);
  drawSingleLine(YELLOW_TOP, YELLOW_BOT, DEF_TOP);
  drawAutoWrap(BLUE_TOP, BLUE_BOT, "SUCCESS");
  u8g2.sendBuffer();
}

void showFail() {
  u8g2.clearBuffer();
  u8g2.drawFrame(0, 0, SCR_W, SCR_H);
  u8g2.setFont(u8g2_font_wqy12_t_gb2312);
  drawSingleLine(YELLOW_TOP, YELLOW_BOT, DEF_TOP);
  drawAutoWrap(BLUE_TOP, BLUE_BOT, "FAIL");
  u8g2.sendBuffer();
}

/**
 * Custom display
 * @param top    Yellow zone text (single line)
 * @param bottom Blue zone text
 *               Contains '\' -> split by '\', each line centered
 *               No '\'       -> auto-wrap by pixel width
 */
void showCustom(String top, String bottom, bool shouldFlash) {
  u8g2.clearBuffer();
  u8g2.drawFrame(0, 0, SCR_W, SCR_H);
  u8g2.setFont(u8g2_font_wqy12_t_gb2312);
  drawSingleLine(YELLOW_TOP, YELLOW_BOT, top.c_str());

  if (bottom.indexOf(SEP_LINE) >= 0) {
    drawBySeparator(BLUE_TOP, BLUE_BOT, bottom);
  } else {
    drawAutoWrap(BLUE_TOP, BLUE_BOT, bottom.c_str());
  }

  if (shouldFlash) {
    flashScreen(3, 80);  // 闪烁3次，每次80ms
    // 闪烁后重新绘制内容
    drawSingleLine(YELLOW_TOP, YELLOW_BOT, top.c_str());
    if (bottom.indexOf(SEP_LINE) >= 0) {
      drawBySeparator(BLUE_TOP, BLUE_BOT, bottom);
    } else {
      drawAutoWrap(BLUE_TOP, BLUE_BOT, bottom.c_str());
    }
  }
  u8g2.sendBuffer();
}

/* Single line centered (yellow zone) */
void drawSingleLine(int y0, int y1, const char* txt) {
  int w = u8g2.getUTF8Width(txt);
  int h = u8g2.getAscent() - u8g2.getDescent();
  int x = (SCR_W - w) / 2;
  int y = y0 + (y1 - y0 + h) / 2;
  if (x < 2) x = 2;
  u8g2.drawUTF8(x, y, txt);
}

/**
 * Split by '\' and draw each line centered (blue zone)
 * Used when Hook sends pre-formatted multi-line text
 */
void drawBySeparator(int y0, int y1, String text) {
  int areaH = y1 - y0;
  int maxL = areaH / LINE_H;
  String lines[MAX_L + 1];
  int cnt = 0;
  int si = 0;

  while (si < (int)text.length() && cnt < maxL) {
    int idx = text.indexOf(SEP_LINE, si);
    if (idx < 0) {
      lines[cnt] = text.substring(si);
      cnt++;
      break;
    } else {
      lines[cnt] = text.substring(si, idx);
      cnt++;
      si = idx + 1;
    }
  }

  int totalH = cnt * LINE_H;
  int startY = y0 + (areaH - totalH) / 2;

  for (int k = 0; k < cnt; k++) {
    int w = u8g2.getUTF8Width(lines[k].c_str());
    int x = (SCR_W - w) / 2;
    int y = startY + k * LINE_H + LINE_H - 2;
    if (x < 2) x = 2;
    u8g2.drawUTF8(x, y, lines[k].c_str());
  }
}


/**
 * 屏幕闪烁效果
 * @param times  闪烁次数
 * @param delayMs 每次亮/灭的间隔（毫秒）
 * 原理：快速发送空白帧和当前帧交替，产生闪烁感
 */
void flashScreen(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    // 亮：全白屏
    u8g2.clearBuffer();
    u8g2.drawBox(0, 0, SCR_W, SCR_H);
    u8g2.sendBuffer();
    delay(delayMs);
    // 灭：全黑屏
    u8g2.clearBuffer();
    u8g2.sendBuffer();
    delay(delayMs);
  }
  // 闪烁结束，重绘最终画面
  u8g2.clearBuffer();
  u8g2.drawFrame(0, 0, SCR_W, SCR_H);
  u8g2.setFont(u8g2_font_wqy12_t_gb2312);
}

/**
 * Auto-wrap by pixel width (blue zone)
 * Supports mixed Chinese/English, vertically centered
 */
void drawAutoWrap(int y0, int y1, const char* text) {
  int areaH = y1 - y0;
  int maxL = areaH / LINE_H;
  String str = String(text);
  String lines[MAX_L + 1];
  int cnt = 0;
  int len = str.length();
  int i = 0;

  while (i < len && cnt < maxL) {
    String line = "";
    int j = i;
    while (j < len) {
      String ch = "";
      unsigned char c = str.charAt(j);
      if (c >= 0x80) {
        if (j + 2 < len) { ch = str.substring(j, j + 3); j += 3; }
        else { ch = str.substring(j); j = len; }
      } else {
        ch = String(str.charAt(j)); j += 1;
      }
      String test = line + ch;
      if (u8g2.getUTF8Width(test.c_str()) > MAX_W && line.length() > 0) break;
      line = test;
    }
    lines[cnt] = line;
    cnt++;
    i = j;
  }

  int totalH = cnt * LINE_H;
  int startY = y0 + (areaH - totalH) / 2;

  for (int k = 0; k < cnt; k++) {
    int w = u8g2.getUTF8Width(lines[k].c_str());
    int x = (SCR_W - w) / 2;
    int y = startY + k * LINE_H + LINE_H - 2;
    if (x < 2) x = 2;
    u8g2.drawUTF8(x, y, lines[k].c_str());
  }
}
