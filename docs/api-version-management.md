# API 版本管理与兼容性

## 概述

QueryCraft 支持API版本控制，允许平滑升级和向后兼容性。此功能使开发者能够迭代API而不影响现有客户端。

## 版本策略

### 支持的版本
- **v1**: 基础API功能（当前兼容）
- **v2**: 增强功能和改进的错误处理
- **v3**: 实验性功能和高级特性

### 版本控制方式

#### 1. URL 路径版本控制
```
/api/v1/generate
/api/v2/generate
/api/v3/generate
```

#### 2. Header 版本协商
```
X-API-Version: v2
Accept: application/vnd.api.v2+json
```

#### 3. 版本发现
可以通过 `/versions` 端点获取所有受支持的版本详情：
```
GET /versions
```

响应包括:
- 支持的版本列表
- 是否弃用的状态
- 文档路径
- 迁移指南

## 兼容性保证

### 弃用政策
- 旧版本将提供至少3个月的迁移期
- 所有弃用版本的API请求会收到警告响应
- 会在相应版本达到生命周期终点前通知客户端

### 客户端最佳实践
1. 明确版本请求（如 `/api/v2/generate`）
2. 监控 `X-API-Version-Warning` 响应头
3. 测试升级到新版本

## 使用方法

### 版本协商
如果没有明确指定版本，系统将默认使用最新版本。推荐在请求头中显式声明期望的版本：

```
POST /generate HTTP/1.1
Content-Type: application/json
X-API-Version: v2
Accept: application/json

{
  "query": "查询最近30天的订单",
  "dialect": "mysql",
  "schema_info": {},
  ...other params
}
```

### 版本差异
- **v2** 包含增强的SQL验证和性能检查
- **v3** 提供实验性API结构

## 后续计划

- 增加自动版本迁移助手
- 支持API版本比较
- 添加客户端SDK版本匹配建议

---

*此文档随API演进而更新*