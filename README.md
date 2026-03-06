# QueryCraft - 自然语言转SQL引擎

**独立可运行的自然语言到SQL转换系统**

## 项目概述

QueryCraft 是一个工业化级别的自然语言转SQL引擎，支持：
- 🗣️ 自然语言查询输入
- 📊 多种数据库方言 (MySQL, PostgreSQL, Hive, Spark, Flink, Iceberg)
- 🔍 智能Schema理解
- ✅ SQL验证与评分
- 📈 持续学习与优化

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Web UI     │  │   REST API   │  │     CLI      │      │
│  │  (React)     │  │  (FastAPI)   │  │  (Command)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                      核心引擎层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ NL Parser    │  │ SQL Generator│  │  Validator   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Schema Store │  │Context Engine│  │   Scorer     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                      数据源层                                │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │ MySQL  │ │  Hive  │ │ Spark  │ │ Flink  │ │ Iceberg│    │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                      AI 模型层                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   OpenAI     │  │  DeepSeek    │  │  Local LLM   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## 目录结构

```
querycraft/
├── backend/                 # Python FastAPI 后端
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心引擎
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务服务
│   │   └── config.py       # 配置
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React Web UI
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── cli/                    # 命令行工具
│   └── querycraft-cli.py
├── connectors/             # 数据源连接器
│   ├── mysql/
│   ├── hive/
│   ├── spark/
│   └── ...
├── docs/                   # 文档
├── docker-compose.yml
├── README.md
└── ROADMAP.md
```

## 快速开始

```bash
# 克隆项目
git clone https://github.com/openclaw/querycraft.git
cd querycraft

# 使用 Docker 启动
docker-compose up -d

# 或手动启动
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API 示例

```bash
# 生成 SQL
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "查询最近30天的订单总金额",
    "dialect": "mysql",
    "datasource": "shop_db"
  }'

# 响应
{
  "sql": "SELECT SUM(amount) as total_amount FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)",
  "confidence": 92,
  "explanation": "根据订单表的created_at字段筛选最近30天数据，并计算amount字段的总和"
}
```

## 配置

```yaml
# config.yaml
server:
  host: 0.0.0.0
  port: 8000

llm:
  provider: openai  # openai | deepseek | local
  model: gpt-4
  api_key: ${OPENAI_API_KEY}

datasources:
  - name: shop_db
    type: mysql
    host: localhost
    port: 3306
    database: shop
```

## 开发状态

- [x] 项目架构设计
- [ ] 后端核心引擎
- [ ] Web UI 开发
- [ ] CLI 工具
- [ ] Docker 部署
- [ ] 文档完善

---
*基于 text2sql-engine skill 开发*
*创建时间: 2026-03-06*