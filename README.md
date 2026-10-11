# rayyyy-agent

一个 Agent 开发的学习仓库 —— 每周完成一个小项目，能力逐级递进。

## 这个仓库是什么

记录 Agent 开发的全过程。核心思路是「每周一个小项目」：

- 不追求"看完教程"，而是每个概念都动手做出来
- 每周的项目在上一周基础上递进，能力像台阶一样往上走
- 最终目标是能独立交付「后端 + 前端 + Agent 逻辑 + 部署」的完整应用

## 项目列表

每完成一周，在表格末尾新增一行。

| 周次 | 项目 | 核心技术 |
|---|---|---|
| W1 | [CLI 大模型问答脚本](W1_cli_chat/) | LLM API 调用、流式输出、错误处理 |

## 整体路线

- **W1–W4**：LLM 应用与后端基础（API 调用 → 多轮对话 → 工具调用 → HTTP 服务）
- **W5–W8**：RAG 检索增强（embedding → 向量库 → 检索优化）
- **W9–W12**：Agent 化与全栈交付（ReAct → 多工具编排 → 部署上线）

## 技术栈

- 语言：Python 3.10+
- 模型：DeepSeek API（兼容 OpenAI 接口格式）
- 核心库：`openai`、`python-dotenv`

## 快速开始

进入任意周项目目录，按该目录下的 `README.md` 操作。以 W1 为例：

```bash
cd W1_cli_chat
pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key
python main.py "你好"
```

## 目录约定

```
.
├── README.md            本文件（仓库首页）
├── .gitignore           忽略 .env 等敏感 / 临时文件
├── .gitattributes       统一换行符
├── W1_cli_chat/         第 1 周项目
│   ├── main.py
│   ├── README.md        项目说明
│   ├── 开发笔记.md       开发过程记录（不公开，已 gitignore）
│   └── _test/           调试探针脚本（已 gitignore）
└── W2_.../              后续周项目
```

## 关于密钥

所有项目的 API Key 都放在各自的 `.env` 文件中，并已通过 `.gitignore` 排除：

- 仓库里只有 `.env.example`（模板，不含真实 Key）
- `.env` 不会进入版本库

## License

MIT
