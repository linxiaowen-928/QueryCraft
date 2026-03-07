"""
API 路由模块

根据API版本管理器来组织不同版本的路由
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
from app.core.monitor import perf_metrics, PerformanceMonitor
from app.services import generator
from app.connectors import manager, ConnectionConfig, create_connector
from app.core.api_versioning import version_manager

# Create routers for different versions
# v1 remains as the original router (backward compatible)
v1_router = APIRouter(prefix="/api/v1", tags=["v1 - Legacy"])

# v2 introduces version-specific behavior while maintaining compatibility
v2_router = APIRouter(prefix="/api/v2", tags=["v2 - Current"]) 

# Future v3 router could introduce breaking changes if needed
v3_router = APIRouter(prefix="/api/v3", tags=["v3 - Experimental"])


def setup_versioned_routes(app):
    """
    Setup all versioned routes in the application
    """
    # Add all versioned routers to the app
    
    # V1 legacy routes (backwards compatible)
    app.include_router(v1_router, prefix="/api/v1")
    
    # V2 current routes (recommended)
    app.include_router(v2_router, prefix="/api/v2") 
    
    # V3 experimental routes
    app.include_router(v3_router, prefix="/api/v3")


# V1 ROUTES (Backward Compatible)
@PerformanceMonitor("/generate")
@v1_router.post("/generate", response_model=GenerateResponse, tags=["SQL生成"])
async def generate_sql_v1(request: GenerateRequest):
    """
    V1: 生成SQL (保持向后兼容)
    
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


@v1_router.post("/validate", response_model=ValidateResponse, tags=["SQL验证"])
async def validate_sql_v1(request: ValidateRequest):
    """
    V1: 验证SQL (保持向后兼容)
    
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


@v1_router.get("/health", response_model=HealthResponse, tags=["系统"])
async def health_check_v1():
    """V1: 健康检查 (保持向后兼容)"""
    from app.config import settings
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        llm_provider=settings.llm_provider,
        timestamp=datetime.utcnow().isoformat()
    )


# V2 ROUTES (With version-aware behavior)
@v2_router.get("/health", response_model=HealthResponse, tags=["系统"])
async def health_check_v2():
    """V2: 健康检查 (改进版)"""
    from app.config import settings
    current_version = getattr(HealthResponse.__config__, 'api_version', 'v2')
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        llm_provider=settings.llm_provider,
        api_version="v2",
        timestamp=datetime.utcnow().isoformat(),
        deprecated=version_manager.is_deprecated("v2")
    )


@PerformanceMonitor("/generate")
@v2_router.post("/generate", response_model=GenerateResponse, tags=["SQL生成"])
async def generate_sql_v2(request: GenerateRequest):
    """
    V2: 生成增强的 SQL (带有上下文和兼容性特性)
    
    将自然语言查询转换为SQL语句，提供改进的错误处理
    """
    result = await generator.generate(
        query=request.query,
        dialect=request.dialect.value,
        schema_info=request.schema_info,
        context=request.context,
        candidates=request.candidates
    )
    
    # V2 could include improved error descriptions or different response format
    if result.get('error'):
        # For v2+, return more detailed error information 
        result['error_details'] = "This error description follows v2+ improved error handling"
    
    return GenerateResponse(**result)


@v2_router.post("/validate", response_model=ValidateResponse, tags=["SQL验证"])
async def validate_sql_v2(request: ValidateRequest):
    """
    V2: 增强的 SQL 验证 (改进版)
    
    提供更全面的 SQL 验证，包括性能检查
    """
    from app.config import settings
    sql = request.sql.upper()
    
    errors = []
    warnings = []
    
    # 语法检查
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
        errors.append("DELETE 语句缺少 WHERE 条件，存在安全隐患")
        security_score -= 50

    if "UPDATE" in sql and "WHERE" not in sql:
        warnings.append("UPDATE 语句缺少 WHERE 条件，可能更新所有数据")
        errors.append("UPDATE 语句缺少 WHERE 条件，存在安全隐患")
        security_score -= 50

    # 性能检查 (new in v2)
    performance_score = 100
    if "JOIN" not in sql and "WHERE" not in sql:
        # This could be an inefficient query without proper filtering
        warnings.append("查询未包含适当过滤条件，可能导致性能问题")
        performance_score -= 20

    if sql.count("SELECT *") > 0:
        # Star select could impact performance
        warnings.append("避免使用 SELECT *, 应明确指定所需的列以提高性能")
        performance_score -= 10
    
    # 语义检查（简化）
    semantic_score = 85
    
    # 计算总分 (balanced average)
    score = (syntax_score + semantic_score + security_score + performance_score) // 4
    valid = len(errors) == 0 and score >= 60
    
    return ValidateResponse(
        valid=valid,
        score=score,
        syntax_score=syntax_score,
        semantic_score=semantic_score,
        security_score=security_score,
        performance_score=performance_score,  # New in v2
        errors=errors,
        warnings=warnings,
        api_version="v2",  # New in v2
        validated_at=datetime.utcnow().isoformat()  # New in v2
    )


# V3 ROUTES (Experimental/Advanced)
@v3_router.get("/health", response_model=HealthResponse, tags=["系统"])
async def health_check_v3():
    """V3: 健康检查 (实验性)"""
    from app.config import settings
    return HealthResponse(
        status="ok", 
        version=settings.app_version,
        llm_provider=settings.llm_provider, 
        api_version="v3",
        experimental=True,  # New in v3
        extended_health=True,  # New in v3
        timestamp=datetime.utcnow().isoformat(),
        deprecated=version_manager.is_deprecated("v3"),
        warning=version_manager.is_deprecated("v3") and "This is an experimental version" or None
    )


@PerformanceMonitor("/generate")
@v3_router.post("/generate", response_model=Dict[str, Any], tags=["SQL生成"])  # Note: Different response type
async def generate_sql_v3(request: GenerateRequest):
    """
    V3: 实验性的多类型 SQL 生成
    """
    result = await generator.generate(
        query=request.query,
        dialect=request.dialect.value,
        schema_info=request.schema_info,
        context=request.context,
        candidates=request.candidates
    )
    
    # V3 would potentially include different response schema
    return {
        # Original result
        **result,
        # V3 additions
        "api_version": "v3",
        "response_format": "experimental",
        "generation_method": "v3_enhanced"
    }


# Add data source management routes for all versions
@v1_router.get("/datasources", tags=["数据源"])
@v2_router.get("/datasources", tags=["数据源"])
@v3_router.get("/datasources", tags=["数据源"])
async def list_datasources():
    """列出所有数据源 (适用于所有版本)"""
    return manager.list_datasources()


@v1_router.post("/datasources/{name}/connect", tags=["数据源"])
@v2_router.post("/datasources/{name}/connect", tags=["数据源"])
@v3_router.post("/datasources/{name}/connect", tags=["数据源"])
async def connect_datasource(name: str, config: ConnectionConfig, connector_type: str = "mysql"):
    """连接数据源 (适用于所有版本)"""
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


# Import and include other routes from routes.py for consistency
from .routes import *  # noqa: F401,F403  - Import remaining routes to maintain backward compatibility