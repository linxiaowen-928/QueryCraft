"""
配置管理
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # 服务器配置
    app_name: str = "QueryCraft"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # LLM 配置
    llm_provider: str = "openai"  # openai | deepseek | local
    llm_model: str = "gpt-4"
    llm_api_key: Optional[str] = None
    llm_api_url: Optional[str] = None
    
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