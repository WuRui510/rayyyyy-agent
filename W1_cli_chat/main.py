"""
W1 : CLI 大模型问答脚本

用法：
    py main.py "你的问题"
    py main.py "你的问题" --stream
    py main.py "你的问题" --model deepseek-v4-pro
"""

import os
import sys
from openai import (
    OpenAI,
    AuthenticationError,
    APIConnectionError,
    RateLimitError,
    APIStatusError,
)
from dotenv import load_dotenv

AVAILABLE_MODELS = ["deepseek-flash","deepseek-v4-pro"]
DEFAULT_MODEL = "deepseek-flash"

def get_api_key() -> str:

    load_dotenv()
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        sys.exit("错误：没有找到 DEEPSEEK_API_KEY,请检查 .env 文件")
    else:
        return key

def ask(question: str, model: str = DEFAULT_MODEL) -> None:

    client = OpenAI(api_key=get_api_key(),base_url="https://api.deepseek.com")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system","content":"你是一个乐于助人的助手"},
            {"role":"user","content":question}
        ]
    )
    print(resp.choices[0].message.content) 

    #为什么system排在前面，因为大模型永远是更重视靠前，且标记为system的内容
    #client.chat.completions.create是一个函数，函数（参数）代表立刻执行


def ask_stream(question: str, model: str = DEFAULT_MODEL) -> None:
    
    client = OpenAI(api_key=get_api_key(),base_url="https://api.deepseek.com")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system","content":"你是一个乐于助人的助手"},   
            {"role":"user","content":question}
        ],
        stream=True,
    )
        
    for chunk in resp:
        piece = chunk.choices[0].delta.content
        #这一小块内容
        if piece:
            print(piece,end = "",flush=True)
            #打印机效果的两个关键开关

    #piece 就是 str，直接就是文字
    #切分是「按 token」，不是「按字」
    #空字符串出现在开头和结尾
    #流式输出核心参数
    #加上这个参数表示resp是一个stream可循环流，是ChatCompletionChunk
    #没加这个参数resp类型是ChatCompletion

def main() -> None:
    
    if len(sys.argv) < 2:
        print("用法:py main.py '你的问题' --stream --model 模型名")
        return
    question = sys.argv[1]

    #判断是否采用流式输出,为true则用，为false则不用
    use_stream = "--stream" in sys.argv

    #选择用什么模型
    model = DEFAULT_MODEL

    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            name = sys.argv[idx + 1] 
            if name in AVAILABLE_MODELS:
                model = name
            else:
                print(f"提示: 未知模型 {name}, 已使用默认模型 {DEFAULT_MODEL}")
                print(f"可用模型：{'、'.join(AVAILABLE_MODELS)}")
        else:
            print(f"已使用默认模型 {DEFAULT_MODEL}")
    
    try:
        if use_stream:
            ask_stream(question,model)
        else:
            ask(question,model)

    except AuthenticationError:
        sys.exit("错误:API KEY无效，请检查.env中的 DEEPSEEK_API_KEY")
    except APIConnectionError:
        sys.exit("错误：无法连接Deepseek服务器，请检查网络连接")
    except RateLimitError:
        sys.exit("错误：请求太频繁，请稍后重试")
    except APIStatusError as e:
        if e.status_code == 402:
            sys.exit("错误：API账户余额不足")
        sys.exit(f"错误：API返回错误码{e.status_code}")
    except Exception as e:
        sys.exit(f"未知错误：{type(e).__name__}:{e}")


if __name__ == "__main__":
    main()