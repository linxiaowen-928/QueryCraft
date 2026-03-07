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
from app.core.monitor import perf_metrics, PerformanceMonitor
from app.services import generator
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


@PerformanceMonitor("/generate")

@router.get("/metrics", tags=["性能"])
async def get_performance_metrics():
    """获取性能指标"""
    return {
        "api_metrics": perf_metrics.get_api_metrics(),
        "db_metrics": perf_metrics.get_db_metrics(),
        "overall_stats": perf_metrics.get_overall_stats(),
    }


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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from app.services.schema_discovery import schema_discovery

@router.post("/datasources/{name}/refresh-schema", tags=["Schema"])
async def refresh_datasource_schema(name: str):
    """刷新数据源Schema"""
    connector = manager.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Datasource '{name}' not found")
    
    try:
        # 发现数据库结构
        db_info = await schema_discovery.discover_database(connector)
        
        return {
            "status": "success",
            "database": schema_discovery.to_dict(db_info)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasources/{name}/schema-detail", tags=["Schema"])
async def get_datasource_schema_detail(name: str):
    """获取数据源详细Schema（带缓存）"""
    connector = manager.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Datasource '{name}' not found")
    
    try:
        # 先检查缓存
        db_name = await connector.get_database_name()
        cached = schema_discovery.get_schema(db_name)
        
        if cached:
            return schema_discovery.to_dict(cached)
        
        # 如果没有缓存，刷新
        db_info = await schema_discovery.discover_database(connector)
        return schema_discovery.to_dict(db_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasources/{name}/tables", tags=["Schema"])
async def list_datasource_tables(name: str):
    """列出数据源的所有表"""
    connector = manager.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Datasource '{name}' not found")
    
    try:
        tables = await connector.get_tables()
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasources/{name}/tables/{table}/columns", tags=["Schema"])
async def list_table_columns(name: str, table: str):
    """列出表的列信息"""
    connector = manager.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Datasource '{name}' not found")
    
    try:
        columns = await connector.get_columns(table)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 查询历史 ==========
from app.services.query_history import query_history
from typing import Optional

@router.get("/history", tags=["查询历史"])
async def get_query_history(limit: int = 50, datasource: Optional[str] = None, favorite_only: bool = False):
    history = query_history.get_history(limit=limit, datasource=datasource, favorite_only=favorite_only)
    return {"history": [{"id": item.id, "query": item.query, "dialect": item.dialect, "generated_sql": item.generated_sql, "datasource": item.datasource, "timestamp": item.timestamp, "favorite": item.favorite, "execution_time_ms": item.execution_time_ms, "success": item.success} for item in history]}

@router.post("/history", tags=["查询历史"])
async def add_query_history(query: str, dialect: str, generated_sql: str, datasource: str, execution_time_ms: int = 0, success: bool = True, error: Optional[str] = None):
    item = query_history.add_query(query=query, dialect=dialect, generated_sql=generated_sql, datasource=datasource, execution_time_ms=execution_time_ms, success=success, error=error)
    return {"status": "success", "id": item.id}

@router.post("/history/{query_id}/favorite", tags=["查询历史"])
async def toggle_favorite(query_id: str):
    result = query_history.toggle_favorite(query_id)
    if result is None: raise HTTPException(status_code=404, detail="Query not found")
    return {"favorite": result}

@router.delete("/history/{query_id}", tags=["查询历史"])
async def delete_query_history(query_id: str):
    success = query_history.delete_history(query_id)
    if not success: raise HTTPException(status_code=404, detail="Query not found")
    return {"status": "success"}

@router.delete("/history", tags=["查询历史"])
async def clear_query_history(datasource: Optional[str] = None):
    query_history.clear_history(datasource)
    return {"status": "success"}

@router.get("/history/search", tags=["查询历史"])
async def search_history(keyword: str, limit: int = 20):
    results = query_history.search_history(keyword, limit)
    return {"results": [{"id": item.id, "query": item.query, "generated_sql": item.generated_sql, "timestamp": item.timestamp} for item in results]}

@router.get("/history/statistics", tags=["查询历史"])
async def get_history_statistics():
    return query_history.get_statistics()


# ========== 学习服务 ==========
from app.services.learning_service import learning_service

@router.post("/feedback", tags=["学习"])
async def add_feedback(query: str, original_sql: str, corrected_sql: Optional[str] = None, feedback_text: Optional[str] = None, datasource: str = ""):
    """添加用户反馈"""
    feedback = learning_service.add_feedback(query=query, original_sql=original_sql, corrected_sql=corrected_sql, feedback_text=feedback_text, datasource=datasource)
    return {"status": "success", "id": feedback.id}

@router.get("/feedback", tags=["学习"])
async def get_feedback_list(limit: int = 50, datasource: Optional[str] = None):
    """获取反馈列表"""
    feedback_list = learning_service.get_feedback(limit=limit, datasource=datasource)
    return {"feedback": [{"id": f.id, "query": f.query, "original_sql": f.original_sql, "corrected_sql": f.corrected_sql, "feedback_text": f.feedback_text, "timestamp": f.timestamp} for f in feedback_list]}

@router.get("/knowledge", tags=["学习"])
async def get_knowledge_list(limit: int = 50, min_confidence: float = 0.0):
    """获取知识库"""
    knowledge_list = learning_service.get_knowledge(limit=limit, min_confidence=min_confidence)
    return {"knowledge": [{"id": k.id, "key_term": k.key_term, "mapped_table": k.mapped_table, "mapped_field": k.mapped_field, "description": k.description, "confidence": k.confidence, "usage_count": k.usage_count} for k in knowledge_list]}

@router.post("/knowledge", tags=["学习"])
async def add_knowledge_item(key_term: str, mapped_table: str, mapped_field: Optional[str] = None, description: Optional[str] = None, confidence: float = 0.8):
    """手动添加知识"""
    knowledge = learning_service.add_knowledge(key_term=key_term, mapped_table=mapped_table, mapped_field=mapped_field, description=description, confidence=confidence)
    return {"status": "success", "id": knowledge.id}

@router.get("/knowledge/search", tags=["学习"])
async def search_knowledge_item(keyword: str):
    """搜索知识"""
    results = learning_service.search_knowledge(keyword)
    return {"results": [{"id": k.id, "key_term": k.key_term, "mapped_table": k.mapped_table, "confidence": k.confidence} for k in results]}

@router.delete("/knowledge/{knowledge_id}", tags=["学习"])
async def delete_knowledge_item(knowledge_id: str):
    """删除知识"""
    success = learning_service.delete_knowledge(knowledge_id)
    if not success: raise HTTPException(status_code=404, detail="Knowledge not found")
    return {"status": "success"}

@router.post("/sessions/{session_id}", tags=["学习"])
async def create_session_item(session_id: str, datasource: str):
    """创建会话"""
    session = learning_service.create_session(session_id, datasource)
    return {"status": "success", "session_id": session.session_id}

@router.get("/sessions/{session_id}", tags=["学习"])
async def get_session_context_item(session_id: str):
    """获取会话上下文（用于SQL生成）"""
    context = learning_service.get_session_context(session_id)
    if not context: raise HTTPException(status_code=404, detail="Session not found")
    return context

@router.put("/sessions/{session_id}/context", tags=["学习"])
async def update_session_context_item(session_id: str, context: Dict[str, Any]):
    """更新会话上下文"""
    learning_service.update_session_context(session_id, context)
    return {"status": "success"}

@router.get("/learning/statistics", tags=["学习"])
async def get_learning_statistics_item():
    """获取学习统计"""
    return learning_service.get_statistics()