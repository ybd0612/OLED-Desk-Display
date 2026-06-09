# AI Agent 桌面小屏幕

> 一个放在电脑旁边的 OLED 小屏幕，每次对话结束后自动显示 AI Agent 的工作摘要。


## 为什么做这个

用 Claude Code 这类 AI 编程工具时，经常要等它跑完一个长任务。眼睛一直盯着终端太累了，而且离开一下又不知道它跑完了没有。

所以想：能不能在桌上放个小屏幕，AI 跑完任务后自动在屏幕上显示结果摘要？抬头看一眼就行。

## 怎么想到这个方案的

最初的想法是外挂一个灯——成功亮绿灯，失败亮红灯。跟 Gemini 讨论了一圈硬件方案：

- **智能插座/灯泡**：能用，但有网络延迟，而且只能亮灯，看不到文字
- **ESP8266 + LED 灯带**：便宜、能自定义闪烁，但还是只有颜色没有内容
- **D1 Mini + 小 OLED 屏**：能显示文字，但 0.66 寸太小看不清

后来发现有一种 **ESP8266 和 0.96 寸 OLED 焊在一块的一体板**，十几块钱，插上 USB 就能用。屏幕够大，能塞下好几行中文，完美解决了"既要看得到内容、又要够便宜、还要免接线"的需求。

最终方案：一体板通过 USB 串口接收电脑端 Python 脚本发来的文字，AI 对话结束后自动推送摘要到屏幕上。


## 设计理念

### 为什么用 AI Agent 总结，而不是用 Hook 自动截取

Hook 脚本只能机械地截取和传递原始文本，没法做语义总结。如果对话内容很长，直接截取的片段往往缺少上下文，看不懂在说什么。

所以采用 **AGENTS.md + conversation_hook.py** 的组合：
- **AGENTS.md** 让 AI 自己理解对话内容，生成精炼的、符合屏幕字数限制的摘要
- **conversation_hook.py** 负责把摘要推送到屏幕

### 为什么要闪屏

直接在屏幕上切换文字，人很容易忽略——尤其是余光扫一眼的时候。所以推送摘要时屏幕会**白黑闪烁 3 次**，确保你能注意到有新消息。

这就是为什么有两个脚本：
- **display_hook.py**：手动控制，直接切换文字，不闪屏（适合主动查看/调试）
- **conversation_hook.py**：AI 对话结束后推送，带闪屏提醒（适合日常使用）

**[English Version](README_EN.md)** | **[技术文档](docs/项目文档.md)**

---

## 你需要准备什么

| 材料 | 说明 | 参考价格 |
|------|------|---------|
| ESP8266 一体板 | 带 0.96 寸 OLED 屏幕的那种（淘宝搜 "ESP8266 OLED 一体板"） | ￥16 |
| Type-C 数据线 | 连接电脑用的，注意要能传数据的那种，不能只能充电 | - |
| 一台电脑 | Windows 10/11 | - |

> 💡 **买板子小贴士**：搜索关键词 "ESP8266 0.96寸 OLED 一体板 NodeMCU"，选带屏幕的版本，买回来直接就能用，不用自己焊。注意确认接口是 Type-C 还是 Micro USB，Type-C 更方便。
>
> 🔗 **推荐购买链接**：[淘宝 - ESP8266 OLED 一体板](https://e.tb.cn/h.RhEO5NmkXbNigtq?tk=HTlngZy42Jn)

## 实物展示

<p align="center">
  <img src="docs/images/demo_animation.gif" alt="OLED Desk Display 效果演示" width="480">
</p>

---

## 第一步：下载项目代码

1. 点击本页面右上角绿色 **Code** 按钮 → **Download ZIP**
2. 解压到你电脑上任意位置（比如桌面）
3. 记住解压后的文件夹路径，后面要用

---

## 第二步：安装 Arduino IDE

### 2.1 下载 Arduino IDE

打开这个网址下载：**https://www.arduino.cc/en/software**

1. 点击 **Windows Win 10 and newer**
2. 下载完双击安装，一路点下一步就行

### 2.2 添加 ESP8266 支持

Arduino IDE 本身不认识我们的小板子，需要告诉它去哪里找：

1. 打开刚装好的 Arduino IDE
2. 点击左上角 **File（文件）** → **Preferences（首选项）**
3. 找到 **Additional Boards Manager URLs（附加开发板管理器网址）** 这一栏
4. 把下面这串网址复制粘贴进去：
   ```
   http://arduino.esp8266.com/stable/package_esp8266com_index.json
   ```
5. 点击 **OK** 保存

### 2.3 安装 ESP8266 支持包

1. 点击 IDE 最左侧侧边栏的 **"正方形积木"图标**（Boards Manager / 开发板管理器）
2. 在搜索框输入：`esp8266`
3. 找到 **esp8266 by ESP8266 Community**，点击 **Install（安装）**
4. 等它下载完成，显示 **Installed** 就行了（可能需要 1-2 分钟，耐心等）

> ⚠️ 如果下载很慢或失败，可能是网络问题。多试几次，或者挂个梯子。

---

## 第三步：安装屏幕驱动库

1. 点击最左侧侧边栏的 **"抽屉/书架"图标**（Library Manager / 库管理器）
2. 在搜索框输入：`U8g2`
3. 找到 **U8g2 by oliver**，点击 **Install（安装）**
4. 如果弹窗问你要不要安装依赖库，点击 **"Install all"** 全选安装

> 💡 **为什么要装这个？** U8g2 是单片机屏幕界的"万能神器"，对国内这种 0.96 寸一体板兼容性最好，自带超多字体，不容易黑屏。

---

## 第四步：上传程序到板子

### 4.1 用数据线把板子连上电脑

把 Type-C 数据线一头插板子，一头插电脑 USB 口。

> ⚠️ **注意**：有些充电线只能充电不能传数据！如果电脑没反应（设备管理器里看不到 COM 口），换一根线试试。

### 4.2 确认电脑识别到了板子

1. 右键点击桌面上的 **"此电脑"**（或 "我的电脑"）→ **管理** → **设备管理器**
2. 展开 **"端口(COM 和 LPT)"**
3. 你应该能看到类似 **USB-SERIAL CH340 (COM3)** 这样的东西
4. 记住这个 **COM 号**（比如 COM3），后面要用

> 💡 如果设备管理器里没看到，说明：
> - 数据线只能充电不能传数据 → 换一根
> - 没装驱动 → 淘宝卖家的详情页一般有驱动下载链接，或者搜 "CH340 驱动下载"

### 4.3 设置开发板

在 Arduino IDE 顶部中间的下拉菜单：

1. **开发板（Board）** 选择：**Generic ESP8266 Module**（通用的，所有 ESP8266 一体板都通吃）
2. **端口（Port）** 选择：你在设备管理器里看到的那个 **COM 号**（比如 COM3）

### 4.4 上传代码

1. 在 Arduino IDE 里打开解压后项目文件夹中的 `arduino/sketch_jun4a/sketch_jun4a.ino`
2. 点击 IDE 左上角的 **👉 箭头图标**（Upload / 上传）
3. 软件下方会显示：
   - `Compiling sketch...`（正在编译...）
   - `Uploading...`（正在上传...）
4. 此时你会看到**板子上有个小灯在疯狂闪烁**，说明程序正在写入
5. 等到显示 `Done uploading.` 就成功了！🎉

> ⚠️ 如果编译卡住不动，检查一下第三步的 U8g2 库有没有装好。

---

## 第五步：安装 Python（电脑端控制脚本）

屏幕程序上传好了，接下来在电脑上装一个 Python 脚本，用来给屏幕发消息。

### 5.1 安装 Python

1. 打开 **https://www.python.org/downloads/**
2. 点击 **Download Python 3.x.x** 下载最新版
3. 安装时 **一定要勾选 "Add Python to PATH"**（最下面那个复选框）！
4. 一路下一步安装完成

### 5.2 安装依赖

打开命令提示符（按 `Win + R`，输入 `cmd`，回车），进入项目文件夹，输入：

```bash
pip install -r requirements.txt
```

看到 `Successfully installed` 就行了。

### 5.3 修改 COM 号

打开 `python/display_hook.py`，找到：

```python
SERIAL_PORT = 'COM3'
```

把 `COM3` 改成你在第四步记下的那个 COM 号，保存。

> 💡 `python/conversation_hook.py` 里也有同样的配置，记得一起改。

---

## 第六步：开始使用 🎉

打开命令提示符（`Win + R` → `cmd` → 回车），进入项目文件夹，然后：

```bash
# 等待状态（屏幕显示：AI Agent + STANDBY）
python python/display_hook.py WAIT

# 成功状态（屏幕显示：AI Agent + SUCCESS）
python python/display_hook.py SUCCESS

# 失败状态（屏幕显示：AI Agent + FAIL）
python python/display_hook.py FAIL

# 自定义文字（黄色区域 | 蓝色区域）
python python/display_hook.py "AI Agent|你好"

# 单行文字（显示在蓝色区域）
python python/display_hook.py hello
```

---

## 我想改屏幕上的默认文字

用记事本打开 `arduino/sketch_jun4a/sketch_jun4a.ino`，找到这两行：

```cpp
const char* DEF_TOP = "AI Agent";   // 黄色区域的文字
const char* DEF_BOT = "STANDBY";    // 蓝色区域的文字
```

改成你想要的，然后重新上传就行。

---

## Web Canvas 画布控制（新功能）

除了命令行推送，还可以通过网页画布自由创作内容推送到屏幕。

### 功能

- **画笔/橡皮** — 在 128x64 画布上自由画画
- **文字输入** — 多行文本，可选字体大小和对齐方式，实时预览
- **图片上传** — 自动缩放并二值化（Floyd-Steinberg 抖动算法）
- **双色模拟** — 画布上半黄色下半蓝色，所见即所得
- **Agents 开关** — 控制 conversation_hook 是否能推送消息
- **自动保存** — 画布和设置保存在浏览器 localStorage，刷新不丢失

### 使用方式

1. 双击 `start_oled_canvas.bat`（或运行 `python python\web_server.py`）
2. 浏览器自动打开画布页面
3. 画完点 **发送到屏幕** 即可

### 一键烧录固件

修改 Arduino 代码后，双击 `flash.bat` 即可一键编译+烧录（首次编译需 2-3 分钟）。

> 💡 Web Canvas 需要更新的 Arduino 固件支持位图模式。首次使用请先用 `flash.bat` 或 Arduino IDE 上传固件。

---

## 常见问题

### Q：上传时报错 "COM 口被占用"
**A：** 把 Arduino IDE 的串口监视器关掉（如果开了的话），或者拔掉数据线重新插。

### Q：上传成功但屏幕没反应
**A：** 检查一下你买的板子是不是自带屏幕的版本。如果是分体式的，需要自己接线（SCL→D6, SDA→D5）。

### Q：Python 脚本报 "无法连接到屏幕硬件"
**A：**
1. 检查 COM 号对不对
2. 检查 Arduino IDE 的串口监视器有没有关掉（同一时间只能一个程序连串口）
3. 拔掉数据线重新插

### Q：中文显示不出来
**A：** 确认你上传的是最新版代码 `arduino/sketch_jun4a/sketch_jun4a.ino`，旧版不支持中文。

### Q：Compiling sketch 卡住不动
**A：** 第三步的 U8g2 库没装好。去库管理器搜索 U8g2 重新安装。

---

## 项目文件说明

| 文件 | 说明 |
|------|------|
| `arduino/sketch_jun4a/sketch_jun4a.ino` | 上传到板子里的程序（一次性） |
| `python/display_hook.py` | 手动控制屏幕（状态/自定义文字） |
| `python/conversation_hook.py` | 对话摘要推送（支持手动/Prompt/管道模式） |
| `python/web_server.py` | Web Canvas 画布控制（画画/文字/图片推送） |
| `hooks/session_start_hook.py` | 对话开始时提醒 agent 推送摘要 |
| `start_oled_canvas.bat` | 一键启动 Web Canvas 服务 |
| `flash.bat` | 一键编译烧录 Arduino 固件 |
| `requirements.txt` | Python 依赖列表 |
| `docs/项目文档.md` | 技术细节和开发记录 |

---

## 还有问题？

- 查看 [技术文档](docs/项目文档.md) 了解详细配置
- 查看 [English Version](README_EN.md)
