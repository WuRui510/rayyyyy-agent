"""
工具注册表：模型给出名字，这里给出对象

依赖方向：registry 只认识 BaseTool，不认识 loop / llm / 数据库。
一次程序运行一个实例，靠传参共享，不做模块级全局（那样测试会互相污染）。
"""

from tools.base import BaseTool


class ToolRegistry:
    """工具登记簿：{工具名: 工具实例}。"""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}#每个实例一个独立的字典

    def register(self, tool: BaseTool) -> None:
        """注册一个工具。
        传进去的永远是子类的实例，BaseTool本身永远不可能被传进来
        重名直接抛异常 —— 这是**装配期**的错误，必须当场发现。
        让它悄悄覆盖的话，你会以为两个都注册了，实际只有一个生效。
        「装配期失败要响，运行期失败要软」—— 和 get() 的取舍正好相反。
        BaseTool是一个抽象基类，无法被实例化
        Python 取属性时按 实例 → 自己的类 → 父类 逐级往上找：
        """
        if not tool.name:#tool.name 是空字符串,拦住忘了设name的工具
            raise ValueError(f"{type(tool).__name__} 没有设置 name，无法注册")#返回的是类的名字
        if tool.name in self._tools:
            raise ValueError(f"工具 {tool.name!r} 已经注册过了")
            #!r的意思是用repr()转换，而不是默认的str,把tool.name带上引号
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        """按名字取工具，取不到返回 None。

        不抛异常 —— 模型给出一个不存在的工具名是**预期内**的情况，
        应该由上层转成一条错误消息喂回去，而不是让程序崩掉。
        """
        return self._tools.get(name)

    def all(self) -> list[BaseTool]:
        """列出所有工具。

        用 list() 包一层：values() 返回的是活视图，
        直接给出去的话，调用方对返回值的修改会影响注册表本身。
        """
        return list(self._tools.values())

    def to_schemas(self) -> list[dict]:
        """一次性拿到全部工具的说明书，喂给 model 的 tools= 参数。"""
        return [t.to_schema() for t in self.all()]
        #self.all() —— 拿到所有工具实例,all()就是把值取出来拼成列表的函数
        #to_schema()是在BaseTool里实现的函数，其子类无需实现，都是用的父类的方法

    def __len__(self) -> int:
        return len(self._tools)


if __name__ == "__main__":
    from tools.builtin.echo import EchoTool

    r = ToolRegistry()

    print("=== 空表 ===")
    print("长度:", len(r))
    print("取不存在的工具:", r.get("nope"))

    print("\n=== 注册 echo 之后 ===")
    r.register(EchoTool())
    print("长度:", len(r))
    print("取 echo:", r.get("echo"))
    print("调用 run:", r.get("echo").run(text="联调 ok"))
    print("schemas 数量:", len(r.to_schemas()))

    print("\n=== 重名应该报错 ===")
    try:
        r.register(EchoTool())
        print("[FAIL] 重名居然没报错")
    except ValueError as e:
        print("[OK] 报错:", e)

    print("\n=== 没有 name 的工具应该报错 ===")

    class NamelessTool(BaseTool):
        description = "忘了设 name"
        parameters = {"type": "object", "properties": {}, "required": []}

        def run(self, **kwargs):
            return None

    try:
        r.register(NamelessTool())
        print("[FAIL] 没 name 居然注册成功了")
    except ValueError as e:
        print("[OK] 报错:", e)