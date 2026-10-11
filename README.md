# rayyyy-agent

> 一个 **Agent 开发**的学习仓库 —— 每周完成一个小项目，能力逐级递进，最终搭出完整的 Agent 全栈应用。

## 📌 这个仓库是什么

记录我从零开始学习 Agent 开发的全过程。核心思路是 **「每周一个小项目」**：

- 不追求"看完教程"，而是**每个概念都动手做出来**
- 每周的项目都在上周基础上递进，能力像台阶一样往上走
- 最终目标是能独立交付「**后端 + 前端 + Agent 逻辑 + 部署**」的完整应用

## 📂 项目列表

| 周次 | 项目 | 核心技术 | 状态 |
|---|---|---|---|
| **W1** | [CLI 大模型问答脚本](W1_cli_chat/) | LLM API 调用 · 流式输出 · 错误处理 | ✅ 完成 |
| W2 | 多轮对话助手 | 对话记忆 · 可配置人设 | 🚧 计划中 |
| W3 | 联网搜索工具 | Function Calling | 🚧 计划中 |
| W4 | FastAPI HTTP 服务 | 后端服务化 · 流式接口 | 🚧 计划中 |
| W5–W8 | RAG 检索增强 | embedding · 向量库 · 检索优化 | 🚧 计划中 |
| W9–W12 | Agent 化 + 全栈交付 | ReAct · 多工具编排 · 部署上线 | 🚧 计划中 |

## 🛠 技术栈

- **语言**：Python 3.10+
- **模型**：DeepSeek API（兼容 OpenAI 接口格式）
- **核心库**：`openai`、`python-dotenv`

## 🚀 快速开始

进入任意周项目目录，按该目录下的 `README.md` 操作。以 W1 为例：

```bash
cd W1_cli_chat
pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key
python main.py "你好"
```

## 📁 目录约定

```
.
├── README.md            # 本文件（仓库首页）
├── .gitignore           # 忽略 .env 等敏感/临时文件
├── W1_cli_chat/         # 第 1 周项目
│   ├── main.py
│   ├── README.md        # 该项目的说明
│   ├── 开发笔记.md       # 开发过程与踩坑记录（不公开，已 gitignore）
│   └── _test/           # 调试探针脚本（已 gitignore）
└── W2_.../              # 后续周项目
```

## 🔐 关于密钥

所有项目的 API Key 都放在各自的 `.env` 文件中，并已通过 `.gitignore` 排除：

- ✅ 仓库里**只有** `.env.example`（模板，不含真实 Key）
- ❌ `.env` **不会**进入版本库

## 📄 License

MIT
