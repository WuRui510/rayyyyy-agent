"""
【W1】模型层 —— 接口 + 实现分离

这个文件要解决的问题：
    W1 项目里你是直接 `new OpenAI(...)` 然后调 `create()`。
    那样一旦要换模型厂商（从 DeepSeek 换到通义千问），
    上层所有调用代码都要改。

    所以这里把它拆开：
        BaseLLM    ← 抽象接口，只规定"能做什么"
        DeepSeekLLM ← 具体实现，管"怎么做"

    上层（loop.py / cli.py）只依赖 BaseLLM，永远不认识 DeepSeekLLM。

【要实现的 3 个东西】
    1. BaseLLM      抽象基类（chat / stream 两个抽象方法）
    2. DeepSeekLLM  具体实现（搬 W1 的 ask / ask_stream）
    3. with_retry   重试装饰器（连接错误重试，鉴权错误不重试）

【验收】
    llm = DeepSeekLLM(api_key="sk-xxx")
    llm.chat([{"role": "user", "content": "你好"}])   → 返回字符串
    for c in llm.stream([...]): print(c, end="")       → 有打字机效果
"""

import time
import logging
from abc import ABC, abstractmethod 
from collections.abc import Iterator
from functools import wraps

from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)

from errors import LLMError
from config import get_settings   
from observability import setup_logging, trace

logger = logging.getLogger(__name__) 


# ============================================================
# 1. 抽象接口
# ============================================================

class BaseLLM(ABC): #抽象类，继承了ABC这个基类，继承它，这个类就是抽象类
    """所有模型实现的共同接口。

    上层只依赖这个类，所以它必须把"能力"描述清楚：
      - chat(messages)        一次性返回完整回答
      - stream(messages)      流式返回（生成器）

    用 @abstractmethod 定义这两个方法。
          注意 stream 是生成器，所以它是 yield 而不是 return。
    """

    @abstractmethod
    def chat(self, messages: list[dict  ], **kwargs) -> str:
        """传入 messages 列表，返回完整回答字符串。"""
        raise NotImplementedError   #Fail loud, not silent. 宁可响亮地报错，也不要静默地返回错东西。
        #万一以后有人写子类时想 super().chat()，会立刻得到清晰报错

    @abstractmethod
    def stream(self, messages: list[dict], **kwargs) -> Iterator[str]:
        """传入 messages 列表，逐块 yield 文本。"""
        raise NotImplementedError


# ============================================================
# 2. 重试装饰器
# ============================================================

def with_retry(max_attempts: int = 3, base_delay: float = 1.0):
    """重试装饰器。

    规则（来自 W1 的 except 分类，但升级成"分类处理"）：
        APIConnectionError / RateLimitError  → 可重试，指数退避
        AuthenticationError                  → 不可重试，立即抛（换个网络也没用）
        APIStatusError 且 402（余额不足）     → 不可重试
        其他                                 → 不重试，直接抛

    提示：指数退避就是第 n 次重试前等 base_delay * 2**(n-1) 秒。

    实现这个装饰器（用 functools.wraps 保留原函数名）。
    """
    max_attempts = max(1, max_attempts)
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1,max_attempts+1):

                try:
                    return func(*args, **kwargs)
                
                except (APIConnectionError,RateLimitError) as e:
                    if attempt == max_attempts:
                        raise LLMError(
                            f"{func.__name__}已重试{max_attempts}次仍然失败：{e}"
                        ) from e
                    delay = base_delay*2**(attempt-1)
                    logger.warning(
                        "[%d/%d]%s, %.1fs后重试",
                        attempt,max_attempts,type(e).__name__,delay,
                    )
                    time.sleep(delay)

                except AuthenticationError as e:
                    raise LLMError(
                        f"{func.__name__}鉴权失败，检查DEEPSEEK_API_KEY：{e}"
                    ) from e

                except APIStatusError as e:
                    if e.status_code == 402:
                        raise LLMError(f"{func.__name__}账户余额不足：{e}") from e
                    raise LLMError(
                        f"{func.__name__}接口返回{e.status_code}:{e}"
                    ) from e
        return wrapper
    return decorator

    #raise NotImplementedError("with_retry 未完成")


# ============================================================
# 3. DeepSeek 实现
# ============================================================

class DeepSeekLLM(BaseLLM):
    """DeepSeek 的具体实现。

    这里做的就是把 W1 的 ask / ask_stream 搬过来，
    但有三处改动：
        ① 参数从 question 改成 messages（因为要支持多轮）
        ② stream 从 print 改成 yield（因为上层要自己决定怎么输出）
        ③ 异常处理从"在 main 里 catch"改成"在装饰器里分类重试"
    """

    def __init__(
        self, api_key=None, base_url=None, model=None
    ):
        """初始化。
            2. 读不到就抛 ValueError（注意：不要在库代码里 sys.exit）
            3. 创建 self._client = OpenAI(api_key=..., base_url=...)
            4. 保存 self.model
        """
        
        s = get_settings()

        self._client = OpenAI(
            api_key=api_key or s.deepseek_api_key, 
            base_url=base_url or s.base_url,
            max_retries=0,
        )
        #self._client 带下划线 Python 约定：内部属性，外部不该直接用。外部只用 chat() / stream()
        self.model = model or s.model       #传就从 config 取（None or s.xxx → 取右边）
        self.timeout = s.llm_timeout        #后面 chat() 要用
        #raise NotImplementedError("DeepSeekLLM.__init__ 未完成")


    #语法糖的本质：把函数当参数传进去，拿一个"改装过的函数"出来
    @trace()
    @with_retry()   #装饰器，给函数加"失败自动重试"，加括号相当于再套一层，可以传参，饰是"定义时"完成的。
    def chat(self, messages: list, **kwargs) -> str:
        """一次性返回。
        """
        
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,  # # 调用方传完整列表
            timeout=self.timeout,
            **kwargs,
        )
        return resp.choices[0].message.content
        #raise NotImplementedError("DeepSeekLLM.chat 未完成")

    def stream(self, messages: list, **kwargs) -> Iterator[str]:
        """流式返回。

        搬 W1 的 ask_stream()，关键改动：
              - `stream=True` 保留
              - 把 `print(piece, end="")` 改成 `yield piece`
              - 注意要过滤掉 None（W1 里那个 `if piece:` 的判断）

        ⚠️ 这里有个容易被忽略的点：
            生成器函数里一旦出现 yield，整个函数体就变成"惰性"的。
            也就是说 with_retry 装饰器包住的其实只是"创建生成器"这一步，
            真正迭代时的异常不在重试范围内。
            → 想一想怎么处理？先跑通再说，这一条放到 docs/W1.md 里记下来。
        """
        
        resp = self._client.chat.completions.create(
            model = self.model,
            messages = messages,
            timeout = self.timeout,
            stream = True,
            **kwargs,
        )
        try:

            for chunk in resp:
                if not chunk.choices:
                    continue
                piece = chunk.choices[0].delta.content
                if piece:
                    yield piece
        finally:
            resp.close()
        #raise NotImplementedError("DeepSeekLLM.stream 未完成")


# ============================================================
# 自测（写完直接 py llm.py）
# ============================================================

if __name__ == "__main__":
    setup_logging("INFO")

    llm = DeepSeekLLM()
    msgs = [{"role": "user", "content": "你是哪个型号"}]

    print("[chat]", llm.chat(msgs))

    print("[stream] ", end="")
    for piece in llm.stream(msgs):
        print(piece, end="", flush=True)
    print()

    print("\n--- 断网模拟 ---")
    bad = DeepSeekLLM(base_url="http://127.0.0.1:9")
    try:
        bad.chat(msgs)
    except LLMError as e:
        print("最终抛出 LLMError：", e)