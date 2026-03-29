"""文件读取工具 - 读取本地文件内容（Skills 机制的核心依赖）"""

from pathlib import Path
from langchain_core.tools import tool
from config import SANDBOX_ROOT


def create_read_file_tool():
    @tool("read_file")
    def read_file(path: str) -> str:
        """读取指定路径的本地文件内容。
        这是 Agent Skills 机制的核心工具 - 用于读取 SKILL.md 的详细说明。
        路径限制在项目根目录内，禁止读取项目以外的系统文件。

        Args:
            path: 文件的相对路径（相对于项目根目录）或绝对路径
        """
        try:
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = SANDBOX_ROOT / file_path

            file_path = file_path.resolve()
            sandbox = SANDBOX_ROOT.resolve()
            if not str(file_path).startswith(str(sandbox)):
                return f"⚠️ 安全限制：不允许读取项目目录以外的文件: {path}"

            if not file_path.exists():
                return f"⚠️ 文件不存在: {path}"

            if not file_path.is_file():
                return f"⚠️ 路径不是文件: {path}"

            content = file_path.read_text(encoding="utf-8")

            if len(content) > 50_000:
                content = content[:50_000] + "\n\n...[truncated]"

            return content

        except UnicodeDecodeError:
            return f"⚠️ 无法以文本模式读取文件（可能是二进制文件）: {path}"
        except Exception as e:
            return f"⚠️ 读取文件出错: {str(e)}"

    return read_file
