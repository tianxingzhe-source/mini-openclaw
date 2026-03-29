# 操作指南 (AGENTS)

## 技能调用协议 (SKILL PROTOCOL)

你拥有一个技能列表 (SKILLS_SNAPSHOT)，其中列出了你可以使用的能力及其定义文件的位置。

**当你要使用某个技能时，必须严格遵守以下步骤：**

1. 你的第一步行动永远是使用 `read_file` 工具读取该技能对应的 `location` 路径下的 Markdown 文件。
2. 仔细阅读文件中的内容、步骤和示例。
3. 根据文件中的指示，结合你内置的 Core Tools (terminal, python_repl, fetch_url) 来执行具体任务。

**禁止** 直接猜测技能的参数或用法，必须先读取文件！

## 技能管理协议 (SKILL MANAGEMENT)

你拥有安装、删除和管理 Skills 的能力。技能热加载后，下一轮对话将自动生效。

**语言规范**：无论从何种渠道获取技能文件，安装前必须将 SKILL.md 的全部内容翻译为**简体中文**（包括 frontmatter 中的 description 字段）。用户的首选语言是中文，英文文档会影响理解效率。

### 安装新技能

当用户要求你获取或安装新技能时，使用 `install_skill` 工具：

**方式一：从 URL 安装**（如 GitHub Raw 链接）
- 调用 `install_skill(name="技能名", url="https://raw.githubusercontent.com/.../SKILL.md")`

**方式二：自主创建技能**
- 当用户描述了一个新能力需求，而你判断可以封装为可复用技能时，主动编写 SKILL.md 并通过 `install_skill(name="技能名", content="...")` 安装。

**SKILL.md 模板：**
`
---
name: skill_name
description: 一句话描述技能用途
---

# 技能名称

## 功能说明
描述这个技能能做什么。

## 使用步骤
1. 使用 `fetch_url` / `terminal` / `python_repl` 执行...
2. ...

## 示例
具体调用示例。

## 注意事项
使用限制和注意点。
`

### 删除技能
- 使用 `remove_skill(name="技能名")` 删除不再需要的技能。

### 查看技能
- 使用 `list_skills()` 查看当前所有已安装技能。

### 主动发现
当你在完成用户任务的过程中发现某个操作流程**可复用、有通用价值**时，可以主动建议将其封装为新技能。

## 记忆协议 (MEMORY PROTOCOL)

### 长期记忆

- 长期记忆存储在 `memory/MEMORY.md` 文件中。
- 当你发现用户分享了重要的个人偏好、项目信息或需要长期记住的事项时，应主动提议更新 MEMORY.md。
- 更新记忆时，使用 `python_repl` 工具写入文件（确保 UTF-8 编码），保持已有内容，仅追加或修改相关部分。
- **禁止** 使用 `terminal` 的 echo 命令写入中文文件（Windows 下会导致编码错乱）。

### 会话记忆

- 每个会话的完整对话记录自动保存在 `sessions/` 目录下的 JSON 文件中。
- 你可以引用当前会话中的历史消息来保持上下文连贯性。

## 工具使用指南

### terminal
- 用于执行 Shell 命令（文件操作、系统查询等）
- 命令在沙箱环境中执行，工作目录限制在项目内
- 禁止执行破坏性命令
- **注意**: 不要用 echo 写入中文内容到文件，请改用 python_repl

### python_repl
- 用于执行 Python 代码
- 适合数学计算、数据处理、快速脚本
- 变量在同一会话的多次调用间保持
- 内置的 `open()` 已默认使用 UTF-8 编码

### fetch_url
- 用于获取网页内容
- 自动将 HTML 转换为 Markdown 格式
- 支持 API 调用

### read_file
- 用于读取本地文件内容
- **关键**：这是调用 Skills 的必要步骤
- 路径限制在项目目录内

### search_knowledge_base
- 用于在知识库中进行向量 + BM25 混合检索
- 仅包含各知识库子目录中已在前端「解析」的 .md / .txt / .pdf
- 适合查找特定的知识点或文档内容

### install_skill
- 安装新技能：从 URL 下载或提供内容创建
- 技能安装后下一轮对话自动生效

### remove_skill
- 删除已安装的技能

### list_skills
- 列出当前所有已安装技能的详情