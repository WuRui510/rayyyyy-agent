# main.py —— 多轮对话助手

一个用 Python 写的命令行对话脚本：**能连续聊天、记得上下文、有固定人设，对话还能存下来下次接着聊。**

## 这个脚本能做什么

- **连续对话**：不是一问一答就结束，可以一直聊下去
- **记得上下文**：能记住前面说过的话
- **可配置人设**：启动时用 `--persona` 指定角色
- **会话命令**：`/exit` 退出、`/clear` 清空历史、`/history` 查看历史
- **历史持久化**：对话自动存进 `history.json`，下次启动可以继续上次的对话

## 和 W1 的区别

| | W1（单轮） | W2（多轮） |
|---|---|---|
| 交互方式 | 问一句、答一句，程序就结束 | 连续对话，直到输入 `/exit` |
| 上下文 | 每次都是全新对话 | 记得前面说过的内容 |
| 人设 | 写死在代码里 | 可通过 `--persona` 配置 |
| 对话历史 | 不存在 | 维护在 `messages` 列表里 |
| 持久化 | 无 | 存进 `history.json`，可跨次启动续聊 |

## 快速上手

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env            # Windows:  copy .env.example .env
```

然后用编辑器打开 `.env`，填入真实 Key：

```ini
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 3. 运行

```bash
python main.py
```

## 使用方式

```
python main.py [--model 模型名] [--persona 人设]
```

| 参数 | 必填 | 说明 |
|---|---|---|
| `--model 模型名` | — | 指定模型；不在白名单内会回退到默认并提示 |
| `--persona 人设` | — | 指定 AI 的人设（如 `"你是一个资深建筑师"`）；不传则用默认人设 |

**示例**：

```bash
python main.py
python main.py --model deepseek-v4-pro
python main.py --persona "你是一个资深建筑师，回答简洁专业"
```

## 对话内命令

进入对话后，除了正常提问，还支持：

| 命令 | 作用 |
|---|---|
| `/exit` | 退出程序（对话已自动保存） |
| `/clear` | 清空对话历史（内存和文件都清），重新开始 |
| `/history` | 打印当前对话历史 |

## 代码结构

对话逻辑在 `main.py`，存储逻辑单独放在 `storage.py`：

| 函数 | 作用 |
|---|---|
| `get_api_key()` | 从 `.env` 读取 API Key（沿用 W1） |
| `build_messages(persona)` | 构造初始对话历史（只含一条 system 人设消息） |
| `ask(messages, model)` | 调用 API，**返回**回答文本（不打印） |
| `chat_loop(model, persona)` | 交互循环：读输入 → 调 API → 打印 → 记录历史 → 存档 |
| `main()` | 解析命令行参数 → 进入对话循环 |
| `storage.save_history()` | 把历史写入 `history.json` |
| `storage.load_history()` | 读回历史；文件不存在或损坏时返回 `None` |
| `storage.clear_history_file()` | 删除历史文件 |

> **为什么把存储单独拆成模块？** 让 `main.py` 只管对话逻辑，文件读写这种"工具活"独立出去。
> 好处是：以后想换成 SQLite / MySQL 存储，**只要重写 `storage.py`，`main.py` 一行都不用改**。

## 执行流程

```
        启动
         │
         ▼
  main() 解析参数（--model / --persona）
         │
         ▼
  chat_loop() 进入循环
         │
         ├─ ① 读历史：load_history()
         │     成功 → 用文件里的历史
         │     失败 → build_messages(persona) 新建
         │
         └─ while True:
              │
              input("你：") 读一行输入
              │
              ├─ /exit    → save_history() 保存 → 退出循环
              ├─ /clear   → 重置内存 + clear_history_file() 删文件
              ├─ /history → 打印 history，继续下一轮
              │
              └─ 普通提问
                   history.append({"role": "user", ...})        ← 用户输入进历史
                   answer = ask(history)                        ← 带上【完整历史】调用
                   print(answer)
                   history.append({"role": "assistant", ...})   ← AI 回答也进历史
                   save_history(history)                        ← ② 存盘
```

## 实现要点

### 1. `messages` 就是「对话历史」

它不是"一次请求的参数"，而是**从对话开始到现在的全部记录**：

```python
history = [
    {"role": "system",    "content": "你是一个资深建筑师"},   # 人设
    {"role": "user",      "content": "四合院是什么"},          # 第 1 轮问
    {"role": "assistant", "content": "四合院是..."},          # 第 1 轮答
    {"role": "user",      "content": "那它有什么缺点"},        # 第 2 轮问
]
```

### 2. API 是「无状态」的 —— 这是 W2 的核心

**服务器不记得你上一轮说了什么。** 所谓"记忆"，**完全是客户端自己维护的**：

> 每轮请求，都要把**完整历史**重新发一遍。

如果漏掉了 `assistant` 那条（没把 AI 的回答记进历史），AI 下一轮就会"不记得自己刚说过什么"。

### 3. 人设靠 `system` 消息

`system` 消息放在历史第一条，用来设定 AI 的身份和风格。**用户看不到它，但它决定了所有回答的调性。**

### 4. 持久化：用 JSON 文件存历史

- 存：`json.dump(history, f, ensure_ascii=False)` —— **`ensure_ascii=False` 不能省**，否则中文会变成 `\uXXXX` 转义码
- 读：文件不存在时返回 `None`（**第一次运行是正常情况，不该让程序崩掉**）
- `/clear` 时**内存和文件都要清** —— 只清一个，下次启动会"复活"

> **设计取舍**：JSON 文件适合单人单会话；如果以后要做多用户、多会话、需要查询统计，
> 就该换成数据库（SQLite / MySQL）—— 那正是 **W10 的任务**。

## 已知限制

- 历史会不断变长，**没有做长度控制**（对话很长时可能超出模型的上下文上限）
- 单会话：只有一份 `history.json`，不支持多个会话并存
- 仍是命令行界面

## 环境要求

- Python 3.10+
- 一个 [DeepSeek API Key](https://platform.deepseek.com/api_keys)

## 参考

- [DeepSeek API 文档](https://api-docs.deepseek.com/zh-cn/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)（DeepSeek 兼容其接口格式）
