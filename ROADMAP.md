# NL2SQL 开发路线图

## 版本规划

### v0.1.0 - MVP (当前)
**目标**: 基本可用的自然语言转SQL功能

- [x] 项目架构设计
- [x] 后端核心引擎
  - [x] SQL 生成服务
  - [x] Schema 管理（通过 schema_info 参数）
  - [x] 基础验证器
- [x] REST API
  - [x] POST /api/v1/generate
  - [x] GET /api/v1/health
  - [x] POST /api/v1/validate
- [x] CLI 工具
- [x] Docker 支持
- [x] 基础配置系统
- [ ] MySQL 连接器（待集成）

### v0.2.0 - 多数据源
**目标**: 支持多种数据库

- [ ] Hive 连接器
- [ ] Spark SQL 连接器
- [ ] PostgreSQL 连接器
- [ ] Schema 自动发现

### v0.3.0 - Web UI
**目标**: 可视化操作界面

- [ ] React 前端
- [ ] 查询编辑器
- [ ] Schema 浏览器
- [ ] 历史记录

### v0.4.0 - 企业特性
**目标**: 生产就绪

- [ ] 用户认证
- [ ] 权限管理
- [ ] 审计日志
- [ ] 性能优化

### v1.0.0 - 正式版
**目标**: 完整功能

- [ ] 完整文档
- [ ] Docker 部署
- [ ] Kubernetes 支持
- [ ] 监控告警

## 技术栈

### 后端
- Python 3.10+
- FastAPI
- SQLAlchemy
- Pydantic

### 前端
- React 18
- TypeScript
- TailwindCSS
- Monaco Editor

### AI
- OpenAI API
- DeepSeek API
- 支持本地模型

### 部署
- Docker
- Docker Compose
- Nginx

## 里程碑

| 版本 | 目标日期 | 状态 |
|------|----------|------|
| v0.1.0 | 2026-03-10 | 🚧 开发中 |
| v0.2.0 | 2026-03-20 | ⏳ 计划中 |
| v0.3.0 | 2026-04-01 | ⏳ 计划中 |
| v0.4.0 | 2026-04-15 | ⏳ 计划中 |
| v1.0.0 | 2026-05-01 | ⏳ 计划中 |

---
*更新时间: 2026-03-06*