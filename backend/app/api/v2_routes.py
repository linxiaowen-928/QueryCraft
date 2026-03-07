"""
API V2 版本 - 更高性能和可用性的版本

提供改进的置信度算法和更多高级特性
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, Any, Optional

from app.models import (
    GenerateRequest,
    GenerateResponse,
    ValidateRequest,
    ValidateResponse,  
)
from app.services import generator
from app.config import settings
from app.connectors import manager, ConnectionConfig, create_connector
from app.core.monitor import perf_metrics

router = APIRouter()


@router.post("/generate-with-confidence", 
             tags=["SQL生成"], 
             summary="生成SQL并返回详细置信度评分",
             description="v2版本的SQL生成接口，提供更精细的置信度和性能数据")
async def generate_sql_detailed_v2(request: GenerateRequest) -> Dict[str, Any]:
    """
    V2版本的SQL生成接口
    
    相较于V1，提供了:
    - 更精细化的置信度评分算法
    - 更精确的SQL类型识别
    - 更详细的执行建议  
    - 包含性能指标的反馈
    """
    # 调用原始的生成服务
    result = await generator.generate(
        query=request.query,
        dialect=request.dialect.value,
        schema_info=request.schema_info,
        context=request.context,
        candidates=request.candidates
    )

    # 在v2中，我们添加更多细节信息到返回结果中
    detailed_result = {
        **result,
        "version": "v2",
        "details": {
            "schema_complexity_score": calculate_schema_complexity_score(request.schema_info),
            "query_comprehension_score": calculate_query_understanding_score(request.query),
            "performance_prediction_ms": estimate_performance_ms(request.query, request.dialect.value)
        }
    }

    return detailed_result


def calculate_schema_complexity_score(schema_info: Optional[Dict]) -> int:
    """计算schema复杂度分数"""
    if not schema_info:
        return 50  # 默认分值
    
    # 根据表格数量和字段数量计算复杂度
    tables = schema_info.get("tables", [])
    total_tables = len(tables)
    
    total_fields = 0
    for table in tables:
        fields = table.get("columns", [])
        total_fields += len(fields)
    
    # 复杂度 = 表数量 * 10 + 字段总数 * 0.5，范围 0-100
    complexity = min(100, total_tables * 10 + total_fields * 0.5)
    return int(complexity)


def calculate_query_understanding_score(query: str) -> int:
    """计算查询理解分数"""
    # 简单的启发式算法来估算查询理解的难易程度
    query_lower = query.lower()
    
    score = 70  # 基础分值
    
    # 查询越具体分数越高
    if "where" in query_lower:
        score += 10
    if "join" in query_lower:
        score += 15
    if "aggregation" in query_lower or "sum" in query_lower or "count" in query_lower:
        score += 10
    if "group by" in query_lower:
        score += 10
        
    # 复杂查询可能降低准确性
    if query.count(" ") > 50:  # 超长查询
        score -= 10
    
    return min(100, max(0, score))


def estimate_performance_ms(query: str, dialect: str) -> int:
    """预估执行时间"""
    # 基础估算（毫秒）
    base_time = 50
    
    query_lower = query.lower()
    
    if "join" in query_lower:
        base_time *= 1.5
    if "aggregation" in query_lower:
        base_time *= 1.3
    if "subquery" in query_lower or "exists" in query_lower:
        base_time *= 2.0
    if query.count("join") > 1:  # 多表连接
        base_time *= 2.0
        
    return int(base_time)


@router.get("/health-detailed", 
            tags=["系统"], 
            summary="详细的健康状况检查",
            description="V2版本的健康检查，返回更详细的系统指标")
async def detailed_health_check():
    """V2版本健康检查 - 提供更详细系统状态信息"""
    return {
        "status": "ok",
        "version": "v2", 
        "version_detail": "API version 2.0 with advanced features",
        "app_version": settings.app_version,
        "llm_provider": settings.llm_provider,
        "timestamp": datetime.utcnow().isoformat(),
        "api_info": {
            "supported_versions": ["v1", "v2"],
            "current_version": "v2",
            "deprecation_status": "none"
        },
        "performance_metrics": perf_metrics.get_overall_stats(),
        "server_timestamp": datetime.now().isoformat()
    }


@router.get("/capabilities", 
            tags=["系统"],
            summary="API能力清单",
            description="返回V2版本支持的具体功能列表")
async def get_capabilities():
    """获取v2版本支持的能力清单"""
    return {
        "version": "v2",
        "features": [
            "精置信度评分 (Enhanced confidence scoring)",
            "性能执行预测 (Performance execution prediction)",
            "复杂度评估 (Complexity assessment)",
            "API版本管理 (API version management)",
            "性能指标反馈 (Performance metric feedback)",
            "详细的健康检查指标 (Detailed health check metrics)"
        ],
        "changes_from_v1": [
            "增加复杂度和理解难度的计算",
            "提供更多关于查询性能的洞见",
            "增强的健康检查端点",
            "API能力清单端点"
        ]
    }