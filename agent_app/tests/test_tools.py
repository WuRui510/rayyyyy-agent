"""W2 单元测试：工具层（BaseTool / EchoTool / ToolRegistry）

跑法：
    py -m pytest tests/ -v

这几个测试全都不依赖数据库、不依赖网络、不依赖 API Key，随时能跑。

⚠️ 每个测试都自己 new 一个 ToolRegistry()，不复用全局状态 ——
   这正是今天选择「实例而不是模块级全局」的原因：
   如果注册表是模块级的，test_a 注册的工具会留到 test_b，而且从报错信息
   里完全看不出真正的原因。
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from errors import ToolResult
from tools.base import BaseTool
from tools.builtin.echo import EchoTool
from tools.registry import ToolRegistry


# ============================================================
# BaseTool：抽象契约
# ============================================================

def test_base_tool_is_abstract():
    """BaseTool 有抽象方法，不能直接实例化。"""
    with pytest.raises(TypeError):
        BaseTool()


def test_subclass_missing_run_is_abstract():
    """子类没实现 run() 也不能实例化 —— 早崩早发现。"""
    class IncompleteTool(BaseTool):
        name = "incomplete"
        description = "忘了实现 run"
        parameters = {"type": "object", "properties": {}, "required": []}

    with pytest.raises(TypeError):
        IncompleteTool()


def test_echo_tool_schema_shape():
    """to_schema() 的输出必须是 OpenAI tools 要求的嵌套结构。"""
    schema = EchoTool().to_schema()

    assert schema["type"] == "function"
    assert "function" in schema
    assert schema["function"]["name"] == "echo"
    assert schema["function"]["description"]
    assert schema["function"]["parameters"]["required"] == ["text"]


def test_echo_tool_run_returns_tool_result():
    """run() 返回 ToolResult，不是裸字符串。"""
    result = EchoTool().run(text="你好")

    assert isinstance(result, ToolResult)
    assert result.ok is True
    assert result.content == "你好"
    assert result.to_text() == "你好"


# ============================================================
# ToolRegistry：注册 / 查找 / 隔离
# ============================================================

def test_registry_register_and_get():
    """注册后能按 name 取回同一个对象。"""
    r = ToolRegistry()
    tool = EchoTool()
    r.register(tool)

    assert len(r) == 1
    assert r.get("echo") is tool
    assert r.all() == [tool]


def test_registry_get_missing_returns_none():
    """取不到返回 None，不抛异常 —— 模型幻觉出不存在的工具名是预期内的。"""
    r = ToolRegistry()
    assert r.get("nope") is None


def test_registry_duplicate_name_raises():
    """重名必须抛异常 —— 这是装配期的错误，不能悄悄覆盖。"""
    r = ToolRegistry()
    r.register(EchoTool())

    with pytest.raises(ValueError, match="已经注册过"):
        r.register(EchoTool())


def test_registry_nameless_tool_raises():
    """忘了设 name 的工具必须被拦下来，否则它注册进去后永远取不出来。"""
    class NamelessTool(BaseTool):
        description = "忘了设 name"
        parameters = {"type": "object", "properties": {}, "required": []}

        def run(self, **kwargs) -> ToolResult:
            return ToolResult.success("never called")

    r = ToolRegistry()
    with pytest.raises(ValueError, match="没有设置 name"):
        r.register(NamelessTool())


def test_registry_to_schemas():
    """to_schemas() 产出与工具数量一致，且每项都是合法 schema。"""
    r = ToolRegistry()
    r.register(EchoTool())

    schemas = r.to_schemas()
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "echo"


def test_registry_instances_are_isolated():
    """两个 ToolRegistry 互不影响 —— 这是「不用模块级全局」的回归测试。

    如果哪天有人把 _tools 挪到类属性或者模块级变量，这个测试会挂。
    """
    a = ToolRegistry()
    b = ToolRegistry()

    a.register(EchoTool())

    assert a.get("echo") is not None
    assert b.get("echo") is None
    assert a._tools is not b._tools
