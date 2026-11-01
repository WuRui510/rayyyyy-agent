# agent_app —— 建筑规范 Agent

> 一个从零搭建的分层 Agent 应用：命令行 / HTTP 双入口、可插拔工具、RAG 检索、MCP 双向集成。

## 现在的状态

**W1 完成  **（2026-10-18 ~ 10-29）：模型层 + 会话层
**W2 进行中**（2026-10-29 ~ 11-05）：模型层 + 会话层

## 为什么要这样分层

| 层 | 文件 | 职责 |
|---|---|---|
| 模型层 | `llm.py` | 只规定"能调模型"，不关心是哪家的模型 |
| 会话层 | `session.py` | 消息、token 估算、持久化 |
| 工具层 | `tools/` | Tool 接口 + 注册表 + 本地工具 + MCP 工具 |
| 循环层 | `loop/` | ReAct 循环（手写版 + LangGraph 版） |
| 检索层 | `rag/` | 文档切分、向量化、检索 |
| 压缩层 | `compaction.py` | token 预算驱动的上下文压缩 |
| 入口层 | `cli.py` / `api.py` | 命令行 / HTTP |
| 评测 | `eval/` | 测试集 + 指标 |

**核心设计：上层只依赖下层的抽象接口，不依赖具体实现。**
换模型不动机型层以上的代码；加工具不改循环层。

## 快速开始

```bash
# 1. 装依赖
py -m pip install -r requirements.txt

# 2. 配密钥
copy .env.example .env
# 然后编辑 .env，填入 DEEPSEEK_API_KEY

# 3. 跑自测
py llm.py

# 4. 跑测试
py -m pytest tests/ -v
```

## 开发进度

| 周 | 内容 | 状态 |
|---|---|---|
| W1 | 模型层 + 会话层 | 完成 |
| W2 | 命令行 + 多轮对话 | 进行中 |
| W3 | 工具层 + 注册表 | ⬜ |
| W4 | 手写 ReAct + LangGraph | ⬜ |
| W5 | RAG | ⬜ |
| W6 | RAG 工具化 + 最小评测 | ⬜ |
| W7 | MCP Client | ⬜ |
| W8 | MCP Server | ⬜ |
| W9 | 压缩层 | ⬜ |
| W10 | FastAPI | ⬜ |
| W11 | 多 Agent 编排 | ⬜ |
| W12 | 评测 + CI + Docker | ⬜ |
| W13 | README + demo | ⬜ |
