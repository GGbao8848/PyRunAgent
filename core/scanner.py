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