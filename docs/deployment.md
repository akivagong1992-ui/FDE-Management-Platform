# Deployment & Local Dev Quick Start

> Phase 0 minimum — get all three apps running.

## 一次性准备

```bash
# 1. 启动 Postgres + Redis (后端 + 数据库)
docker compose up -d postgres redis

# 2. 后端依赖
cd backend
uv sync
cp .env.example .env       # 修改 JWT_SECRET 等

# 3. 两个前端
cd ../admin-web && pnpm install
cd ../cockpit-screen && pnpm install
```

## 日常启动（三个终端）

```bash
# Terminal 1 — 后端
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Terminal 2 — 管理后台
cd admin-web && pnpm dev      # http://localhost:5173

# Terminal 3 — 驾驶舱大屏
cd cockpit-screen && pnpm dev # http://localhost:5174
```

## 默认账号

| 用户名 | 密码 | 角色 |
|---|---|---|
| admin | admin123 | lead (团队负责人) |

> 首次启动后端时会自动 create_all + seed admin 用户。Phase 1 起切换到 Alembic 迁移。

## 接口快速验证

- 健康检查：`curl http://localhost:8000/health`
- 登录：`curl -X POST http://localhost:8000/api/admin/auth/login -d 'username=admin&password=admin123'`
- 驾驶舱占位数据：`curl http://localhost:8000/api/cockpit/overview`（localhost 默认在白名单内）

## 全量 Docker（Phase 1+ 完善）

```bash
docker compose up -d --build
# backend → http://localhost:8000
# 前端工程目前不在 compose 中，本地 pnpm dev 跑即可
```
