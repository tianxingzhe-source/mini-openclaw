"""沙箱功能验证脚本 — 运行前确保 .env 中 SANDBOX_ENABLED=true 且 Docker 正在运行"""

import os
os.environ.setdefault("SANDBOX_ENABLED", "true")

from config import SANDBOX_ENABLED, SKILLS_DIR

if not SANDBOX_ENABLED:
    print("❌ SANDBOX_ENABLED 未启用，请在 .env 中设置 SANDBOX_ENABLED=true")
    raise SystemExit(1)

from sandbox.manager import get_sandbox

print("=" * 60)
print("沙箱功能验证")
print("=" * 60)

sandbox = get_sandbox()
sandbox.ensure_running()
print("✅ 沙箱容器已启动\n")

passed = 0
failed = 0


def check(name: str, ok: bool, detail: str = ""):
    global passed, failed
    status = "✅ PASS" if ok else "❌ FAIL"
    print(f"  {status} | {name}")
    if detail:
        for line in detail.strip().splitlines():
            print(f"         {line}")
    if ok:
        passed += 1
    else:
        failed += 1
    print()


# ── 测试 1: 基本 Shell 命令 ────────────────────────────────
print("【测试组 1】Shell 命令执行")

out = sandbox.exec_command("echo hello-sandbox")
check("echo 命令", "hello-sandbox" in out, f"输出: {out!r}")

out = sandbox.exec_command("pwd")
check("工作目录是 /sandbox", out.strip() == "/sandbox", f"输出: {out!r}")

out = sandbox.exec_command("ls /sandbox")
check(
    "挂载目录存在",
    all(d in out for d in ["skills", "workspace", "memory", "knowledge"]),
    f"输出: {out!r}",
)

# ── 测试 2: 基本 Python 执行 ──────────────────────────────
print("【测试组 2】Python 代码执行")

out = sandbox.exec_python("print(1 + 1)")
check("简单计算", "2" in out, f"输出: {out!r}")

out = sandbox.exec_python("import sys; print(sys.version)")
check("Python 版本", "3.12" in out or "3." in out, f"输出: {out!r}")

# ── 测试 3: 命名空间持久性 ─────────────────────────────────
print("【测试组 3】Python 命名空间持久性")

sandbox.exec_python("sandbox_test_var = 42")
out = sandbox.exec_python("print(sandbox_test_var)")
check("变量跨调用保持", "42" in out, f"输出: {out!r}")

# ── 测试 4: 文件隔离验证 ──────────────────────────────────
print("【测试组 4】文件系统隔离")

out = sandbox.exec_command("cat /etc/hostname")
check("可读取容器内部文件（正常）", len(out.strip()) > 0, f"输出: {out!r}")

out = sandbox.exec_command("ls C:\\ 2>&1 || echo ISOLATED")
check(
    "无法访问 Windows 宿主机路径",
    "ISOLATED" in out or "No such file" in out or "cannot access" in out,
    f"输出: {out!r}",
)

out = sandbox.exec_command("ls /home 2>&1")
check(
    "宿主机 home 目录不可见",
    "SKILL.md" not in out and "app.py" not in out,
    f"输出: {out!r}",
)

# ── 测试 5: 挂载目录读写同步 ──────────────────────────────
print("【测试组 5】挂载目录读写同步")

test_file = "skills/_sandbox_test/SKILL.md"
test_content = "---\nname: sandbox_test\n---\n# Test Skill"

sandbox.exec_command(f"mkdir -p /sandbox/skills/_sandbox_test")
sandbox.exec_command(
    f"cat > /sandbox/{test_file} << 'HEREDOC'\n{test_content}\nHEREDOC"
)

local_path = SKILLS_DIR / "_sandbox_test" / "SKILL.md"
local_exists = local_path.exists()
local_content = local_path.read_text(encoding="utf-8").strip() if local_exists else ""
check(
    "容器内创建文件 → 本地可见",
    local_exists and "sandbox_test" in local_content,
    f"本地路径: {local_path}\n存在: {local_exists}\n内容: {local_content!r}",
)

sandbox.exec_command("rm -rf /sandbox/skills/_sandbox_test")
check(
    "容器内删除文件 → 本地同步删除",
    not local_path.exists(),
    f"本地文件已删除: {not local_path.exists()}",
)

# ── 测试 6: knowledge 目录只读 ────────────────────────────
print("【测试组 6】knowledge 目录只读保护")

out = sandbox.exec_command(
    "touch /sandbox/knowledge/_test_write 2>&1; echo EXIT:$?"
)
check(
    "knowledge 目录不可写入",
    "EXIT:0" not in out or "Read-only" in out or "Permission denied" in out,
    f"输出: {out!r}",
)
sandbox.exec_command("rm -f /sandbox/knowledge/_test_write 2>&1")

# ── 测试 7: 超时保护 ─────────────────────────────────────
print("【测试组 7】超时保护")

out = sandbox.exec_command("sleep 10", timeout=3)
check("Shell 超时生效", "超时" in out, f"输出: {out!r}")

out = sandbox.exec_python("import time; time.sleep(10)", timeout=3)
check("Python 超时生效", "超时" in out, f"输出: {out!r}")


# ── 汇总 ──────────────────────────────────────────────────
print("=" * 60)
print(f"结果: {passed} 通过, {failed} 失败 / 共 {passed + failed} 项")
print("=" * 60)

if failed:
    raise SystemExit(1)
