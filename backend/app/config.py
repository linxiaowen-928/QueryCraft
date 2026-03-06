"""
配置管理
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # 忽略未定义的环境变量
    )
    
    # 服务器配置
    app_name: str = "QueryCraft"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8080
    
    # LLM 配置 - 默认使用 ZhipuAI
    llm_provider: str = "zhipuai"
    llm_model: str = "glm-4-flash"
    llm_api_key: Optional[str] = None
    llm_api_url: str = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    
    # 数据库配置
    database_url: Optional[str] = None
    
    # 安全配置
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 30


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()