"""
【W1】会话层 —— 消息 + token 估算 + 持久化

这个文件要解决的问题：
    W2 项目里你用"裸 list"存历史，能用但有两个问题：
      ① 没有地方放 session_id —— 多个会话分不开
      ② 不知道历史有多长 —— 只能等它真的超了才报错

    所以把它升级成一个对象：Session

【要实现的 4 个东西】
    1. Session 类
       - messages: list[dict]      真正的历史
       - session_id: str           会话标识
       - 方法 add_user / add_assistant / add_system
       - 属性 token_estimate       粗估 token 数（W9 压缩要用）

    2. save()   存成 JSON
    3. load()   读回来（读不到返回 None，不报错）
    4. clear()  删文件

【和 W2 的对应关系】
    W2.build_messages()   →  Session.__init__(persona=...)
    W2.storage.save_history()      →  Session.save()
    W2.storage.load_history()      →  Session.load()
    W2.storage.clear_history_file() → Session.clear()

【验收】
    s = Session(persona="你是助手")
    s.add_user("你好"); s.add_assistant("你好呀")
    s.save()
    s2 = Session.load(); assert len(s2.messages) == 3   # 含 system
"""

import json
import os
import uuid

DEFAULT_PATH = "D:\\桌面\\target and schedule\\代码练习\\项目\\agent_app\\history.json"


class Session:
    """一次会话的全部状态。session 会话"""

    def __init__(self, persona: str = "你是一个乐于助人的助手。", session_id: str | None = None):
        """初始化。

        
            1. self.session_id = session_id or 新生成的 uuid4 短串
            2. self.messages = [{"role": "system", "content": persona}]
            3. 记住 persona（W9 压缩时需要保留 system 消息）
        """
        
        self.session_id=session_id or uuid.uuid4().hex[:8]
        self.persona=persona
        self.messages=[{"role":"system", "content":persona}]
        #raise NotImplementedError("Session.__init__ 未完成")

    # ---------- 追加消息 ----------

    def add_user(self, text: str) -> None:
        """追加一条用户消息。

        往 self.messages 里 append {"role": "user", "content": text}
        """
        
        self.messages.append({"role":"user", "content":text})
        

    def add_assistant(self, text: str) -> None:
        """追加一条助手消息。

        ⚠️ 这一步最容易漏。W2 的 chat_loop 里如果忘了加，
            AI 下一轮就不记得自己刚说过什么。
        """
        
        self.messages.append({"role":"assistant", "content":text})
        

    # ---------- token 估算 ----------

    @property#让这个方法可以当成属性用,因为本质是一个计算结果，不是动作，写成属性，调用方用起来就像在查找一个值
    def token_estimate(self) -> int:
        """粗估当前历史占多少 token。

        先用最笨的办法 —— 所有 content 的字符数加起来，除以 1.5。
              （中文大致 1 字 ≈ 0.7 token，英文 1 词 ≈ 1.3 token，除 1.5 是个够用的粗估）

        W9 做压缩时会用到这个数字：超过预算就触发压缩。
        先能算出个数字就行，精确度以后再说。
        """
        
        total = sum(len(m["content"]) for m in self.messages)
        return int(total/1.5)
        

    # ---------- 持久化 ----------

    def save(self, path: str = DEFAULT_PATH) -> None:
        """存成 JSON。

        搬 W2 步骤 5-1。
              注意 ensure_ascii=False（否则中文变成 \\uXXXX）
              注意要把 session_id 一起存进去（否则读回来分不清是哪个会话）
        """
        
        data={"session_id":self.session_id,"messages":self.messages}
        with open (path, "w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2)
            #with 负责退出时自动关闭文件，包括中途抛异常的情况
        #raise NotImplementedError

    @classmethod #第一个参数变成类本身，不用实例也能调用
    #也能用cls这个类造实例s = cls(session_id=...)
    def load(cls, path: str = DEFAULT_PATH):
        """读回来。

        搬 W2 步骤 5-2，返回 Session 或 None。

        要处理的 3 种情况（跟 W2 一模一样）：
            ① 文件不存在       → 返回 None
            ② 不是合法 JSON    → 打印提示，返回 None
            ③ 不是 dict/list   → 打印提示，返回 None

        ⚠️ 存的时候你存的是 dict（含 session_id + messages），
           读回来要先判断结构再复原，不要假设它一定是 list。
        """
        
        try:
            with open(path,"r",encoding="utf-8") as f:
                data=json.load(f)
        except FileNotFoundError:
            return None 
        except json.JSONDecodeError:
            print(f"[warn] {path} 不是合法JSON，忽略")
            return None #文件坏了

        if not isinstance(data,dict) or not isinstance(data.get("messages"),list):
            print(f"[warn] {path} 格式不对，忽略")
            return None

        s = cls(session_id=data.get("session_id"))
        #为什么不用session;在父类的方法里写死父类名字，等于宣告：「这个方法产出的永远是父类的对象」。
        #新建一个session类的实例，也急就是对象，此时对象里只有__init__塞进去的system消息
        s.messages=data["messages"]#走到这一行，message键一定存在，现在才插入内容
        return s
        #raise NotImplementedError
        #所以加载的实际含义是，读文件，照着文件内容，重建一个一模一样的session对象

    @staticmethod
    #它禁止 Python 自动往方法里塞第一个参数。让实例调和类调行为一致
    #这是一个普通函数，但是我把它放在类里
    def clear(path: str = DEFAULT_PATH) -> None:
        """删文件。

        搬 W2 步骤 5-3。删之前先 os.path.exists 判断。
        """

        if os.path.exists(path):
            os.remove(path)
        #raise NotImplementedError


if __name__ == "__main__":
    s = Session(persona="你是一个简洁的助手")
    s.add_user("你好")
    s.add_assistant("你好，有什么可以帮你？")
    s.save()

    s2 = Session.load()
    print("读回来消息数:", len(s2.messages) if s2 else None)
    print("session_id 一致:", s.session_id == (s2.session_id if s2 else None))

    Session.clear()
    print("clear 后再 load:", Session.load())
