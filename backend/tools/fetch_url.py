"""Fetch 网络信息获取工具 - 获取网页内容并转为可读文本"""

import httpx
import html2text
from langchain_core.tools import tool


def create_fetch_url_tool():
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True
    converter.body_width = 0

    @tool("fetch_url")
    def fetch_url(url: str) -> str:
        """获取指定 URL 的网页内容，自动将 HTML 转换为 Markdown 格式的纯文本。
        适用于获取网页信息、API 调用等场景。

        Args:
            url: 要获取内容的完整 URL 地址
        """
        try:
            with httpx.Client(timeout=15, follow_redirects=True) as client:
                response = client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; MiniOpenClaw/1.0)"
                })
                response.raise_for_status()

            content_type = response.headers.get("content-type", "")

            if "application/json" in content_type:
                return response.text[:8000]
            elif "text/html" in content_type:
                md_content = converter.handle(response.text)
                return md_content[:8000]
            elif "text/plain" in content_type:
                return response.text[:8000]
            else:
                return response.text[:8000]

        except httpx.TimeoutException:
            return f"⚠️ 请求超时: {url}"
        except httpx.HTTPStatusError as e:
            return f"⚠️ HTTP 错误 {e.response.status_code}: {url}"
        except Exception as e:
            return f"⚠️ 获取失败: {str(e)}"

    return fetch_url
