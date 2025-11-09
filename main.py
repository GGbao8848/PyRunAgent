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