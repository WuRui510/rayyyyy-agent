"""
【W1】可观测性 —— 日志 / trace / token 统计

为什么个人项目也要做这个？

    因为面试官问「线上出问题你怎么查」的时候，
    "我打了很多 print" 和 "我有结构化日志和 trace_id" 是两种人。

    而且更实际的原因：**LLM 调用是按 token 计费的**。
    不统计，你根本不知道一次问答花了多少钱、哪个环节最贵。

【要做的】
    1. setup_logging()    结构化日志配置
    2. trace()            装饰器：生成 trace_id，记录耗时
    3. TokenCounter       累计 token 与费用预估
"""

import logging
import time
import uuid #用于生成唯一ID的标准库
from functools import wraps

logger = logging.getLogger("agent")


# ============================================================
# 1. 日志
# ============================================================

def setup_logging(level: str = "INFO") -> None:
    """配置日志格式。

    
        用 logging.basicConfig 配置，格式建议包含：
            时间 | 级别 | 模块名 | 消息
        格式串参考：
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"

        ⚠️ 注意：basicConfig 只生效一次，重复调用不会改格式。
           这在测试里会坑你（测试改了日志级别影响其他测试）。
    """
    
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )
    #raise NotImplementedError("setup_logging 未完成")


# ============================================================
# 2. trace 装饰器
# ============================================================

def trace(name: str | None = None):
    """给函数加 trace：生成短 id，记录进入/退出和耗时。
    给任何函数加一次记录日志与记时

    
        1. 每次调用生成一个 8 位短 id（uuid4().hex[:8]）
        2. 进入时 log：`[a1b2c3d4] -> chat 开始`
        3. 结束时 log：`[a1b2c3d4] <- chat 完成 1234ms`
        4. 抛异常时 log：`[a1b2c3d4] !! chat 失败 500ms: <错误>`
        5. 用 functools.wraps 保留原函数名
        6. 重新抛出异常（不要吞掉）

    ⚠️ 注意：这个装饰器要能同时包普通函数和生成器函数。
       生成器的情况和 with_retry 一样——第一次返回的是生成器对象，
       真正的执行发生在迭代时。想清楚怎么处理（或者先接受这个限制，
       记进 docs/W1.md）。
    """
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            label = name or func.__name__
            tid = uuid.uuid4().hex[:8]
            logger.info("[%s] -> %s 开始", tid, label)
            start = time.perf_counter()

            try:
                result = func(*args, **kwargs) #执行原函数（成功路径）
            except Exception as e:
                ms = (time.perf_counter()-start) * 1000
                logger.warning("[%s] !! %s 失败 %.0fms: %s", tid, label, ms, e)
                raise #把异常重新抛出，traceback完整保留

            ms = (time.perf_counter()-start) * 1000
            logger.info("[%s] <- %s 完成 %.0fms", tid, label, ms)
            return result
        return wrapper
    return decorator

    #raise NotImplementedError("trace 未完成")


# ============================================================
# 3. token 统计
# ============================================================

class TokenCounter:
    """累计 token 用量与费用。

    TODO：
        1. __init__ 里初始化 prompt_tokens / completion_tokens / calls
        2. add(prompt: int, completion: int) 累加，并 log 一次
        3. property total 返回 prompt + completion
        4. property cost 按单价估算费用
           （DeepSeek 的单价自己去查，写进注释，别瞎编）

    ⚠️ 数据从哪来？
       OpenAI 兼容接口的 response.usage 里有 prompt_tokens / completion_tokens。
       流式响应要额外加参数才能拿到 usage，这块 W1 可以先不做，
       等 W2 跑通流式之后再补。先留接口。
    """

    # TODO: 实现


if __name__ == "__main__":
    setup_logging("DEBUG") ## ← 必须在任何日志产生之前,测试脚本的前置开关
    #五种日志级别从低到高 ： DEBUG  INFO    WARNING ERROR   CRITICAL

    @trace()
    def demo(x: int) -> int:
        time.sleep(0.05)
        return x * 2

    @trace("自定义名字")
    def boom():
        raise ValueError("模拟失败") #抛出

    print("结果:", demo(21))
    try:
        boom()
    except ValueError as e: #捕获
        print("抛出:", e)
