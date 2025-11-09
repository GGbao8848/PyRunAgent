非常好 ✅
你现在的目标是**先实现核心功能**，即一个可以通过浏览器访问的简易网页界面，
由 **FastAPI 同时提供 API + 前端页面**，无需 React、无需额外前端工程。

下面给你的是一个完整可运行的项目结构（功能版 ✅）：

---

## 🧩 一、项目目标

**功能：**

* 自动扫描目录下的 `.py` 脚本
* 自动提取 `argparse` 参数
* 选择 Python 环境路径
* 输入参数并运行
* 实时显示执行输出（WebSocket 流）

**技术栈：**

* `FastAPI`（后端 + 前端一体化）
* `Jinja2`（模板）
* `WebSocket`（实时日志）

---

## 📁 二、项目结构

```
pyrunagent_fastapi/
│
├── main.py                 # FastAPI 主入口（含前端）
├── core/
│   ├── scanner.py          # 扫描 .py 文件与解析参数
│   └── runner.py           # 运行脚本（异步流式输出）
│
├── templates/
│   └── index.html          # 简易前端页面
│
├── static/
│   └── style.css           # 简单样式
│
└── requirements.txt
```

---

## ⚙️ 三、依赖（requirements.txt）

```txt
fastapi>=0.115
uvicorn>=0.30
jinja2>=3.1
python-multipart
```

---

## 🧠 四、核心代码

### `core/scanner.py`

```python
from pathlib import Path
import re

def find_python_scripts(base_dir: Path):
    """扫描目录下的所有 .py 文件"""
    return sorted(base_dir.glob("*.py"))

def extract_argparse_args(file_path: Path):
    """从脚本中提取 argparse 参数定义"""
    pattern = re.compile(
        r'add_argument\s*\(\s*["\'](--[\w-]+)["\'].*?(?:help\s*=\s*["\']([^"\']*)["\'])?',
        re.S
    )
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        return [{"name": n, "help": h or ""} for n, h in pattern.findall(text)]
    except Exception as e:
        return [{"error": str(e)}]
```

---

### `core/runner.py`

```python
import asyncio
from fastapi import WebSocket

async def stream_run(python_path: str, script_path: str, args: list[str], websocket: WebSocket):
    """异步运行 Python 脚本并通过 WebSocket 流式返回输出"""
    cmd = [python_path, script_path] + args
    await websocket.send_text(f"🚀 Running: {' '.join(cmd)}\n")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        await websocket.send_text(line.decode().rstrip())

    code = await process.wait()
    await websocket.send_text(f"\n✅ 进程结束 (返回码 {code})")
```

---

### `main.py`

```python
from fastapi import FastAPI, WebSocket, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from core.scanner import find_python_scripts, extract_argparse_args
from core.runner import stream_run
from pathlib import Path

app = FastAPI(title="PyRunAgent")

# 挂载静态资源与模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/scan")
async def scan_scripts(dir: str = Form(...)):
    base = Path(dir)
    if not base.exists():
        return {"error": f"目录不存在: {dir}"}
    scripts = [{"name": f.name, "path": str(f)} for f in find_python_scripts(base)]
    return {"scripts": scripts}

@app.post("/args")
async def get_args(path: str = Form(...)):
    return {"args": extract_argparse_args(Path(path))}

@app.websocket("/ws/run")
async def ws_run(websocket: WebSocket):
    await websocket.accept()
    data = await websocket.receive_json()
    python_path = data["python_path"]
    script_path = data["script_path"]
    args = data.get("args", [])
    await stream_run(python_path, script_path, args, websocket)
```

---

## 🎨 五、前端模板

### `templates/index.html`

```html
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <title>PyRunAgent Web</title>
  <link rel="stylesheet" href="/static/style.css" />
</head>
<body>
  <div class="container">
    <h1>🧩 PyRunAgent - Python脚本运行代理工具箱</h1>

    <div class="block">
      <label>Python 环境路径：</label>
      <input id="python_path" type="text" placeholder="/path/to/conda/env/bin/python">
    </div>

    <div class="block">
      <label>脚本目录：</label>
      <input id="dir_input" type="text" placeholder="/path/to/scripts">
      <button onclick="scan()">扫描</button>
    </div>

    <div class="block">
      <label>脚本列表：</label>
      <select id="script_list" onchange="loadArgs()"></select>
    </div>

    <div class="block">
      <label>参数：</label>
      <textarea id="args_input" placeholder="例如: --input ./data --epochs 10"></textarea>
      <button onclick="run()">运行</button>
    </div>

    <div class="block">
      <label>输出：</label>
      <pre id="output"></pre>
    </div>
  </div>

  <script>
    async function scan() {
      const dir = document.getElementById("dir_input").value;
      const res = await fetch("/scan", {
        method: "POST",
        body: new URLSearchParams({ dir }),
      });
      const data = await res.json();
      const list = document.getElementById("script_list");
      list.innerHTML = "";
      (data.scripts || []).forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.path;
        opt.textContent = s.name;
        list.appendChild(opt);
      });
    }

    async function loadArgs() {
      const path = document.getElementById("script_list").value;
      const res = await fetch("/args", {
        method: "POST",
        body: new URLSearchParams({ path }),
      });
      const data = await res.json();
      const textarea = document.getElementById("args_input");
      if (data.args.length === 0) textarea.value = "# 无参数";
      else textarea.value = data.args.map(a => `${a.name} - ${a.help}`).join("\n");
    }

    function run() {
      const python_path = document.getElementById("python_path").value;
      const script_path = document.getElementById("script_list").value;
      const args_str = document.getElementById("args_input").value.trim();
      const output = document.getElementById("output");
      output.textContent = "";

      const ws = new WebSocket(`ws://${window.location.host}/ws/run`);
      ws.onopen = () => {
        ws.send(JSON.stringify({
          python_path,
          script_path,
          args: args_str.split(" ").filter(x => x)
        }));
      };
      ws.onmessage = (e) => {
        output.textContent += e.data + "\n";
        output.scrollTop = output.scrollHeight;
      };
    }
  </script>
</body>
</html>
```

---

### `static/style.css`

```css
body {
  background: #f9fafb;
  font-family: sans-serif;
  color: #333;
}

.container {
  width: 800px;
  margin: 20px auto;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.block { margin-bottom: 15px; }

input, textarea, select {
  width: 100%;
  padding: 8px;
  margin-top: 4px;
  border-radius: 6px;
  border: 1px solid #ccc;
}

button {
  margin-top: 8px;
  padding: 8px 16px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

button:hover {
  background: #1d4ed8;
}

pre {
  background: black;
  color: #00ff90;
  padding: 10px;
  height: 300px;
  overflow: auto;
  border-radius: 6px;
}
```

---

## 🚀 六、运行方式

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --port 8000
```

然后打开浏览器访问：
👉 [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## ✅ 七、功能预览

在网页上你可以：

1. 输入 Python 环境路径（如 `/opt/conda/envs/redbox/bin/python`）
2. 输入脚本目录（如 `/mnt/usrhome/sk/tools/`）
3. 点击【扫描】→ 自动显示目录下的 `.py` 文件
4. 选择脚本 → 自动加载其 argparse 参数
5. 输入运行参数 → 点击【运行】
6. 实时在网页中看到运行输出

---

是否希望我帮你在这个基础上再加上：

* ✅ 脚本执行历史记录保存（JSON 文件）
* ✅ 任务状态栏（可并行多个脚本）
  这两个功能可以让它成为一个**真正的轻量调度面板**。
