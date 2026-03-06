"""
配置管理
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # 服务器配置
    app_name: str = "QueryCraft"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8080
    
    # LLM 配置 - 默认使用 ZhipuAI
    llm_provider: str = "zhipuai"  # openai | deepseek | zhipuai | local
    llm_model: str = "glm-4-flash"
    llm_api_key: Optional[str] = os.getenv("ZHIPUAI_API_KEY")
    llm_api_url: str = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    
    # 数据库配置
    database_url: Optional[str] = None
    
    # 安全配置
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()