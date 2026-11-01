"""
最小CLI：多轮对话+退出保存+重启恢复
"""

from config import get_settings
from llm import DeepSeekLLM
from observability import setup_logging,trace
from session import Session

def main(llm=None):
    setup_logging(get_settings().log_level)
    llm=llm or DeepSeekLLM() 

    s=Session.load()
    if s is None:
        s=Session(persona="你是一个乐于助人的助手")
        print(f"[新会话{s.session_id}]")
    else:
        print(f"[恢复会话 {s.session_id}，{len(s.messages)} 条历史]") 

    while True:
        q=input("你> ").strip()#strip()去除首尾空格,input永远返回字符串
        if not q:
            continue
        if q in ("/exit","/q"):
            s.save()
            print(f"[已保存到 history.json]")
            break
        if q == "/clear":
            Session.clear()
            s=Session()
            print("[历史已清空]")
            continue

        s.add_user(q)
        print("AI> ",end="",flush=True)

        reply=""
        try:
            for piece in llm.stream(s.messages):
                print(piece,end="",flush=True) #收到一块打印一块
                reply +=piece 
        except Exception as e:
            print(f"\n[请求失败]{e}")
            continue
        print() #换行收尾

        s.add_assistant(reply)

if __name__ == "__main__":
    main()