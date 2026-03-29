"""Python 代码解释器 - 执行 Python 代码片段"""

import sys
import io
import builtins
from functools import partial
from langchain_core.tools import tool


def _utf8_open(*args, **kwargs):
    """强制使用 UTF-8 编码的 open 函数，避免 Windows 默认 GBK 导致乱码"""
    if "b" not in (args[1] if len(args) > 1 else kwargs.get("mode", "")):
        kwargs.setdefault("encoding", "utf-8")
    return builtins.open(*args, **kwargs)


def create_python_repl_tool():
    namespace: dict = {"open": _utf8_open}

    @tool("python_repl")
    def python_repl(code: str) -> str:
        """执行 Python 代码并返回输出结果。
        适用于逻辑计算、数据处理、脚本执行等场景。
        代码在隔离的命名空间中运行，变量在多次调用间保持。

        Args:
            code: 要执行的 Python 代码字符串
        """
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = captured_out = io.StringIO()
        sys.stderr = captured_err = io.StringIO()

        try:
            exec(code, namespace)
            output = captured_out.getvalue()
            errors = captured_err.getvalue()
            result = output
            if errors:
                result += f"\n[STDERR]: {errors}"
            return result.strip() or "(代码执行完毕，无输出)"
        except Exception as e:
            return f"执行出错: {type(e).__name__}: {str(e)}"
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    return python_repl
