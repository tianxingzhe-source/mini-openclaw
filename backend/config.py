"""Mini-OpenClaw 配置管理"""

import os
import sys

# Windows 全局强制 UTF-8，防止 subprocess / open 等默认走 GBK 导致中文乱码
os.environ.setdefault("PYTHONUTF8", "1")
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

PORT = int(os.getenv("PORT", "8002"))
SANDBOX_ROOT = Path(os.getenv("SANDBOX_ROOT", str(BASE_DIR))).resolve()

WORKSPACE_DIR = BASE_DIR / "workspace"
MEMORY_DIR = BASE_DIR / "memory"
SESSIONS_DIR = BASE_DIR / "sessions"
SKILLS_DIR = BASE_DIR / "skills"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
STORAGE_DIR = BASE_DIR / "storage"

MAX_PROMPT_CHARS = 20_000
DANGEROUS_COMMANDS = [
    "rm -rf /", "rm -rf /*", "mkfs", "dd if=", ":(){:|:&};:",
    "shutdown", "reboot", "halt", "poweroff",
    "format c:", "del /f /s /q c:\\",
]

# Docker 沙箱配置（设 SANDBOX_ENABLED=true 启用容器隔离执行）
SANDBOX_ENABLED = os.getenv("SANDBOX_ENABLED", "false").lower() == "true"
SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE", "mini-openclaw-sandbox")
SANDBOX_CONTAINER_NAME = os.getenv("SANDBOX_CONTAINER_NAME", "mini-openclaw-sandbox")
SANDBOX_EXECUTOR_PORT = int(os.getenv("SANDBOX_EXECUTOR_PORT", "9999"))
