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


# ============================================================
# HTML
# ============================================================

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OLED Canvas</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#1a1a2e;color:#e0e0e0;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;padding:16px}
h1{font-size:18px;margin-bottom:12px;color:#00d4ff}
.toolbar{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;justify-content:center}
.toolbar button,.toolbar select,.toolbar input[type="range"]{padding:6px 14px;border:1px solid #444;border-radius:6px;background:#2a2a4a;color:#e0e0e0;cursor:pointer;font-size:13px}
.toolbar button:hover{background:#3a3a6a}
.toolbar button.active{background:#00d4ff;color:#000;border-color:#00d4ff}
.canvas-wrap{position:relative;border:2px solid #00d4ff;border-radius:8px;background:#000;overflow:hidden}
canvas#preview{display:block;image-rendering:pixelated}
.text-panel{display:none;margin-top:12px;width:100%;max-width:540px}
.status{margin-top:12px;padding:8px 16px;border-radius:6px;font-size:13px;min-height:36px;text-align:center}
.status.ok{background:#0a3a0a;color:#4f4}
.status.err{background:#3a0a0a;color:#f44}
.status.info{background:#0a2a3a;color:#4df}
.send-row{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;justify-content:center}
.send-row button{padding:10px 28px;border:none;border-radius:8px;font-size:15px;cursor:pointer;font-weight:600}
#btnSendBitmap{background:#ff6b6b;color:#fff}
#btnClear{background:#444;color:#e0e0e0}
#btnUndo{background:#444;color:#e0e0e0}
.help{margin-top:16px;font-size:12px;color:#888;text-align:center;max-width:540px}
</style>
</head>
<body>
<h1>OLED Canvas (128 x 64)</h1>

<div style="display:flex;gap:8px;margin-bottom:12px;align-items:center;">
  <label style="cursor:pointer;display:flex;align-items:center;gap:6px;font-size:13px;">
    <span>Agents</span>
    <input type="checkbox" id="agentsToggle" onchange="toggleAgents(this.checked)" style="width:16px;height:16px;cursor:pointer;">
    <span id="agentsLabel" style="font-size:12px;color:#888;">关闭</span>
  </label>
</div>



<div id="canvasArea">
<div class="toolbar">
  <button id="toolDraw" class="active" onclick="setTool('draw')">画笔</button>
  <button id="toolErase" onclick="setTool('erase')">橡皮</button>
  <button id="toolText" onclick="setTool('text')">文字</button>
  <button id="toolImage" onclick="setTool('image')">图片</button>
  <button id="btnUndo" onclick="undo()">撤销</button>
  <button id="btnClear" onclick="clearCanvas()">清空</button>
  <label style="display:flex;align-items:center;gap:4px;font-size:12px;">
    粗细 <input type="range" id="brushSize" min="1" max="4" value="1" style="width:60px;">
  </label>
</div>

<div class="text-panel" id="textPanel">
  <div style="display:flex;gap:8px;align-items:flex-start;flex-wrap:wrap;">
    <textarea id="textInput" rows="3" placeholder="输入要显示的文字" style="flex:1;min-width:200px;padding:8px;border:1px solid #444;border-radius:6px;background:#2a2a4a;color:#e0e0e0;font-size:14px;resize:vertical;"></textarea>
    <div style="display:flex;flex-direction:column;gap:6px;">
      <select id="textSize" style="padding:6px;border:1px solid #444;border-radius:6px;background:#2a2a4a;color:#e0e0e0;font-size:12px;">
        <option value="8">8px</option>
        <option value="10">10px</option>
        <option value="12" selected>12px 标准</option>
        <option value="14">14px</option>
        <option value="16">16px 大</option>
        <option value="20">20px</option>
      </select>
      <select id="textAlign" style="padding:6px;border:1px solid #444;border-radius:6px;background:#2a2a4a;color:#e0e0e0;font-size:12px;">
        <option value="left">左对齐</option>
        <option value="center" selected>居中</option>
        <option value="right">右对齐</option>
      </select>

    </div>
  </div>
</div>

<input type="file" id="fileInput" accept="image/*" style="display:none" onchange="loadImage(event)">

<div class="canvas-wrap">
  <canvas id="preview" width="128" height="64" style="width:512px;height:256px;"></canvas>
</div>

<div class="send-row">
  <button id="btnSendBitmap" onclick="sendBitmap()">发送到屏幕</button>
</div>

<div class="status info" id="status">检测中...</div>

<div class="help">
  画笔画画 / 橡皮擦除 / 文字模式点预览后写入画布 / 图片自动缩放二值化<br>
  黄色=上半区域 蓝色=下半区域 所见即所得预览
</div>

</div>

<script>
const W=128,H=64,BITMAP_SIZE=1024;
const canvas=document.getElementById('preview');
const ctx=canvas.getContext('2d');
let tool='draw',drawing=false,history=[],brushSz=1;
let lastX=-1,lastY=-1;

function initCanvas(){
  ctx.fillStyle='#1a1500';ctx.fillRect(0,0,W,16);
  ctx.fillStyle='#000';ctx.fillRect(0,16,W,1);
  ctx.fillStyle='#000a1a';ctx.fillRect(0,17,W,47);
}
if(!restoreCanvas())initCanvas();

function saveState(){if(history.length>30)history.shift();history.push(ctx.getImageData(0,0,W,H));}
function undo(){if(history.length===0)return;ctx.putImageData(history.pop(),0);setStatus('已撤销','info');}
function clearCanvas(){saveState();initCanvas();setStatus('已清空','info');}

function setTool(t){
  tool=t;
  document.querySelectorAll('.toolbar button[id^="tool"]').forEach(b=>b.classList.remove('active'));
  document.getElementById('tool'+t.charAt(0).toUpperCase()+t.slice(1)).classList.add('active');
  document.getElementById('textPanel').style.display=t==='text'?'block':'none';
  if(t==='text')document.getElementById('textInput').focus();
  if(t==='image'){document.getElementById('fileInput').click();setTool('draw');}
}
document.getElementById('brushSize').addEventListener('input',e=>{brushSz=parseInt(e.target.value);});

function getPos(e){
  const rect=canvas.getBoundingClientRect();
  const scaleX=W/rect.width,scaleY=H/rect.height;
  const clientX=e.touches?e.touches[0].clientX:e.clientX;
  const clientY=e.touches?e.touches[0].clientY:e.clientY;
  return{x:Math.floor((clientX-rect.left)*scaleX),y:Math.floor((clientY-rect.top)*scaleY)};
}

canvas.addEventListener('mousedown',onDown);
canvas.addEventListener('mousemove',onMove);
canvas.addEventListener('mouseup',onUp);
canvas.addEventListener('mouseleave',onUp);
canvas.addEventListener('touchstart',e=>{e.preventDefault();onDown(e);});
canvas.addEventListener('touchmove',e=>{e.preventDefault();onMove(e);});
canvas.addEventListener('touchend',e=>{e.preventDefault();onUp(e);});

function onDown(e){
  if(tool==='text')return;
  if(tool==='draw'||tool==='erase'){saveState();drawing=true;const p=getPos(e);lastX=p.x;lastY=p.y;drawDot(p.x,p.y);}
}
function onMove(e){
  if(!drawing)return;const p=getPos(e);drawLine(lastX,lastY,p.x,p.y);lastX=p.x;lastY=p.y;
}
function onUp(){drawing=false;lastX=-1;lastY=-1;}

function drawLine(x0,y0,x1,y1){
  const dx=Math.abs(x1-x0),dy=Math.abs(y1-y0);
  const sx=x0<x1?1:-1,sy=y0<y1?1:-1;
  let err=dx-dy;
  while(true){drawDot(x0,y0);if(x0===x1&&y0===y1)break;const e2=2*err;if(e2>-dy){err-=dy;x0+=sx;}if(e2<dx){err+=dx;y0+=sy;}}
}

function getZoneColor(y){return y<16?'#ffcc00':'#00aaff';}
function drawDot(x,y){
  if(x<0||x>=W||y<0||y>=H)return;
  ctx.fillStyle=tool==='erase'?(y<16?'#1a1500':y===16?'#000':'#000a1a'):getZoneColor(y);
  if(brushSz===1){ctx.fillRect(x,y,1,1);}
  else{const r=brushSz;ctx.fillRect(x-r+1,y-r+1,r*2-1,r*2-1);}
}

// Text
let textPreviewData=null;
function previewText(){
  const txt=document.getElementById('textInput').value;
  if(!txt.trim()){setStatus('请输入文字','err');return;}
  const size=parseInt(document.getElementById('textSize').value);
  const align=document.getElementById('textAlign').value;
  if(textPreviewData)ctx.putImageData(textPreviewData,0,0);
  textPreviewData=ctx.getImageData(0,0,W,H);
  initCanvas();
  const lines=txt.split('\n');
  const lineH=Math.ceil(size*1.3);
  const totalH=lines.length*lineH;
  const startY=Math.max(0,Math.floor((H-totalH)/2));
  ctx.textBaseline='top';
  for(let i=0;i<lines.length;i++){
    const y=startY+i*lineH;
    ctx.font=size+'px monospace';ctx.fillStyle=getZoneColor(y);
    let x;const w=ctx.measureText(lines[i]).width;
    if(align==='center')x=Math.floor((W-w)/2);
    else if(align==='right')x=W-w-2;else x=2;
    if(x<0)x=0;ctx.fillText(lines[i],x,y);
  }
  setStatus('预览中 点写入画布确认','info');
}
document.getElementById('textInput').addEventListener('input',()=>{clearTimeout(previewTimer);previewTimer=setTimeout(previewText,300);});
let previewTimer=null;
document.getElementById('textSize').addEventListener('change',()=>{if(document.getElementById('textInput').value.trim())previewText();});
document.getElementById('textAlign').addEventListener('change',()=>{if(document.getElementById('textInput').value.trim())previewText();});

// Image
function loadImage(e){
  const file=e.target.files[0];if(!file)return;
  const reader=new FileReader();
  reader.onload=function(ev){
    const img=new Image();
    img.onload=function(){
      saveState();
      const tmp=document.createElement('canvas');tmp.width=W;tmp.height=H;
      const tc=tmp.getContext('2d');
      const scale=Math.min(W/img.width,H/img.height);
      const dw=img.width*scale,dh=img.height*scale;
      tc.fillStyle='#000';tc.fillRect(0,0,W,H);
      tc.drawImage(img,(W-dw)/2,(H-dh)/2,dw,dh);
      const imgData=tc.getImageData(0,0,W,H);
      const data=imgData.data;
      const gray=new Float32Array(W*H);
      for(let i=0;i<W*H;i++){gray[i]=0.299*data[i*4]+0.587*data[i*4+1]+0.114*data[i*4+2];}
      for(let y=0;y<H;y++){for(let x=0;x<W;x++){
        const idx=y*W+x;const old=gray[idx];const nv=old>127?255:0;gray[idx]=nv;const err=old-nv;
        if(x+1<W)gray[idx+1]+=err*7/16;
        if(y+1<H){if(x>0)gray[idx+W-1]+=err*3/16;gray[idx+W]+=err*5/16;if(x+1<W)gray[idx+W+1]+=err*1/16;}
      }}
      initCanvas();
      for(let y=0;y<H;y++){for(let x=0;x<W;x++){
        if(gray[y*W+x]>127){ctx.fillStyle=getZoneColor(y);ctx.fillRect(x,y,1,1);}
      }}
      setStatus('图片已加载并二值化','ok');saveCanvas();
    };img.src=ev.target.result;
  };reader.readAsDataURL(file);e.target.value='';
}

// Auto-save canvas to localStorage
function saveCanvas(){
  try{localStorage.setItem('oled_canvas', canvas.toDataURL());}catch(e){}
}
function restoreCanvas(){
  try{
    const d=localStorage.getItem('oled_canvas');
    if(!d)return false;
    const img=new Image();
    img.onload=function(){ctx.drawImage(img,0,0);};
    img.src=d;
    return true;
  }catch(e){return false;}
}

// Auto-save after draw operations
const _origDrawDot=drawDot;
drawDot=function(x,y){_origDrawDot(x,y);saveCanvas();};
const _origUndo=undo;
undo=function(){_origUndo();saveCanvas();};
const _origClear=clearCanvas;
clearCanvas=function(){_origClear();setTimeout(saveCanvas,10);};

// Bitmap
function getBitmapData(){
  const imgData=ctx.getImageData(0,0,W,H);const data=imgData.data;
  const bytes=new Uint8Array(BITMAP_SIZE);
  for(let y=0;y<H;y++){for(let bx=0;bx<W/8;bx++){
    let byte=0;
    for(let bit=0;bit<8;bit++){
      const x=bx*8+bit;const idx=(y*W+x)*4;
      if(data[idx]>30||data[idx+1]>30||data[idx+2]>30)byte|=(1<<bit);
    }
    bytes[y*(W/8)+bx]=byte;
  }}
  return bytes;
}

async function sendBitmap(){
  const bytes=getBitmapData();
  try{
    const r=await fetch('/api/send_bitmap',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({data:Array.from(bytes)})});
    const j=await r.json();setStatus(j.ok?'画面已发送!':'发送失败: '+j.error,j.ok?'ok':'err');
  }catch(e){setStatus('请求失败: '+e.message,'err');}
}

// Mode: canvas=手动画布 agents=接受Python自动推送
function setMode(mode){
  document.getElementById('canvasArea').style.display=mode==='canvas'?'':'none';
  document.getElementById('agentsPanel').style.display=mode==='agents'?'block':'none';
  try{localStorage.setItem('oled_mode',mode);}catch(e){}
}
// Restore saved mode
try{
  const savedMode=localStorage.getItem('oled_mode');
  if(savedMode==='agents'){
    document.querySelector('input[name="mode"][value="agents"]').checked=true;
    setMode('agents');
  }
}catch(e){}


function setStatus(msg,type){const el=document.getElementById('status');el.textContent=msg;el.className='status '+(type||'info');}

// 初始状态检查
fetch('/api/status').then(r=>r.json()).then(j=>{
  setStatus(j.port?'已连接 '+j.port:'未检测到ESP8266',j.port?'ok':'err');
}).catch(()=>setStatus('服务连接失败','err'));

// Agents toggle
let agentsEnabled=true;
function toggleAgents(on){
  agentsEnabled=on;
  document.getElementById('agentsLabel').textContent=on?'\u5f00\u542f':'\u5173\u95ed';
  document.getElementById('agentsLabel').style.color=on?'#4f4':'#888';
  fetch('/api/agents_toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:on})});
  try{localStorage.setItem('oled_agents',on?'1':'0');}catch(e){}
}
fetch('/api/agents_status').then(r=>r.json()).then(j=>{
  agentsEnabled=j.enabled;
  document.getElementById('agentsToggle').checked=j.enabled;
  document.getElementById('agentsLabel').textContent=j.enabled?'\u5f00\u542f':'\u5173\u95ed';
  document.getElementById('agentsLabel').style.color=j.enabled?'#4f4':'#888';
}).catch(()=>{});

// Restore saved text inputs
try{
  const st=localStorage.getItem('oled_agentTitle');
  if(st)document.getElementById('agentTitle').value=st;
  const sb=localStorage.getItem('oled_agentBody');
  if(sb)document.getElementById('agentBody').value=sb;
  const si=localStorage.getItem('oled_textInput');
  if(si)document.getElementById('textInput').value=si;
}catch(e){}

// Auto-save text inputs
document.getElementById('agentTitle').addEventListener('input',()=>{try{localStorage.setItem('oled_agentTitle',document.getElementById('agentTitle').value);}catch(e){}});
document.getElementById('agentBody').addEventListener('input',()=>{try{localStorage.setItem('oled_agentBody',document.getElementById('agentBody').value);}catch(e){}});
document.getElementById('textInput').addEventListener('input',()=>{try{localStorage.setItem('oled_textInput',document.getElementById('textInput').value);}catch(e){}});

</script>
</body>
</html>
"""

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
            self.wfile.write(HTML_PAGE.encode('utf-8'))
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
