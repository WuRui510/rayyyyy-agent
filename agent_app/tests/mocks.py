"""
测试用加模型，无需联网，不花钱，可重复
"""

from collections.abc import Iterable

from llm import BaseLLM

class MockLLM(BaseLLM):
    def __init__(self, reply:str ="固定回复"):
        self.reply=reply
        self.calls:list[list]=[]

    def chat(self,messages:list, **kwargs) ->str:
        self.calls.append(list(messages))
        return self.reply

    def stream(self, messages:list, *kwargs) ->Iterable[str]:
        self.calls.append(messages)
        for ch in self.reply:
            yield ch