"""Mini-OpenClaw Core Tools"""

from tools.terminal import create_terminal_tool
from tools.python_repl import create_python_repl_tool
from tools.fetch_url import create_fetch_url_tool
from tools.read_file import create_read_file_tool
from tools.rag_search import create_rag_search_tool
from tools.skill_manager import (
    create_install_skill_tool,
    create_remove_skill_tool,
    create_list_available_skills_tool,
)


def get_all_tools():
    """初始化并返回所有核心工具列表"""
    return [
        create_terminal_tool(),
        create_python_repl_tool(),
        create_fetch_url_tool(),
        create_read_file_tool(),
        create_rag_search_tool(),
        create_install_skill_tool(),
        create_remove_skill_tool(),
        create_list_available_skills_tool(),
    ]
