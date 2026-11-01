"""W1 单元测试：llm.py 和 session.py

跑法：
    py -m pytest tests/ -v

⚠️ 只写了需要你自己补的断言，函数名已经给好。
   有 3 个测试不需要 API Key（标记了 no_api），可以随时跑。
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm import BaseLLM, DeepSeekLLM
from session import Session
from tests.mocks import MockLLM


# ============================================================
# 不需要 API Key 的测试
# ============================================================

def test_base_llm_is_abstract():
    """BaseLLM 是抽象类，不能直接实例化。"""
    with pytest.raises(TypeError):
        BaseLLM()


def test_session_init_has_system_message():
    s = Session(persona="你是助手")
    assert len(s.messages) == 1
    assert s.messages[0]["role"] == "system"
    assert s.messages[0]["content"] == "你是助手"


def test_session_add_messages():
    s = Session()
    s.add_user("你好")
    s.add_assistant("你好呀")
    assert len(s.messages) == 3
    assert s.messages[1]["content"] == "你好"
    assert s.messages[2]["role"] == "assistant"


def test_session_token_estimate_grows():
    s1, s2 = Session(), Session()
    s2.add_user("这是一段比较长的用户输入。" * 5)
    assert s2.token_estimate > s1.token_estimate


# ============================================================
# 需要 API Key 的测试（没配就自动跳过）
# ============================================================

HAS_KEY = bool(os.getenv("DEEPSEEK_API_KEY"))
skip_no_api = pytest.mark.skipif(not HAS_KEY, reason="需要 DEEPSEEK_API_KEY")


@skip_no_api #"如果没有 API Key，这个测试就别跑了，标成 SKIPPED。"
def test_chat_returns_string():
    """chat() 应该返回非空字符串。"""
    llm = DeepSeekLLM()
    out = llm.chat([{"role": "user", "content": "只回复两个字：收到"}])
    assert isinstance(out, str)
    assert len(out) > 0


@skip_no_api
def test_stream_yields_pieces():
    """stream() 应该 yield 多个非空字符串片段。"""
    llm = DeepSeekLLM()
    pieces = list(llm.stream([{"role": "user", "content": "数到三"}]))
    assert len(pieces) > 1
    assert all(isinstance(p, str) for p in pieces)

def test_mock_receives_full_history():
    m = MockLLM("好的")
    s = Session()
    s.add_user("第一句")
    s.add_assistant(m.chat(s.messages))
    s.add_user("第二句")
    m.chat(s.messages)

    assert len(m.calls) == 2
    assert len(m.calls[1]) == 4          # system + user + assistant + user
    assert m.calls[1][2]["role"] == "assistant"