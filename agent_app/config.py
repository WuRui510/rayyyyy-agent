"""
【W1】配置层 —— 所有配置集中在这一个地方

为什么要单独一个文件？
    W1 项目里你是这样：
        load_dotenv()
        key = os.getenv("DEEPSEEK_API_KEY")

    能用，但有三个问题：
        ① 配置散落各处：key 在 llm.py 读，文件路径在 session.py 写死
        ② 没法校验：key 拼错了要等到真正调 API 时才发现
        ③ 没法分环境：开发和线上应该是不同配置

    所以用 pydantic-settings：
        - 自动从 .env 和环境变量读
        - 有类型（timeout 一定是 float，不会是字符串）
        - 缺必填项会在启动时立刻报错（Fail Fast）

【要做的】
    1. 定义 Settings 类
    2. 提供 get_settings() 单例

【验收】
    from config import get_settings
    s = get_settings()
    print(s.deepseek_api_key, s.model, s.llm_timeout)
"""

from functools import lru_cache #缓存装饰器，保证单例对象，整个程序里配置对象只构造一次

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全部配置项。

    
        1. 加 model_config，让它读 .env 文件：
               model_config = SettingsConfigDict(env_file=".env", extra="ignore")
           （extra="ignore" 是为了让 .env 里有多余变量时不报错）

        2. 定义字段。注意 pydantic 会做类型转换和校验：
               deepseek_api_key: str          # 没有默认值 = 必填，缺了就启动报错
               model: str = "deepseek-flash"
               base_url: str = "https://api.deepseek.com"
               llm_timeout: float = 30.0     # 单次 LLM 调用超时（秒）
               max_retries: int = 3
               log_level: str = "INFO"
               session_file: str = "history.json"

           ⚠️ 下面这组是【数据库】相关，W1 只定义、不连接：
               pg_dsn: str = "postgresql://agent:agent_dev_pw@localhost:55432/tpch"
               query_timeout: float = 30.0   # 单条 SQL 执行的超时上限（秒）
               max_optimize_rounds: int = 3  # Agent 最多优化几轮

           为什么 W1 就写进去？
             因为它让 config.py 成为"唯一的配置真相"。
             W2 接数据库时直接 get_settings().pg_dsn，不用回头改任何文件。

        3. 想一想：环境变量名会自动匹配吗？
           pydantic-settings 默认是大小写不敏感的，所以
           `.env` 里的 DEEPSEEK_API_KEY → 字段 deepseek_api_key，能自动对上。
    """

    

    model_config = SettingsConfigDict(env_file=".env", extra = "ignore")

    deepseek_api_key: str
    model:str = "deepseek-flash"
    base_url:str = "https://api.deepseek.com" #字段需要类型注解
    llm_timeout:float = 30.0   #单次调用大模型的超时上限（秒）
    max_attempts: int = 3   #明确：总共有 3 次机会
    log_level: str = "INFO" #日志的详细程度：DEBUG/INFO/WARNING/ERROR,生产环境必须是info
    session_file:str = "history.json"   #会话持久化的文件路径。Session.save() 默认写到这。

    pg_dsn: str = "postgresql://agent:agent_dev_pw@localhost:55432/tpch" #数据库连接串
    query_timeout: float = 30.0 #单条 SQL 执行的超时上限（秒）
    max_optimize_rounds: int = 3 # Agent 最多优化几轮


@lru_cache #装饰器
def get_settings() -> Settings:
    """单例。用 lru_cache 保证全局只构造一次。

    返回 Settings()

    ⚠️ 注意：不要把 settings 当成全局变量到处 import 后修改，
       它是只读的。要改配置就改 .env 然后重启。
    """
    
    return Settings()
    #raise NotImplementedError("get_settings 未完成")


if __name__ == "__main__":
    s = get_settings()
    print("model      :", s.model)
    print("base_url   :", s.base_url)
    print("timeout    :", s.llm_timeout)
    print("api_key    :", (s.deepseek_api_key[:6] + "***") if s.deepseek_api_key else "(空)")
