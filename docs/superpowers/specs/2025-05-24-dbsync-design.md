# DBSync — 数据库备份迁移系统设计

**日期:** 2025-05-24
**状态:** 已定稿

## 概述

Web 管理后台，支持 MySQL 和 PostgreSQL 的全量/增量备份、恢复、同库/跨库数据迁移。

## 技术栈

| 层         | 技术                                  |
|-----------|--------------------------------------|
| 前端       | Vite 8 + Vue 3 + TDesign + Pinia     |
| 后端       | Python 3.12 + FastAPI                |
| 异步任务   | Celery + Redis                       |
| WebSocket | FastAPI WebSocket                    |
| 元数据     | MySQL 8                              |
| 部署       | Docker + docker-compose（开发/生产）   |

## 架构

```
前端 (Vue 3 + TDesign)
    │ REST API + WebSocket
    ▼
FastAPI 后端
    ├─ API 层 (CRUD + 触发任务)
    ├─ WebSocket (实时进度推送)
    └─ Service 层 (业务逻辑)
        │ 任务投递
        ▼
    Redis 消息队列
        │
        ▼
    Celery Worker
        ├─ 全量/增量备份
        ├─ 恢复
        └─ 同库/跨库迁移
            │
    ┌───────┼───────┐
    ▼       ▼       ▼
  MySQL  PostgreSQL  文件存储
```

## 数据模型

### datasources — 数据源配置
| 字段             | 类型         | 说明                     |
|-----------------|-------------|-------------------------|
| id              | INT PK AI   |                         |
| name            | VARCHAR(64) | 数据源名称                |
| type            | ENUM(mysql,postgresql) | 数据库类型      |
| host            | VARCHAR(255)|                         |
| port            | INT         | 默认 3306/5432           |
| username        | VARCHAR(64) |                         |
| password        | VARCHAR(512)| AES 加密                 |
| database        | VARCHAR(64) | 默认库                    |
| ssl_config      | JSON        | SSL 配置，可空             |
| extra_params    | JSON        | 额外连接参数               |
| is_active       | BOOL        | 启用状态                  |
| created_at      | DATETIME    |                         |
| updated_at      | DATETIME    |                         |

### backup_tasks — 备份任务定义
| 字段             | 类型                | 说明                        |
|-----------------|--------------------|----------------------------|
| id              | INT PK AI          |                            |
| name            | VARCHAR(128)       | 任务名                      |
| datasource_id   | FK→datasources     |                            |
| backup_type     | ENUM(full,incremental) |                        |
| schedule_config | JSON               | cron 配置，null=手动        |
| storage_path    | VARCHAR(512)       | 备份文件存储路径              |
| retention_days  | INT                | 保留天数                    |
| compression     | BOOL               | 是否 gzip 压缩              |
| is_enabled      | BOOL               |                            |
| created_at      | DATETIME           |                            |
| updated_at      | DATETIME           |                            |

### backup_records — 备份执行记录
| 字段                | 类型               | 说明                       |
|--------------------|-------------------|----------------------------|
| id                 | INT PK AI         |                            |
| task_id            | FK→backup_tasks   |                            |
| status             | ENUM(running,success,fail) |                  |
| started_at         | DATETIME          |                            |
| finished_at        | DATETIME          |                            |
| file_path          | VARCHAR(512)      |                            |
| file_size          | BIGINT            | bytes                      |
| checksum           | VARCHAR(64)       | SHA256                     |
| error_message      | TEXT              |                            |
| incremental_base_id| FK→backup_records | 基于的上次全量备份            |

### migration_tasks — 迁移任务定义
| 字段                   | 类型                    | 说明              |
|-----------------------|------------------------|------------------|
| id                    | INT PK AI              |                  |
| name                  | VARCHAR(128)           |                  |
| source_datasource_id  | FK→datasources         |                  |
| target_datasource_id  | FK→datasources         |                  |
| table_include         | JSON                   | 包含表列表，null=全部 |
| table_exclude         | JSON                   | 排除表列表          |
| transfer_type         | ENUM(schema_only,data_only,schema_and_data) | |
| created_at            | DATETIME               |                  |
| updated_at            | DATETIME               |                  |

### migration_records — 迁移执行记录
| 字段                | 类型                     | 说明     |
|--------------------|-------------------------|---------|
| id                 | INT PK AI               |         |
| task_id            | FK→migration_tasks      |         |
| status             | ENUM(running,success,fail) |      |
| started_at         | DATETIME                |         |
| finished_at        | DATETIME                |         |
| rows_transferred   | INT                     |         |
| error_message      | TEXT                    |         |

### task_logs — 统一任务日志
| 字段            | 类型                            | 说明                      |
|----------------|--------------------------------|--------------------------|
| id             | INT PK AI                      |                          |
| task_type      | ENUM(backup,migration,restore) |                          |
| task_record_id | INT                            | 关联 backup/migration/restore 记录 ID |
| level          | ENUM(info,warning,error)       |                          |
| message        | TEXT                           |                          |
| created_at     | DATETIME                       |                          |

## API 设计

### 数据源
| 方法   | 路径                            | 说明     |
|--------|--------------------------------|---------|
| POST   | /api/v1/datasources            | 创建    |
| GET    | /api/v1/datasources            | 列表    |
| GET    | /api/v1/datasources/{id}       | 详情    |
| PUT    | /api/v1/datasources/{id}       | 更新    |
| DELETE | /api/v1/datasources/{id}       | 删除    |
| POST   | /api/v1/datasources/{id}/test  | 测试连接 |

### 备份
| 方法   | 路径                                  | 说明       |
|--------|--------------------------------------|-----------|
| POST   | /api/v1/backup-tasks                 | 创建任务   |
| GET    | /api/v1/backup-tasks                 | 列表      |
| PUT    | /api/v1/backup-tasks/{id}            | 更新      |
| DELETE | /api/v1/backup-tasks/{id}            | 删除      |
| POST   | /api/v1/backup-tasks/{id}/run        | 手动触发   |
| GET    | /api/v1/backup-records               | 记录列表   |
| GET    | /api/v1/backup-records/{id}          | 记录详情   |
| POST   | /api/v1/backup-records/{id}/restore  | 恢复      |

### 迁移
| 方法   | 路径                                  | 说明     |
|--------|--------------------------------------|---------|
| POST   | /api/v1/migration-tasks              | 创建    |
| GET    | /api/v1/migration-tasks              | 列表    |
| DELETE | /api/v1/migration-tasks/{id}         | 删除    |
| POST   | /api/v1/migration-tasks/{id}/run     | 执行    |
| GET    | /api/v1/migration-records            | 记录列表 |

### WebSocket
| 路径                | 说明                       |
|--------------------|---------------------------|
| /ws/tasks/{task_id}| 实时推送任务日志和进度百分比 |

### 安全
- 数据库密码 AES-256-GCM 加密存储，密钥环境变量注入
- API 返回密码字段脱敏为 `***`

## 执行引擎

### 全量备份
- MySQL: `mysqldump --single-transaction --routines --triggers --set-gtid-purged=OFF`
- PG: `pg_dump -Fc --no-owner`
- 打包: gzip 压缩，计算 SHA256

### 增量备份
- MySQL: 基于 binlog 位点，`mysqlbinlog --start-position=...`
- PG: 基于 WAL 归档，需先全量备份作为基线

### 恢复
- 自动识别备份文件格式，选择对应恢复工具
- 支持指定目标数据源、时间点恢复

### 同库迁移
- 从源导出 → 导入目标（schema/data/schema_and_data）
- 分表并行传输

### 跨库迁移 (类型映射)

| MySQL       | PostgreSQL         |
|------------|--------------------|
| INT        | INTEGER            |
| BIGINT     | BIGINT             |
| VARCHAR(n) | VARCHAR(n)         |
| TEXT       | TEXT               |
| DATETIME   | TIMESTAMP          |
| TINYINT    | SMALLINT           |
| DOUBLE     | DOUBLE PRECISION   |
| BLOB       | BYTEA              |
| ENUM       | VARCHAR            |
| AUTO_INCREMENT | SERIAL         |

## 前端页面

| 路由                      | 页面          | TDesign 核心组件              |
|--------------------------|--------------|-----------------------------|
| /                        | 仪表盘        | Card, Progress, Tag        |
| /datasources             | 数据源管理     | Table, Dialog, Form, Button |
| /datasources/:id         | 数据源详情     | Descriptions, Tag           |
| /backup                  | 备份任务列表   | Table, Switch, Dialog       |
| /backup/create           | 新建备份任务   | Form, Select, Input, Switch |
| /backup/:id              | 任务详情      | Table, Timeline, Button     |
| /backup/:id/record/:rid  | 备份记录详情   | Descriptions, Log Preview   |
| /restore                 | 恢复管理      | Table, Form, Select         |
| /migration               | 迁移任务列表   | Table, Dialog               |
| /migration/create        | 新建迁移任务   | Form, Select, Transfer     |
| /migration/:id           | 迁移详情      | Table, Progress             |
| /schedules               | 定时策略      | Tag, Switch, Dialog         |
| /logs                    | 统一日志      | Table, Search, Filter       |

实时进度通过 WebSocket 连接，TaskProgress 组件显示百分比 + 日志流。

## Docker 部署

### 服务
| 服务     | 镜像                   | 端口        |
|---------|-----------------------|------------|
| backend | Python:3.12-slim      | 8000       |
| worker  | Python:3.12-slim      | —          |
| beat    | Python:3.12-slim      | —          |
| frontend| node:22 (dev) / nginx (prod) | 5173 / 80 |
| mysql   | mysql:8               | 3306       |
| redis   | redis:7-alpine        | 6379       |

### 开发环境
`docker compose up` 启动全部服务，后端和前端均热重载。

### 生产环境
`docker compose -f docker-compose.prod.yml up -d`，前端 nginx 反代后端 API，前端构建为静态文件。

## 测试策略

### 后端 (pytest)
- 单元测试: Service 层、Utils 层
- 集成测试: API 端点 + 真实 MySQL/Redis（Testcontainers）
- Worker 测试: Mock subprocess，参数校验

### 前端 (vitest + @vue/test-utils)
- 组件测试: 表单、表格、对话框等
- 页面测试: 路由、API 交互

### 独立测试环境
`docker compose -f docker-compose.test.yml up -d` 提供独立 MySQL/Redis 测试容器。

## 目录结构

```
dbsync/
├── backend/
│   ├── app/
│   │   ├── api/               # FastAPI 路由 + WebSocket
│   │   │   ├── datasources.py
│   │   │   ├── backup.py
│   │   │   ├── migration.py
│   │   │   └── ws.py
│   │   ├── core/              # 配置、加密、依赖注入
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/            # SQLAlchemy 模型
│   │   ├── schemas/           # Pydantic 模型
│   │   ├── services/          # 业务逻辑层
│   │   ├── worker/            # Celery 任务
│   │   │   ├── app.py         # Celery 实例
│   │   │   ├── backup.py
│   │   │   ├── restore.py
│   │   │   ├── migration.py
│   │   │   └── engines/
│   │   │       ├── base.py
│   │   │       ├── mysql.py
│   │   │       └── postgresql.py
│   │   └── main.py
│   ├── alembic/               # 数据库迁移
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   ├── components/        # 通用组件
│   │   ├── api/               # HTTP + WebSocket 封装
│   │   ├── stores/            # Pinia stores
│   │   ├── router/            # Vue Router
│   │   ├── assets/
│   │   ├── App.vue
│   │   └── main.ts
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── Dockerfile
├── docker/
│   ├── backend/Dockerfile
│   ├── frontend/Dockerfile
│   └── nginx/nginx.conf
├── docker-compose.yml
├── docker-compose.prod.yml
├── docker-compose.test.yml
└── .env.example
```
