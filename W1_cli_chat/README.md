# main.py —— 命令行大模型问答脚本

一个用 Python 写的命令行脚本：**在终端输入问题，调用 DeepSeek API，把回答打印出来。**

支持流式输出（打字机效果）、模型切换与错误处理。

---

## 这个脚本能做什么

- 在命令行里直接向大模型提问
- **流式输出**：逐字返回，像打字机一样，不用等整段生成完
- **切换模型**：`deepseek-flash`（快）/ `deepseek-v4-pro`（强）
- **友好报错**：出错时给一句人话提示，而不是甩一堆报错栈给用户

## 快速上手

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env            # Windows:  copy .env.example .env
```

然后用编辑器打开 `.env`，填入你的真实 Key：

```ini
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 3. 运行

```bash
python main.py "你好，介绍一下你自己"
```


## 使用方式

```
python main.py "你的问题" [--stream] [--model 模型名]
```

| 参数 | 必填 | 说明 |
|---|---|---|
| `"你的问题"` | ✅ | 要问的问题（**含空格必须加引号**） |
| `--stream` | — | 开启流式输出（打字机效果） |
| `--model 模型名` | — | 指定模型；不在白名单内会回退到默认并提示 |

**示例**：

```bash
python main.py "1+1 为什么等于 2"
python main.py "写一首关于秋天的诗" --stream
python main.py "解释一下快速排序" --model deepseek-v4-pro
python main.py                                        # 不带参数 → 打印用法
```

## 代码结构

脚本只有一个文件 `main.py`，共 4 个函数：

| 函数 | 作用 |
|---|---|
| `get_api_key()` | 从 `.env` 读取 API Key；读不到就提示并退出 |
| `ask(question, model)` | **非流式**调用：拿到完整回答后一次性打印 |
| `ask_stream(question, model)` | **流式**调用：逐字打印，打字机效果 |
| `main()` | 解析命令行参数 → 校验模型 → 调用 → 错误处理 |

## 执行流程

```
        命令行输入
             │
             ▼
   main() 解析 sys.argv
             │
      ┌──────┴──────┐
      │ 没给问题？    │── 是 ──→ 打印用法提示 → 退出
      └──────┬──────┘
             │ 否
             ▼
      取出问题、判断参数
             │
      ┌──────┴────────────┐
      │ 有 --model？       │── 是 ──→ 查白名单：合法就用 / 不合法回退默认并提示
      └──────┬────────────┘
             │
      ┌──────┴──────┐
      │ 有 --stream？│
      └──┬───────┬──┘
         │是      │否
         ▼        ▼
   ask_stream()  ask()
         │        │
         └───┬────┘
             ▼
      调用 DeepSeek API
             │
      ┌──────┴──────┐
      │   成功？     │
      └──┬───────┬──┘
         │是      │否
         ▼        ▼
      打印回答   按错误类型给出友好提示
```

## 实现要点

### 1. 流式输出（打字机效果）

```python
resp = client.chat.completions.create(..., stream=True)
for chunk in resp:
    piece = chunk.choices[0].delta.content
    if piece:                                 # 首尾 chunk 内容为空，需判空
        print(piece, end="", flush=True)      # 不换行 + 立即刷新
```

- 加了 `stream=True` 后，返回的是 **`Stream` 对象**（可循环），而不是 `ChatCompletion`
- 每一小片内容在 **`delta.content`**（注意不是 `message.content`）
- `flush=True` 是关键——不加会因输出缓冲而失去逐字效果

### 2. 错误处理

按「出问题的一方是谁」分类处理，而不是笼统地 `except Exception`：

| 异常 | 触发场景 | 状态码 | 可否重试 |
|---|---|---|---|
| `AuthenticationError` | API Key 无效 | 401 | ❌ 需改配置 |
| `APIConnectionError` | 网络不通 / 地址错误 | — | ✅ |
| `RateLimitError` | 请求过于频繁 | 429 | ✅ 稍后重试 |
| `APIStatusError` | 其他状态码（如 402 余额不足） | 多种 | 视情况 |
| `Exception` | 兜底 | — | — |

**捕获顺序**：具体异常 → `APIStatusError`（父类）→ `Exception` 兜底。
顺序不能乱，否则父类会「吃掉」子类，导致分不清错误类型。

### 3. 模型白名单校验

命令行传进来的模型名先查白名单，不合法就回退到默认模型并提示 ——
避免把 API 的 `400 Bad Request` 直接暴露给用户。

### 4. 密钥安全

API Key 通过 `python-dotenv` 从 `.env` 读取，`.env` 已列入 `.gitignore`：
**代码与密钥分离，不会随仓库泄露。**

## 文件说明

| 文件 | 用途 |
|---|---|
| `main.py` | 脚本本体 |
| `requirements.txt` | 依赖清单（`openai`、`python-dotenv`） |
| `.env.example` | Key 配置模板（不含真实 Key） |
| `.gitignore` | 忽略 `.env` 等敏感/临时文件 |
| `开发笔记.md` | 开发过程与踩坑记录 |
| `_test/` | 调试探针脚本（查看返回结构 / 类型 / 异常） |

## 已知限制

- 只支持**单轮问答**，没有对话记忆（每次都是全新对话）
- 没有自动重试（429 / 网络错误只提示，未做退避重试）
- 没有对话历史持久化

## 环境要求

- Python 3.10+
- 一个 [DeepSeek API Key](https://platform.deepseek.com/api_keys)

## 参考

- [DeepSeek API 文档](https://api-docs.deepseek.com/zh-cn/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)（DeepSeek 兼容其接口格式）
