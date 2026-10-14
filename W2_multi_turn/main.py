"""
W2 项目：多轮对话助手（记忆 + 人设 + 持久化）

用法：
    py main.py
    py main.py --model deepseek-v4-pro
    py main.py --persona "你是一个资深算法工程师，回答简洁专业"

进入对话后，支持以下命令：
    /exit      退出
    /clear     清空对话历史（重新开始）
    /history   查看当前对话历史
"""

import os
import sys

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)

# 步骤 6 会用到（做前 5 步时可以先忽略这个导入）
from storage import clear_history_file, load_history, save_history

AVAILABLE_MODELS = ["deepseek-flash", "deepseek-v4-pro"]
DEFAULT_MODEL = "deepseek-flash"
DEFAULT_PERSONA = "你是一个乐于助人的助手。"


def get_api_key() -> str:
    load_dotenv()
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        sys.exit("错误：没有找到 DEEPSEEK_API_KEY，请检查 .env 文件")
    return key


# ============================================================
# 步骤 1~4 在这个文件里实现
# 步骤 5 在 storage.py 里实现
# 步骤 6 回到 chat_loop() 把两者接起来
# ============================================================


def build_messages(persona: str) -> list:
    """构造初始的对话历史—— 只包含一条 system 消息。
    """

    return [{"role":"system","content":persona}]

def ask(messages: list, model: str = DEFAULT_MODEL) -> str:
    """
   注意和 W1 的 ask() 有【三处不同】：

        1. 参数是 messages列表，而不是单个 question
        2. 直接把整个列表传给 API,不用在函数内部拼 messages
        3. 用 return 把文本返回出去，而不是 print, 因为调用者需要把这段回答存进历史
    """
   
    client = OpenAI(api_key=get_api_key(),base_url="https://api.deepseek.com")
    resp = client.chat.completions.create(
        model = model,
        messages=messages
        #w1是直接在messages里构造，与这里不同
    )
    return resp.choices[0].message.content
    


def chat_loop(model: str, persona: str) -> None:
    """步骤 3 + 步骤 6交互循环、维护历史、接入持久化。

    ⚠️ 分两次做：先把步骤 3 跑通（纯内存的多轮对话），再加步骤 6 的持久化。

    ========== 步骤 3：交互循环 + 维护历史 ==========

        ① 初始化历史

        ② 进入无限循环，每次用 input() 读一行用户输入

        ③ 先判断是不是命令：
             /exit     → 打印告别语，退出循环
             /clear    → 清空历史（重新 build_messages），提示"已清空"，继续下一轮
             /history  → 打印当前 history 的全部内容，继续下一轮

        ④ 普通提问时：
             把用户输入加进历史 → 调用 ask() → 打印回答
             ⚠️ 然后【还要往历史里加什么？想一想】
                （提示：如果漏了这一步，AI 下一轮会不记得自己刚说过什么）

    ========== 步骤 6：接入存储（用步骤 5 写好的 storage.py） ==========

        步骤 5 写完的 storage.py 里有 3 个函数：

        要「接」进 4 个地方：

        ① 启动时 —— 优先读文件，读不到才新建：

        ② 每轮问完后 —— 存一次

        ③ 收到 /clear 时 —— 内存和文件都要清
    
        ④ 收到 /exit 时—— 再存一次当保险

        想一想：载入历史后，命令行的 --persona 还要不要生效？
    """
    # TODO: 实现步骤 3
    raise NotImplementedError("步骤 3 未完成")

    # TODO: 实现步骤 6（在步骤 3 跑通、且步骤 5 写完 storage.py 之后再做）
    # raise NotImplementedError("步骤 6 未完成")


def main() -> None:
    """【步骤 4】解析命令行参数 → 进入对话循环。

    TODO：和 W1 的 main() 很像，但有三处变化：

        1. 不再需要"问题"参数了 —— 问题在对话循环里输入
        2. 新增 --persona 参数（可选）：用来指定人设
           没传就用 DEFAULT_PERSONA
        3. 最后调用 chat_loop(model, persona)，而不是 ask()

    --model 的处理方式和 W1 一样（找位置 → 取下一个 → 查白名单 → 不合法回退默认并提示）。

    注意：这次不传参数是【正常情况】（不是用法错误），
         直接进对话就行，不要再打印"用法提示"。
    """
    # TODO: 实现步骤 4
    raise NotImplementedError("步骤 4 未完成")


if __name__ == "__main__":
    main()
