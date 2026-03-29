# Mini-OpenClaw

轻量级本地 AI Agent 系统 —— 拥有"真实记忆"的数字副手。

## 核心特性

- **文件即记忆**：所有对话、反思以 Markdown/JSON 文件形式存在，完全人类可读
- **技能即插件**：通过文件夹结构管理 Agent Skills，"拖入即用"
- **透明可控**：System Prompt 拼接、工具调用、记忆读写完全透明

## 技术架构

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python 3.10+) |
| Agent 引擎 | LangChain 1.x (`create_agent`) |
| RAG 检索 | LlamaIndex (BM25 + 向量混合检索) |
| 前端框架 | Next.js 14+ (App Router, TypeScript) |
| UI | Tailwind CSS, Lucide Icons, Monaco Editor |
| 模型接口 | 兼容 OpenAI API 格式 |

## 快速开始

### 1. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入你的 API Key 和模型配置
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
python app.py
```

后端服务将在 `http://localhost:8002` 启动。

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端将在 `http://localhost:3000` 启动。

## 项目结构

```
mini-openclaw/
├── backend/                    # FastAPI 后端
│   ├── app.py                  # 入口文件 (Port 8002)
│   ├── config.py               # 配置管理
│   ├── tools/                  # 5 个核心工具
│   │   ├── terminal.py         # Shell 命令
│   │   ├── python_repl.py      # Python 解释器
│   │   ├── fetch_url.py        # 网页获取
│   │   ├── read_file.py        # 文件读取
│   │   └── rag_search.py       # RAG 知识检索
│   ├── graph/                  # Agent 核心逻辑
│   │   ├── agent.py            # create_agent 构建
│   │   ├── prompt.py           # System Prompt 拼接
│   │   └── skills_scanner.py   # Skills 扫描器
│   ├── workspace/              # 人格与记忆文件
│   │   ├── SOUL.md             # 核心设定
│   │   ├── IDENTITY.md         # 自我认知
│   │   ├── USER.md             # 用户画像
│   │   └── AGENTS.md           # 行为准则
│   ├── memory/                 # 记忆存储
│   │   └── MEMORY.md           # 长期记忆
│   ├── sessions/               # 会话 JSON 记录
│   ├── skills/                 # Agent Skills
│   │   └── get_weather/        # 示例技能
│   │       └── SKILL.md
│   ├── knowledge/              # RAG 知识库文档
│   └── storage/                # 持久化索引
│
├── frontend/                   # Next.js 前端
│   └── src/
│       ├── app/                # App Router
│       ├── components/         # 组件
│       │   ├── chat/           # 对话面板
│       │   ├── editor/         # Monaco 编辑器
│       │   ├── sidebar/        # 侧边栏
│       │   └── navbar/         # 导航栏
│       └── lib/                # API 客户端 & 类型
│
└── PRD.md                      # 需求文档
```

## API 接口

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | `/api/chat` | 对话 (支持 SSE 流式) |
| GET | `/api/files?path=...` | 读取文件 |
| POST | `/api/files` | 保存文件 |
| GET | `/api/sessions` | 会话列表 |
| POST | `/api/sessions` | 创建会话 |
| DELETE | `/api/sessions/{id}` | 删除会话 |
| GET | `/api/skills` | 技能列表 |
| GET | `/api/file-tree` | 文件树 |

## 模型配置

支持所有兼容 OpenAI API 格式的模型服务：

| 服务 | OPENAI_BASE_URL | 示例 MODEL_NAME |
|------|-----------------|-----------------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| OpenRouter | `https://openrouter.ai/api/v1` | `anthropic/claude-3.5-sonnet` |

## 添加新技能

1. 在 `backend/skills/` 下创建新文件夹
2. 添加 `SKILL.md` 文件，包含 Frontmatter 元数据和使用说明
3. 重启后端服务，技能自动注册

```markdown
---
name: my_skill
description: 技能描述
---

# 技能名称

## 使用步骤
1. ...
2. ...
```

## 开发者

**天行者** · [代码仓库](https://github.com/tianxingzhe-source)
