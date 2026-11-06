"""工具层的基类。

所有工具都继承它。三个描述字段给模型看，run() 给自己写。
"""

from abc import ABC, abstractmethod

from errors import ToolResult


class BaseTool(ABC):
    """所有工具的基类。

    子类必须做两件事：
      1. 覆盖 name / description / parameters
      2. 实现 run()
    """

    name: str = ""
    description: str = ""
    parameters: dict = {"type": "object", "properties": {}, "required": []}

    @abstractmethod
    def run(self, **kwargs) -> ToolResult:
        """执行工具。

        失败要返回 ToolResult.fail(...)，不要抛异常 ——
        抛出去模型就看不见错误原因了。
        """
        raise NotImplementedError

    def to_schema(self) -> dict:
        """转成 OpenAI tools 参数格式。"""
        
        return{
            "type":"function",
            "function":{
                "name":self.name,
                "description":self.description,
                "parameters":self.parameters,
            },
        }
        #raise NotImplementedError