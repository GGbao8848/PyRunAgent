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