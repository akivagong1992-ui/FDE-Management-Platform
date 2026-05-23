# 天翼云部署指南

> 目标：把这套人力管理平台搬到天翼云 ECS，对内/对外提供 HTTPS 访问。
> 预估总耗时：**半天 ~ 一天**（含申请云资源时间）。

---

## 一、买什么云资源

| # | 资源 | 推荐规格 | 月成本（粗估）| 说明 |
|---|---|---|---|---|
| 1 | **弹性云主机 ECS** | 2 vCPU / 4 GB RAM / 100 GB SSD / CentOS 9 | ~ ¥120 | 跑所有 Docker 容器 |
| 2 | **公网 IP + 带宽** | 弹性公网 IP + 5 Mbps 带宽 | ~ ¥40 | 对外访问 |
| 3 | **域名 + ICP**（可选）| `.cn` 域名 + 备案 | ¥55/年 + 免费 | 没有也可用 IP，但 HTTPS 证书签发会更麻烦 |
| 4 | **RDS PostgreSQL**（可选但推荐）| 1 vCPU / 2 GB / 20 GB | ~ ¥150 | 替代自托管 PG，自动备份 + 高可用 |
| 5 | **OOS 对象存储**（可选）| 标准存储 50 GB | ~ ¥5 | 替代本地 uploads/，文件持久化 |
| 6 | **DCS Redis**（可选）| 256 MB 单节点 | ~ ¥30 | 替代自托管 Redis |

**最简化配置**：只买 #1 + #2 + #3，剩下用 docker-compose 自托管。月成本 ~¥215。
**生产推荐**：#1 + #2 + #3 + #4 + #5 + #6。月成本 ~¥400。

---

## 二、一次性准备

```bash
# 1. SSH 上 ECS
ssh root@<your-public-ip>

# 2. 装 Docker（CentOS 9）
sudo dnf install -y dnf-plugins-core
sudo dnf-3 config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable --now docker

# 3. 装 Git（同步代码）
sudo dnf install -y git

# 4. 拉代码
git clone <your-repo-url> /opt/manpower
cd /opt/manpower

# 5. 准备 SSL 证书（用 Let's Encrypt 免费版）
sudo dnf install -y certbot
sudo certbot certonly --standalone -d manpower.your-domain.com
mkdir -p nginx/certs
sudo cp /etc/letsencrypt/live/manpower.your-domain.com/fullchain.pem nginx/certs/
sudo cp /etc/letsencrypt/live/manpower.your-domain.com/privkey.pem  nginx/certs/

# 6. 准备前端 dist（先在本地或 ECS 上 build）
sudo dnf install -y nodejs npm
npm install -g pnpm
(cd admin-web      && pnpm install && pnpm build)
(cd cockpit-screen && pnpm install && pnpm build)
```

---

## 三、配置环境变量

```bash
cp .env.production.example .env.production

# 必改：
# - JWT_SECRET (openssl rand -hex 32)
# - FIELD_ENCRYPTION_KEY (openssl rand -base64 32)
# - POSTGRES_PASSWORD (强随机)
# - DEFAULT_ADMIN_PASSWORD
# - PUBLIC_URL (你的域名)
# - COCKPIT_ALLOWED_IPS (会议室大屏内网 IP)
vim .env.production
```

⚠️ **`FIELD_ENCRYPTION_KEY` 改了之后已加密的字段（HKID 等）就解不出来**——首次生成后**严格备份**，别再改。

---

## 四、首次启动

```bash
# 1. 起 Postgres + Redis + Backend + Nginx
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# 2. backend 会在启动时自动跑 alembic upgrade head — 建表 + 加 admin
docker compose logs backend | tail -30

# 3. 验证
curl https://manpower.your-domain.com/health
# → {"status":"ok",...}

# 4. 打开浏览器
# https://manpower.your-domain.com/admin/   ← 管理后台
# https://manpower.your-domain.com/cockpit/ ← 驾驶舱
```

---

## 五、从本地 SQLite 把演示数据迁过去（可选）

如果想把本地演示数据（30 工程师 / 28 项目 / 248 工时...）一起搬过去：

```bash
# 本地：把 manpower.db 传到 ECS
scp backend/manpower.db root@<ecs>:/tmp/

# ECS 上：
docker exec -it manpower-backend sh
# 在容器内：
export SOURCE_SQLITE=/tmp/manpower.db
export TARGET_PG_URL=postgresql+asyncpg://manpower:密码@postgres:5432/manpower
uv run python -m scripts.migrate_sqlite_to_pg
```

脚本会按依赖顺序逐表搬运，并自动重置 Postgres 的 sequence。完成后：

```bash
docker exec manpower-pg psql -U manpower -d manpower -c "\dt"
docker exec manpower-pg psql -U manpower -d manpower -c "SELECT COUNT(*) FROM projects"
```

---

## 六、改用天翼云 RDS PostgreSQL（推荐生产）

自托管 Postgres 的问题：宿主机崩了数据就丢了。生产建议直接用天翼云 RDS：

1. 控制台 → 关系型数据库 RDS → 创建 PostgreSQL 16 实例
2. 配置安全组允许 ECS 内网 IP 访问 5432 端口
3. 创建 `manpower` 库 + `manpower` 用户
4. 改 `docker-compose.prod.yml`：
   ```yaml
   # 删掉 services.postgres 和 services.pg-backup 整段
   # backend.depends_on 里删掉 postgres
   # backend.environment.DATABASE_URL 改成：
   DATABASE_URL: postgresql+asyncpg://manpower:密码@rds-xxxx.ctyun.cn:5432/manpower
   ```
5. 重启 `docker compose down && up -d`

RDS 自带：每日自动备份、7 天回滚、读写分离（按需）、监控告警。

---

## 七、改用天翼云 OOS 对象存储（可选）

当前 `uploads/` 是本地目录，ECS 换机就丢了。Phase 4 真接时：

1. OOS 控制台 → 创建 bucket `manpower-uploads`
2. 创建 AK/SK（控制台 → 密钥管理）
3. 后端代码改：把 `app/api/admin/files.py` 的本地写文件，改为 boto3 上传到 OOS（OOS 是 S3 兼容协议）
4. 文件下载地址用预签名 URL

代码改动量大约 50 行。**Phase 4 任务**，现在先用本地 uploads/。

---

## 八、日常维护

```bash
# 升级代码
cd /opt/manpower
git pull
(cd admin-web && pnpm build)
(cd cockpit-screen && pnpm build)
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build backend

# 手动备份
docker exec manpower-pg pg_dump -U manpower -d manpower -Fc -f /backups/manual-$(date +%F).dump

# 查看实时日志
docker compose -f docker-compose.prod.yml logs -f backend

# 续 SSL 证书（每 90 天）
sudo certbot renew
sudo cp /etc/letsencrypt/live/manpower.your-domain.com/{fullchain,privkey}.pem nginx/certs/
docker compose -f docker-compose.prod.yml restart nginx
```

---

## 九、安全清单（上线前必须）

- [ ] `JWT_SECRET` / `FIELD_ENCRYPTION_KEY` / `POSTGRES_PASSWORD` 已换真随机
- [ ] `DEFAULT_ADMIN_PASSWORD` 首次登录后**立即改密码**
- [ ] 安全组只放行 80/443（22 SSH 限源 IP）
- [ ] `COCKPIT_ALLOWED_IPS` 真正配置成会议室大屏 IP（防外网偷看驾驶舱）
- [ ] `COCKPIT_TOKEN` 定期轮换（建议每月）
- [ ] HTTPS 证书到期前 30 天有 certbot cron 自动续
- [ ] `pg-backup` 容器跑着（或 RDS 自带备份开启）
- [ ] 备份**异地下载**（不要只放在同一台 ECS）

---

## 故障速查

| 症状 | 排查 |
|---|---|
| backend 起不来 | `docker compose logs backend` — 看 alembic 是否报错 |
| 502 Bad Gateway | nginx 找不到 backend，检查 backend 健康状态 |
| 驾驶舱白屏 | 浏览器 F12 → Network 看 `/api/cockpit/*` 是否 403（IP 不在白名单 + 没带 token）|
| 数字滚动卡顿 | 检查浏览器是否被 zoom；4K 大屏建议 100% 缩放 |
| 工时 Excel 导入失败 | 检查表头是否完全匹配，第一列必须叫"工程师姓名" |
