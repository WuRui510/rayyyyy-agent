"""
【W1】错误层 —— 统一异常类型 + 工具返回协议

这个文件解决两个问题：

问题一：异常没有分类
    W1 里你在 main() 里 except 了五种异常，那是"在入口兜底"。
    但库代码里应该抛"自己定义的"异常，让上层能区分：
        LLM 挂了     → 可以重试
        配置错了     → 重试一万次也没用，直接退出
        工具失败了   → 不一定要中断，可以告诉模型

问题二：工具失败怎么办 ⭐ 这是 Agent 工程的核心
    普通程序：工具失败 → 抛异常 → 整个流程中断
    Agent 程序：工具失败 → **把错误当作工具结果返回给模型**
                → 模型自己决定：重试？换个工具？还是告诉用户「我查不到」？

    ⚠️ 这就是 Agent 和普通程序的根本差别之一。
       面试问「工具调用失败怎么办」，答这个。

【要做的】
    1. 异常类层次
    2. ToolResult 协议（不是抛异常，而是返回结果对象）
"""

from dataclasses import dataclass #dataclass = 「这个类主要是装数据」的声明


# ============================================================
# 1. 异常层次
# ============================================================

class AgentError(Exception): #xception = 「这是一个普通错误」的标记。 你的类继承它，就获得了「能被 raise / except」的资格。
    """所有自定义异常的基类。

    好处：上层可以 `except AgentError` 一把抓住自己的错，
          而不会误伤 KeyboardInterrupt 之类的系统异常。
    """


class ConfigError(AgentError):
    """配置问题（缺 key、地址写错）。重试没有意义，应该直接退出。"""


class LLMError(AgentError):
    """模型调用失败。

    TODO：想一想为什么要单独分出来？
          （提示：它可能是"可重试"的，也可能是"不可重试"的，
           所以可以再加一个 retryable 字段或者用子类区分）
    """


class ToolError(AgentError):
    """工具执行失败。**注意：这个异常通常不应该往上抛**，
    而应该被包装成 ToolResult 回填给模型。详见下面。
    """


# ============================================================
# 2. 工具返回协议
# ============================================================

@dataclass
class ToolResult:
    """工具的执行结果。

    为什么不用"成功返回字符串 / 失败抛异常"？
        因为失败也是信息，模型需要知道失败原因才能决策。

    
        1. 定义三个字段：
               ok: bool           # 是否成功
               content: str       # 成功时的内容（喂给模型的文本）
               error: str = ""    # 失败原因
        2. 加两个类方法方便构造：
               @classmethod ok_result(cls, content: str) -> "ToolResult"
               @classmethod fail(cls, error: str) -> "ToolResult"

    ⚠️ 注意：字段名和类方法名不能都叫 ok，会冲突。
       类方法建议叫 success。
    """

    
    ok: bool #不给默认值,必填字段，强制每次都必须判断成功还是失败
    content: str = ""
    error: str = ""

    @classmethod #把方法变成属于类的方法，而不是属于实例的方法,调用前不用构造实例
    def success(cls, content: str) ->"ToolResult":
        return cls(ok = True, content=content)

    @classmethod
    def fail(cls, error: str) -> "ToolResult":
        return cls(ok = False, error = error)

    def to_text(self) -> str:
        return self.content if self.ok else f"[TOOL_ERROR] {self.error}"





if __name__ == "__main__":
    ok = ToolResult.success("查到 3 条规范条款")
    bad = ToolResult.fail("知识库连接超时")

    print("对象 :", ok)
    print("对象 :", bad)
    print("文本 :", ok.to_text())
    print("文本 :", bad.to_text())
    print("布尔 :", ok.ok, bad.ok)
