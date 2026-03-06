"""
数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class Dialect(str, Enum):
    """SQL方言"""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    HIVE = "hive"
    SPARK = "spark"
    FLINK = "flink"
    ICEBERG = "iceberg"


class GenerateRequest(BaseModel):
    """SQL生成请求"""
    query: str = Field(..., description="自然语言查询", min_length=1)
    dialect: Dialect = Field(default=Dialect.MYSQL, description="SQL方言")
    datasource: Optional[str] = Field(None, description="数据源名称")
    schema_info: Optional[Dict[str, Any]] = Field(None, description="Schema信息")
    context: Optional[Dict[str, Any]] = Field(None, description="业务上下文")
    candidates: int = Field(default=1, ge=1, le=5, description="候选SQL数量")


class GenerateResponse(BaseModel):
    """SQL生成响应"""
    success: bool = Field(..., description="是否成功")
    sql: Optional[str] = Field(None, description="生成的SQL")
    candidates: Optional[List[str]] = Field(None, description="候选SQL列表")
    confidence: int = Field(default=0, ge=0, le=100, description="置信度")
    explanation: Optional[str] = Field(None, description="SQL解释")
    error: Optional[str] = Field(None, description="错误信息")
    duration_ms: int = Field(default=0, description="耗时(毫秒)")


class ValidateRequest(BaseModel):
    """SQL验证请求"""
    sql: str = Field(..., description="待验证的SQL")
    dialect: Dialect = Field(default=Dialect.MYSQL, description="SQL方言")
    schema_info: Optional[Dict[str, Any]] = Field(None, description="Schema信息")


class ValidateResponse(BaseModel):
    """SQL验证响应"""
    valid: bool = Field(..., description="是否有效")
    score: int = Field(default=0, ge=0, le=100, description="总分")
    syntax_score: int = Field(default=0, ge=0, le=100, description="语法分")
    semantic_score: int = Field(default=0, ge=0, le=100, description="语义分")
    security_score: int = Field(default=0, ge=0, le=100, description="安全分")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本号")
    llm_provider: str = Field(..., description="LLM提供商")
    timestamp: str = Field(..., description="时间戳")


class DataSourceInfo(BaseModel):
    """数据源信息"""
    name: str = Field(..., description="数据源名称")
    type: str = Field(..., description="数据源类型")
    host: str = Field(..., description="主机")
    port: int = Field(..., description="端口")
    database: str = Field(..., description="数据库")
    status: str = Field(default="unknown", description="连接状态")


class SchemaInfo(BaseModel):
    """Schema信息"""
    datasource: str = Field(..., description="数据源名称")
    database: str = Field(..., description="数据库名")
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="表信息")
    last_updated: Optional[datetime] = Field(None, description="最后更新时间")