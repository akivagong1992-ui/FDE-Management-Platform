# API Reference

Phase 0 endpoints. 完整 OpenAPI 文档：启动后端后访问 http://localhost:8000/docs

## 鉴权

- 管理后台路由 `/api/admin/*` — 需 `Authorization: Bearer <token>` 头
- 驾驶舱路由 `/api/cockpit/*` — IP 白名单 (`COCKPIT_ALLOWED_IPS`) 或 `X-Cockpit-Token` 头

## 端点速查

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| GET | `/health` | 无 | 健康检查 |
| POST | `/api/admin/auth/login` | 无 | 表单登录，返回 JWT |
| GET | `/api/admin/users` | admin/lead | 用户列表 |
| POST | `/api/admin/users` | admin/lead | 新建用户 |
| PATCH | `/api/admin/users/{id}` | admin/lead | 更新用户 |
| DELETE | `/api/admin/users/{id}` | admin/lead | 删除用户 |
| GET | `/api/admin/data-dict?category=skill` | 已登录 | 字典查询 |
| POST | `/api/admin/data-dict` | admin/lead | 新建字典项 |
| PATCH | `/api/admin/data-dict/{id}` | admin/lead | 更新字典项 |
| DELETE | `/api/admin/data-dict/{id}` | admin/lead | 删除字典项 |
| POST | `/api/admin/files/upload` | 已登录 | multipart 文件上传 |
| GET | `/api/cockpit/overview` | 白名单/token | 驾驶舱总览占位数据 |

Phase 1+ 接口按 8 大维度逐步增加。
