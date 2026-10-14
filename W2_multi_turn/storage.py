"""
W2 存储模块：把对话历史持久化到 JSON 文件。

【为什么要单独一个模块？】
    让 main.py 只管「对话逻辑」，文件读写这种「工具活」放在这里（关注点分离）。
    好处：以后想换成 SQLite / MySQL 存储，只要重写这个文件，main.py 一行都不用改。

【本文件 = 步骤 5，要实现下面 3 个函数】
    步骤 5-1  save_history()          把历史写入文件
    步骤 5-2  load_history()          从文件读回历史
    步骤 5-3  clear_history_file()    删除文件

写完这 3 个之后，回到 main.py 做步骤 6（把它们接进 chat_loop）。
"""

import json
import os

# 历史文件路径（默认放项目根目录，已加入 .gitignore）
HISTORY_FILE = "history.json"


def save_history(history: list, path: str = HISTORY_FILE) -> None:
    """【步骤 5-1】把对话历史写入文件。

    TODO：实现「打开文件 → 把列表写成 JSON」

    提示：
        - 用 open(path, "w", encoding="utf-8") 打开
          （"w" = 写入模式，会【覆盖】原内容）
        - 用 json.dump(要写的数据, 文件对象, ensure_ascii=False, indent=2)
        - 建议用 with 语句（它会自动帮你关闭文件）

    ⚠️ ensure_ascii=False 千万别省！
       不加的话，中文会被写成 \\u4f60\\u597d 这种转义码，文件根本没法看。
    """
    # TODO: 实现步骤 5-1
    raise NotImplementedError("步骤 5-1 未完成")


def load_history(path: str = HISTORY_FILE):
    """【步骤 5-2】从文件读取对话历史。

    TODO：实现「读文件 → 解析 JSON → 返回列表」

    返回：
        list  —— 读取成功
        None  —— 读不到 / 内容坏了 / 格式不对

    要处理 3 种情况：
        ① 文件不存在（第一次运行）   → 返回 None（【不要】报错）
        ② 文件存在但不是合法 JSON   → 打印提示，返回 None
        ③ 读出来的东西不是列表       → 打印提示，返回 None

    提示：
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            ...                    # 情况 ①
        except json.JSONDecodeError:
            ...                    # 情况 ②

        # 情况 ③：用 isinstance(data, list) 判断

    想一想：为什么"读不到"要返回 None，而不是让程序直接报错？
            （提示：第一次运行时没有 history.json，是【完全正常】的情况）
    """
    # TODO: 实现步骤 5-2
    raise NotImplementedError("步骤 5-2 未完成")


def clear_history_file(path: str = HISTORY_FILE) -> None:
    """【步骤 5-3】删除历史文件（/clear 命令时调用）。

    TODO：实现「如果文件存在，就删掉它」

    提示：
        - os.path.exists(path)   判断文件是否存在
        - os.remove(path)        删除文件

    ⚠️ 删之前一定要先判断存在！
       对不存在的文件调 os.remove 会直接抛异常，程序就崩了。

    想一想：为什么文件不存在时不该报错？
            （提示：执行 /clear 时，可能本来就没有历史文件）
    """
    # TODO: 实现步骤 5-3
    raise NotImplementedError("步骤 5-3 未完成")
