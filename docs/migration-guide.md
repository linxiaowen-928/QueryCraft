# API 版本迁移指南

本文档指导如何从 QueryCraft API v1 迁移至 v2。

## 版本概述

QueryCraft v2 API 在 v1 的基础上增加了更多企业级功能：
- 更精细的置信度评估
- 更精准的性能预测 
- 更完善的错误诊断功能

v1 API 将持续获得安全更新至少 6 个月。

## 迁移时间线

- **现在**: v2 版本稳定，可供新项目使用
- **3周后**: 新功能将仅添加到 v2
- **6周后**: 所有新项目鼓励使用 v2
- **6个月**: v1 将停止添加功能性更新（仅安全更新）

## 迁移步骤

### 1. 更新基础 URL

将 API 端点从 `/api/v1/` 改为 `/api/v2/`

**迁移前** (v1):
```
POST /api/v1/generate
```

**迁移后** (v2):
```
POST /api/v2/generate-with-confidence
```

### 2. 处理响应格式变化

#### 传统 v1 响应:
```json
{
  "sql": "SELECT * FROM users WHERE id = 1",
  "confidence": 85,
  "explanation": "根据用户表的ID字段查找"
}
```

#### v2 新增响应字段:
```json
{
  "sql": "SELECT * FROM users WHERE id = 1", 
  "confidence": 85,
  "explanation": "根据用户表的ID字段查找",
  "version": "v2",
  "details": {
    "schema_complexity_score": 65,
    "query_comprehension_score": 90, 
    "performance_prediction_ms": 45
  }
}
```

### 3. 使用新特性

v2 接口提供新的分析能力：

- **schema_complexity_score**: 表示涉及数据复杂度（0-100）
- **query_comprehension_score**: 表示模型对查询的理解度（0-100）
- **performance_prediction_ms**: 预估 SQL 执行时间（毫秒）

## 新功能

### 精细化置信度

V2 API 不仅提供整体置信度，还提供：

1. Schema复杂度评估
2. 查询理解难易度评估  
3. 性能预期

### 增强的健康检查

使用新的 `/api/v2/health-detailed` 端点替代传统的健康检查获取更详细信息。

### API 能力探测

使用 `/api/v2/capabilities` 可查询 API 的具体功能特性。

## 端点映射

| v1 端点 | v2 等效端点 | 说明 |
|---------|-------------|------|
| GET /api/v1/health | GET /api/v2/health-detailed | 更详尽的健康信息 |
| POST /api/v1/generate | POST /api/v2/generate-with-confidence | 包含更多详情 |
| - | GET /api/v2/capabilities | 新端点-能力清单 |
| - | GET /api/v2/generate-with-confidence | 新端点-详细SQL生成 |

## 向后兼容性

v1 API 保持完全向后兼容，但推荐新开发迁移到 v2 以享受新特性。

老版本的端点仍然可以在 v1 下使用，但我们鼓励在新开发中使用更新更可靠的 v2 端点。

## 资源

- [详细 API 参考 - v2](https://github.com/linxiaowen-928/QueryCraft/blob/main/docs/api-reference-v2.md)
- [示例代码](https://github.com/linxiaowen-928/QueryCraft/tree/main/examples)
- [常见问题](https://github.com/linxiaowen-928/QueryCraft/blob/main/docs/faq.md)