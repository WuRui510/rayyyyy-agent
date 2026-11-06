"""假工具：原样返回输入。用来验证工具链路，不接数据库。"""

from errors import ToolResult
from tools.base import BaseTool


class EchoTool(BaseTool):
    name = "echo"
    description = "原样返回输入的内容。用来测试工具链路是否通畅。"
    parameters = {
        "type": "object",
        "properties": {"text": {"type": "string", "description": "要回显的文本"}},
        "required": ["text"],
    }

    def run(self, text: str) -> ToolResult:
        return ToolResult.success(text)