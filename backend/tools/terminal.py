"""命令行操作工具 - 支持 Docker 沙箱 / 本地双模式执行"""

import os
import subprocess
from langchain_core.tools import tool
from config import SANDBOX_ROOT, SANDBOX_ENABLED, DANGEROUS_COMMANDS


def _is_dangerous(command: str) -> bool:
    cmd_lower = command.lower().strip()
    for pattern in DANGEROUS_COMMANDS:
        if pattern in cmd_lower:
            return True
    return False


def _exec_local(command: str) -> str:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            cwd=str(SANDBOX_ROOT),
            env=env,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]: {result.stderr}"
        if result.returncode != 0:
            output += f"\n[EXIT CODE]: {result.returncode}"
        return output.strip() or "(命令执行完毕，无输出)"
    except subprocess.TimeoutExpired:
        return "⚠️ 命令执行超时（30秒限制）"
    except Exception as e:
        return f"⚠️ 命令执行出错: {str(e)}"


def create_terminal_tool():
    @tool("terminal")
    def terminal(command: str) -> str:
        """在安全环境下执行 Shell 命令。
        可用于文件操作、系统查询、包管理等任务。
        禁止执行危险的系统命令（如 rm -rf /）。

        Args:
            command: 要执行的 Shell 命令字符串
        """
        if _is_dangerous(command):
            return f"⚠️ 安全拦截：命令 `{command}` 被判定为高危操作，已阻止执行。"

        if SANDBOX_ENABLED:
            from sandbox.manager import get_sandbox
            return get_sandbox().exec_command(command)

        return _exec_local(command)

    return terminal
