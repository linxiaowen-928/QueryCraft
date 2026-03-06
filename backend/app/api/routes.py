"""
API路由
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, Any

from app.models import (
    GenerateRequest,
    GenerateResponse,
    ValidateRequest,
    ValidateResponse,
    HealthResponse
)
from app.services import generator
from app.config import settings
from app.connectors import manager, ConnectionConfig, create_connector

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["系统"])
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        llm_provider=settings.llm_provider,
        timestamp=datetime.utcnow().isoformat()
    )


@router.post("/generate", response_model=GenerateResponse, tags=["SQL生成"])
async def generate_sql(request: GenerateRequest):
    """
    生成SQL
    
    将自然语言查询转换为SQL语句
    """
    result = await generator.generate(
        query=request.query,
        dialect=request.dialect.value,
        schema_info=request.schema_info,
        context=request.context,
        candidates=request.candidates
    )
    
    return GenerateResponse(**result)


@router.post("/validate", response_model=ValidateResponse, tags=["SQL验证"])
async def validate_sql(request: ValidateRequest):
    """
    验证SQL
    
    检查SQL语法、语义和安全性
    """
    # TODO: 实现完整的验证逻辑
    sql = request.sql.upper()
    
    errors = []
    warnings = []
    
    # 语法检查（简化）
    syntax_score = 100
    if not sql.strip().startswith(("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER")):
        errors.append("SQL语句必须以有效关键字开头")
        syntax_score -= 30
    
    # 安全检查
    security_score = 100
    dangerous_keywords = ["DROP", "TRUNCATE", "GRANT", "REVOKE"]
    for keyword in dangerous_keywords:
        if keyword in sql:
            errors.append(f"禁止使用 {keyword} 语句")
            security_score -= 50
    
    if "DELETE" in sql and "WHERE" not in sql:
        warnings.append("DELETE 语句缺少 WHERE 条件，可能删除所有数据")
        errors.append("DELETE 语句缺少 WHERE 条件，存在安全隐患")  # 安全隐患视为错误
        security_score -= 50

    if "UPDATE" in sql and "WHERE" not in sql:
        warnings.append("UPDATE 语句缺少 WHERE 条件，可能更新所有数据")
        errors.append("UPDATE 语句缺少 WHERE 条件，存在安全隐患")  # 安全隐患视为错误
        security_score -= 50
    # 语义检查（简化）
    semantic_score = 85
    
    # 计算总分
    score = (syntax_score + semantic_score + security_score) // 3
    valid = len(errors) == 0 and score >= 60
    
    return ValidateResponse(
        valid=valid,
        score=score,
        syntax_score=syntax_score,
        semantic_score=semantic_score,
        security_score=security_score,
        errors=errors,
        warnings=warnings
    )


# ========== 数据源管理 ==========

@router.get("/datasources", tags=["数据源"])
async def list_datasources():
    """列出所有数据源"""
    return manager.list_datasources()


@router.post("/datasources/{name}/connect", tags=["数据源"])
async def connect_datasource(name: str, config: ConnectionConfig, connector_type: str = "mysql"):
    """连接数据源"""
    try:
        connector = create_connector(config, connector_type)
        manager.register(name, connector)
        success = await connector.connect()
        
        if success:
            return {"status": "connected", "name": name, "type": connector_type}
        else:
            raise HTTPException(status_code=500, detail="Connection failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasources/{name}/schema", tags=["数据源"])
async def get_datasource_schema(name: str):
    """获取数据源Schema"""
    connector = manager.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Datasource '{name}' not found")
    
    try:
        schema = await connector.get_schema()
        return schema
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/datasources/{name}/execute", tags=["数据源"])
async def execute_sql(name: str, sql: str, limit: int = 1000):
    """在数据源上执行SQL"""
    connector = manager.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Datasource '{name}' not found")
    
    try:
        result = await connector.execute(sql, limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))