from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础
    APP_NAME: str = "Course AI Helper"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # 服务器
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/course_ai.db"
    # PostgreSQL 示例: "postgresql+psycopg2://user:pass@localhost:5432/course_ai"
    
    # JWT 认证
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天
    
    # 文件存储（使用绝对路径，相对于项目根目录）
    DATA_DIR: str = "../data"
    VIDEO_DIR: str = "../data/videos"
    SUBTITLE_DIR: str = "../data/subtitles"
    SUMMARY_DIR: str = "../data/summaries"
    EMBEDDING_DIR: str = "../data/embeddings"
    
    # 向量数据库
    CHROMA_PERSIST_DIR: str = "../data/chroma"
    EMBEDDING_MODEL: str = "bge-small-zh-v1.5"
    
    # LLM 配置 - 本地 (Ollama)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    
    # LLM 配置 - DeepSeek
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_API_KEY: Optional[str] = None
    
    # LLM 配置 - OpenAI
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4.1-mini"
    OPENAI_API_KEY: Optional[str] = None
    
    # LLM 配置 - 阿里百炼 Coding Plan (qwen3.5-plus)
    # 参考文档：https://help.aliyun.com/zh/model-studio/coding-plan-quickstart
    ALIBABA_BASE_URL: str = "https://coding.dashscope.aliyuncs.com/v1"
    ALIBABA_MODEL: str = "qwen3.5-plus"
    ALIBABA_API_KEY: str = "sk-sp-b2642e0a143d4a15b1ccf290607f5a3c"  # 阿里百炼 API Key
    
    # 默认 LLM 后端
    DEFAULT_LLM_BACKEND: str = "alibaba"  # local / deepseek / openai / alibaba
    
    # ASR 配置
    ASR_ENGINE: str = "deepgram"  # whisper / faster-whisper / deepgram
    ASR_MODEL: str = "nova-3"
    DEEPGRAM_API_KEY: str = "e1af15d95d0fb97db51629933147120c6f067482"  # Deepgram API Key
    DEEPGRAM_MODEL: str = "nova-3"
    
    # 字幕分段配置
    MAX_SEGMENT_DURATION: float = 2.2  # 秒
    MAX_SEGMENT_CHARS: int = 28
    
    # 总结配置
    SUMMARY_MAX_TOKENS: int = 4000
    KNOWLEDGE_POINT_MAX_COUNT: int = 20
    
    # 搜索配置
    SEARCH_TOP_K: int = 10
    SEARCH_SCORE_THRESHOLD: float = 0.5
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
