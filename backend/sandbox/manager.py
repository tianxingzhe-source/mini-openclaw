"""Docker 沙箱管理器 — 管理沙箱容器的生命周期与命令执行"""

import time
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

_instance: "SandboxManager | None" = None


class SandboxManager:
    """通过 Docker 容器提供隔离的命令 / Python 执行环境。

    挂载策略（选择性目录挂载）：
        skills/     → /sandbox/skills     (rw)  Agent 可创建、编辑技能
        workspace/  → /sandbox/workspace  (rw)  Agent 工作区
        memory/     → /sandbox/memory     (rw)  长期记忆
        knowledge/  → /sandbox/knowledge  (ro)  知识库，只读
    """

    def __init__(self):
        import docker

        self._docker = docker
        try:
            self._client = docker.from_env()
            self._client.ping()
        except Exception as e:
            raise RuntimeError(
                f"无法连接到 Docker: {e}\n"
                "请确保 Docker Desktop 已安装并正在运行。"
            ) from e

        from config import (
            SANDBOX_IMAGE,
            SANDBOX_CONTAINER_NAME,
            SANDBOX_EXECUTOR_PORT,
            SKILLS_DIR,
            WORKSPACE_DIR,
            MEMORY_DIR,
            KNOWLEDGE_DIR,
        )

        self._image = SANDBOX_IMAGE
        self._name = SANDBOX_CONTAINER_NAME
        self._port = SANDBOX_EXECUTOR_PORT
        self._dockerfile_dir = str(Path(__file__).resolve().parent)

        for d in [SKILLS_DIR, WORKSPACE_DIR, MEMORY_DIR, KNOWLEDGE_DIR]:
            d.mkdir(parents=True, exist_ok=True)

        self._volumes = {
            str(SKILLS_DIR.resolve()): {"bind": "/sandbox/skills", "mode": "rw"},
            str(WORKSPACE_DIR.resolve()): {"bind": "/sandbox/workspace", "mode": "rw"},
            str(MEMORY_DIR.resolve()): {"bind": "/sandbox/memory", "mode": "rw"},
            str(KNOWLEDGE_DIR.resolve()): {"bind": "/sandbox/knowledge", "mode": "ro"},
        }
        self._container = None

    # ── 容器生命周期 ──────────────────────────────────────────

    def _get_container(self):
        try:
            return self._client.containers.get(self._name)
        except self._docker.errors.NotFound:
            return None

    def _image_exists(self) -> bool:
        try:
            self._client.images.get(self._image)
            return True
        except self._docker.errors.ImageNotFound:
            return False

    def _build_image(self):
        logger.info("正在构建沙箱镜像 '%s' ...", self._image)
        self._client.images.build(
            path=self._dockerfile_dir,
            tag=self._image,
            rm=True,
        )
        logger.info("沙箱镜像构建完成")

    def ensure_running(self):
        """确保沙箱容器处于运行状态；不存在时自动构建 & 创建。"""
        container = self._get_container()

        if container is not None:
            if container.status == "running":
                self._container = container
                return
            logger.info("启动已有沙箱容器 ...")
            container.start()
            self._container = container
            self._wait_for_executor()
            return

        if not self._image_exists():
            self._build_image()

        logger.info("创建沙箱容器 '%s' ...", self._name)
        self._container = self._client.containers.run(
            self._image,
            detach=True,
            name=self._name,
            volumes=self._volumes,
            ports={"9999/tcp": ("127.0.0.1", self._port)},
            mem_limit="512m",
            cpu_period=100000,
            cpu_quota=50000,
            restart_policy={"Name": "unless-stopped"},
        )
        self._wait_for_executor()
        logger.info("沙箱容器已就绪")

    def _wait_for_executor(self, timeout: int = 60):
        """轮询等待容器内 Python 执行器服务启动。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                resp = httpx.post(
                    f"http://127.0.0.1:{self._port}/exec",
                    json={"code": "pass"},
                    timeout=2,
                )
                if resp.status_code == 200:
                    return
            except (httpx.ConnectError, httpx.TimeoutException):
                pass
            time.sleep(0.5)
        raise TimeoutError("沙箱 Python 执行器启动超时")

    def stop(self):
        container = self._get_container()
        if container and container.status == "running":
            container.stop(timeout=5)
            logger.info("沙箱容器已停止")

    def destroy(self):
        container = self._get_container()
        if container:
            container.remove(force=True)
            logger.info("沙箱容器已移除")

    # ── 命令执行 ──────────────────────────────────────────────

    def exec_command(self, command: str, timeout: int = 30) -> str:
        """在沙箱容器中执行 Shell 命令并返回输出。"""
        self.ensure_running()
        try:
            exit_code, output = self._container.exec_run(
                ["timeout", str(timeout), "bash", "-c", command],
                workdir="/sandbox",
                demux=True,
                environment={"PYTHONIOENCODING": "utf-8"},
            )
            stdout = (output[0] or b"").decode("utf-8", errors="replace")
            stderr = (output[1] or b"").decode("utf-8", errors="replace")

            if exit_code == 124:
                return f"⚠️ 命令执行超时（{timeout}秒限制）"

            result = stdout
            if stderr:
                result += f"\n[STDERR]: {stderr}"
            if exit_code != 0:
                result += f"\n[EXIT CODE]: {exit_code}"
            return result.strip() or "(命令执行完毕，无输出)"
        except Exception as e:
            return f"⚠️ 沙箱命令执行出错: {str(e)}"

    def exec_python(self, code: str, timeout: int = 30) -> str:
        """在沙箱容器中执行 Python 代码（持久命名空间）。"""
        self.ensure_running()
        try:
            resp = httpx.post(
                f"http://127.0.0.1:{self._port}/exec",
                json={"code": code},
                timeout=timeout,
            )
            data = resp.json()
            return data.get("output", "(无输出)")
        except httpx.TimeoutException:
            return "⚠️ 代码执行超时"
        except Exception as e:
            return f"⚠️ 沙箱代码执行出错: {str(e)}"


def get_sandbox() -> SandboxManager:
    """获取沙箱管理器单例（懒初始化）。"""
    global _instance
    if _instance is None:
        _instance = SandboxManager()
    return _instance
