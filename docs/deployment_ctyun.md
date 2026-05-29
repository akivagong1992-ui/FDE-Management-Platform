# 天翼云部署指南

> 目标：把这套人力管理平台部署到天翼云 ECS，对内/对外提供访问；并打通"本地改代码 → 一行命令同步到云"的循环。
>
> 预估首次部署耗时：**1-3 小时**（含申请云资源时间）。后续每次改代码部署：**30 秒 ~ 2 分钟**。

---

## 0. 总览

### 架构

```
本地 Mac                          天翼云 ECS（一台虚拟机）
─────────                        ──────────────────────────
git push  ───→  GitHub  ───→     ┌──────────────────────────┐
                                  │ docker compose 跑 5 个容器: │
                                  │   - postgres (DB)         │
                                  │   - redis                 │
                                  │   - backend (FastAPI)     │
                                  │   - nginx (反向代理)       │
                                  │   - admin-web / cockpit   │
                                  │     （由 nginx 静态托管）  │
                                  └──────────────────────────┘
                                          ↑
                                          │  浏览器
                                       公网 IP / 域名
```

### 阶段拆解

| 阶段 | 一次性？ | 耗时 |
|---|---|---|
| 1. 买云资源 | 一次性 | 10-30 分钟（看天翼云审核） |
| 2. ECS 配机（装 docker、配 git） | 一次性 | 15 分钟 |
| 3. 拉代码 + 配 `.env.production` | 一次性 | 10 分钟 |
| 4. 首次启动 + 验证 | 一次性 | 5-10 分钟 |
| 5. 写 `deploy.sh` | 一次性 | 5 分钟 |
| **后期改代码部署** | **每次** | **30 秒 ~ 2 分钟** |

---

## 1. 买什么云资源

| # | 资源 | 推荐规格 | 月成本（粗估） | 必需？ |
|---|---|---|---|---|
| 1 | **弹性云主机 ECS** | 2 vCPU / 4 GB RAM / 60 GB 云盘 / Ubuntu 22.04 | ~ ¥120 | ✅ |
| 2 | **弹性公网 IP + 带宽** | EIP + 5 Mbps | ~ ¥40 | ✅ |
| 3 | **域名 + ICP 备案** | `.cn` 域名 + 备案 | ¥55/年 + 免费 | 仅公网访问需要 |
| 4 | **RDS PostgreSQL** | 1 vCPU / 2 GB / 20 GB | ~ ¥150 | 可选（推荐生产） |
| 5 | **OOS 对象存储** | 50 GB 标准 | ~ ¥5 | 可选（uploads 持久化） |
| 6 | **DCS Redis** | 256 MB 单节点 | ~ ¥30 | 可选 |

**最简化（够用）**：仅 #1 + #2，月成本 ~ ¥160。Postgres / Redis 都用 docker compose 内置。
**生产推荐**：#1 + #2 + #3 + #4，月成本 ~ ¥365。

> ⚠️ **磁盘别选临时盘**——重启数据丢失。一定要用云盘。

---

## 2. 首次配机（一次性）

### 2.1 SSH 上 ECS

```bash
# 在本地终端
ssh ubuntu@<ECS_公网_IP>
```

> 如果用 CentOS 9，用户名是 `root`。下面命令的 `apt` 换成 `dnf`。

### 2.2 装 Docker

```bash
# 官方一键脚本
curl -fsSL https://get.docker.com | sudo sh

# 把当前用户加入 docker 组，免 sudo
sudo usermod -aG docker $USER

# 退出再登一次让权限生效
exit
```

```bash
# 重新 SSH
ssh ubuntu@<ECS_公网_IP>

# 验证
docker --version
docker compose version
```

### 2.3 配 Docker 国内镜像加速（建议）

国内访问 Docker Hub 经常慢甚至超时。加阿里云镜像加速：

```bash
sudo mkdir -p /etc/docker
echo '{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://docker.mirrors.ustc.edu.cn"
  ]
}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
```

---

## 3. 把代码搬到 ECS

### 3.1 配置 SSH key 访问 GitHub（推荐，比 PAT 安全）

```bash
# 在 ECS 上
ssh-keygen -t ed25519 -C "ecs-manpower-deploy" -f ~/.ssh/id_ed25519 -N ""

# 显示公钥
cat ~/.ssh/id_ed25519.pub
```

**把输出的公钥复制**，打开 https://github.com/settings/keys → **New SSH key** → 粘贴 → 保存。

```bash
# 测试 GitHub 连接
ssh -T git@github.com
# 看到 "Hi <你的用户名>!" 就 OK
```

### 3.2 拉代码

```bash
mkdir -p ~/projects && cd ~/projects
git clone git@github.com:<你的GitHub账号>/FDE-Management-Platform.git
cd FDE-Management-Platform
```

> ❌ **绝对不要把 PAT (`ghp_...`) 直接写在 git remote URL 里**——`.git/config` 会泄露；任何 `git remote -v` 输出/截图都暴露 token。

---

## 4. 配置生产环境变量

```bash
cd ~/projects/FDE-Management-Platform
cp .env.production.example .env.production
```

### 4.1 生成所有密钥

```bash
echo "POSTGRES_PASSWORD=$(openssl rand -hex 24)"
echo "JWT_SECRET=$(openssl rand -hex 32)"
echo "FIELD_ENCRYPTION_KEY=$(openssl rand -base64 32)"
echo "COCKPIT_TOKEN=$(openssl rand -hex 16)"
echo "DEFAULT_ADMIN_PASSWORD=$(openssl rand -base64 12)"
```

把这些值**逐个复制**到 `.env.production` 对应行。

```bash
vim .env.production
```

### 4.2 还要改这几项

- `PUBLIC_URL` — 有域名填 `https://manpower.example.com`；无域名填 `http://<ECS_公网_IP>`
- `COCKPIT_ALLOWED_IPS` — 会议室大屏的内网出口 IP；不确定就填 `127.0.0.1`，让用户走 token

### 4.3 重要警告

⚠️ **`FIELD_ENCRYPTION_KEY` 一旦改了，已加密的字段（HKID、证件号）就解不出来**——首次生成后**严格备份这个值到密码管理器**，永远别再改。

⚠️ **`DEFAULT_ADMIN_PASSWORD` 自己记一下**——首次登录用。登录后立刻在用户管理里改成你能记的密码。

---

## 5. 首次启动

```bash
cd ~/projects/FDE-Management-Platform
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

第一次会下载基础镜像 + 构建 3 个应用镜像，**等 3-8 分钟**（看网速）。

实时跟随后端启动日志：

```bash
docker compose -f docker-compose.prod.yml logs -f backend
```

看到这两行就 OK：

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

按 `Ctrl+C` 退出 follow（不会停容器）。

```bash
# 看 5 个容器都跑起来了
docker ps
```

应该看到：`manpower-pg`、`manpower-redis`、`manpower-backend`、`manpower-nginx`（admin-web 和 cockpit-screen 由 nginx 静态托管 dist/，不是独立容器）。

---

## 6. 验证可访问

### 6.1 安全组放行端口

天翼云控制台 → ECS → 安全组 → 入方向规则：

| 协议 | 端口 | 源 | 备注 |
|---|---|---|---|
| TCP | 22 | **限你自己 IP**（不要 0.0.0.0/0） | SSH |
| TCP | 80 | 0.0.0.0/0 | HTTP（nginx）|
| TCP | 443 | 0.0.0.0/0 | HTTPS（绑域名后用）|

### 6.2 浏览器访问

```
http://<ECS_公网_IP>/admin/    ← 管理后台
http://<ECS_公网_IP>/cockpit/  ← 驾驶舱（要带 token）
http://<ECS_公网_IP>/api/health ← 返回 {"status":"ok"} 即正常
```

登录用 `admin` + 你 4.1 生成的 `DEFAULT_ADMIN_PASSWORD`，登录后**立刻改密**。

---

## 7. 写一个 `deploy.sh`（部署脚本）

ECS 上：

```bash
cat > ~/projects/FDE-Management-Platform/deploy.sh <<'EOF'
#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "▶ pulling latest code…"
git pull origin main
echo "▶ rebuilding & restarting…"
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
echo "✓ deployed at $(date)"
EOF
chmod +x ~/projects/FDE-Management-Platform/deploy.sh
```

---

## 8. 后期改代码循环（核心章节）

每次改完代码部署只需 2 步：

### 本地

```bash
# 改完代码
git add .
git commit -m "feat: …"
git push origin main
```

### 触发部署（本地一行命令）

```bash
ssh ubuntu@<ECS_公网_IP> 'bash ~/projects/FDE-Management-Platform/deploy.sh'
```

整个过程 30 秒 ~ 2 分钟，docker 只重建变化的层，前端纯改了 ts/vue 会比改了后端代码慢一点（前端 build 时间长）。

### 进阶（可选）：本地写个 alias

```bash
# 本地 ~/.zshrc 或 ~/.bashrc 加
alias mpdeploy='ssh ubuntu@<ECS_公网_IP> "bash ~/projects/FDE-Management-Platform/deploy.sh"'
```

之后 `git push && mpdeploy` 就完事。

### 再进阶：GitHub Actions 自动部署

跑顺 ≥10 次手动部署后再考虑这个。把 `.github/workflows/deploy.yml` 加上，监听 push to main 自动 SSH 到 ECS 跑 deploy.sh。**别一开始就上 CI/CD**，调起来痛苦。

---

## 9. 备份策略

### 9.1 Postgres 数据库（每天自动）

```bash
# 在 ECS 上设 crontab
crontab -e
# 加这一行：每天凌晨 3 点备份
0 3 * * * docker exec manpower-pg pg_dump -U manpower manpower | gzip > ~/backups/manpower-$(date +\%F).sql.gz
```

```bash
# 创建备份目录
mkdir -p ~/backups
```

### 9.2 备份**异地下载**（关键）

只放在 ECS 上 = 没备份。每周从本地拉一次：

```bash
# 本地跑
rsync -av ubuntu@<ECS_公网_IP>:~/backups/ ~/manpower-backups/
```

或者：备份脚本里直接 `scp` 推到另一台机器 / 同步到天翼云 OOS。

### 9.3 上传文件（`uploads/`）

工程师证书附件、客户 logo 都存在 docker volume `backend_uploads` 里。生产环境强烈建议改用对象存储——见 §11。

---

## 10. HTTPS + 域名（可选，公网用建议加）

### 10.1 域名准备

1. 买域名（阿里云/腾讯云/天翼云都行）
2. 解析到 ECS 公网 IP（A 记录）
3. **ICP 备案**（天翼云控制台 → 备案管理）—— 境内云强制要求，2 周左右

### 10.2 证书签发（用 Let's Encrypt 免费）

```bash
# 在 ECS
sudo apt install -y certbot

# 关掉 nginx 容器再签（certbot 要占 80 端口）
docker compose -f docker-compose.prod.yml stop nginx
sudo certbot certonly --standalone -d manpower.your-domain.com
docker compose -f docker-compose.prod.yml start nginx

# 证书路径：
# /etc/letsencrypt/live/manpower.your-domain.com/fullchain.pem
# /etc/letsencrypt/live/manpower.your-domain.com/privkey.pem
```

### 10.3 把证书挂进 nginx 容器

```bash
mkdir -p nginx/certs
sudo cp /etc/letsencrypt/live/manpower.your-domain.com/fullchain.pem nginx/certs/
sudo cp /etc/letsencrypt/live/manpower.your-domain.com/privkey.pem  nginx/certs/
sudo chown -R $USER:$USER nginx/certs/
docker compose -f docker-compose.prod.yml restart nginx
```

> nginx 配置已经在 `nginx/nginx.conf` 里准备好了 HTTPS 监听 443，证书路径用 `/etc/nginx/certs/{fullchain,privkey}.pem`，确认一下。

### 10.4 自动续证书（每 90 天）

```bash
sudo crontab -e
# 加这一行：每月 1 号凌晨 4 点尝试续
0 4 1 * * certbot renew --quiet --deploy-hook 'cp /etc/letsencrypt/live/manpower.your-domain.com/{fullchain,privkey}.pem /home/ubuntu/projects/FDE-Management-Platform/nginx/certs/ && docker compose -f /home/ubuntu/projects/FDE-Management-Platform/docker-compose.prod.yml restart nginx'
```

---

## 11. 用天翼云 RDS 替代自托管 Postgres（推荐生产）

自托管 Postgres 的硬伤：宿主机挂了数据就丢；ECS 续费换机也要手动迁。生产环境强烈建议天翼云 RDS：

1. 控制台 → 关系型数据库 RDS → 创建 PostgreSQL 16 实例
2. 配置安全组允许 ECS 内网 IP 访问 5432
3. 在 RDS 里创建 `manpower` 库 + `manpower` 用户
4. 修改 `docker-compose.prod.yml`：
   ```yaml
   # 删掉 services.postgres 整段
   # backend.depends_on 里删掉 postgres
   # backend.environment.DATABASE_URL 改成：
   DATABASE_URL: postgresql+asyncpg://manpower:密码@rds-xxxx.ctyun.cn:5432/manpower
   ```
5. 重启：`docker compose -f docker-compose.prod.yml --env-file .env.production up -d`

RDS 自带：每日自动备份、7 天回滚、高可用主备、慢查询监控。

---

## 12. 用天翼云 OOS 对象存储（可选，Phase 4 任务）

当前 `uploads/` 在 docker volume，ECS 换机就丢。改造方案：

1. OOS 控制台 → 创建 bucket `manpower-uploads`
2. 创建 AK/SK（控制台 → 密钥管理）
3. 后端代码改 `app/api/admin/files.py`：本地写文件 → boto3 上传到 OOS（S3 兼容协议）
4. 文件下载用预签名 URL

改造量约 50 行 Python。**这是 Phase 4 任务**，现在先用本地 uploads/ 凑合。

---

## 13. 从本地 SQLite 把演示数据迁过去（可选）

如果想把本地 demo 数据搬过去：

```bash
# 本地
scp backend/manpower.db ubuntu@<ECS>:/tmp/

# ECS 上
docker exec -it manpower-backend sh
# 容器内：
export SOURCE_SQLITE=/tmp/manpower.db
export TARGET_PG_URL=postgresql+asyncpg://manpower:密码@postgres:5432/manpower
uv run python -m scripts.migrate_sqlite_to_pg
```

脚本会按依赖顺序逐表搬运，自动重置 Postgres 的 sequence。

```bash
# 验证
docker exec manpower-pg psql -U manpower -d manpower -c "\dt"
docker exec manpower-pg psql -U manpower -d manpower -c "SELECT COUNT(*) FROM projects"
```

---

## 14. 故障排查

| 症状 | 排查 |
|---|---|
| 拉 docker 镜像超时 | 见 §2.3 配镜像加速 |
| `docker compose up` 卡 | `docker compose logs <service名>` 看具体阶段 |
| backend 一直 restart | `docker compose logs backend` —— alembic 报错 / DB 密码不一致 / `.env.production` 缺字段 |
| 浏览器访问 ECS IP 不通 | 安全组没放行 80 端口 / nginx 没起来 |
| 502 Bad Gateway | nginx 找不到 backend，先 `docker ps` 看 backend 是否 healthy |
| 驾驶舱白屏 | F12 看 Network → `/api/cockpit/*` 是否 403。本机不在 `COCKPIT_ALLOWED_IPS` 又没带 `?token=` |
| 工时 Excel 导入失败 | 表头必须完全匹配，第一列必须叫"工程师姓名" |
| 改代码 push 完线上没生效 | 忘了跑 `deploy.sh`；或 git pull 拉到了但 docker 没重 build |
| **改代码 + 部署后浏览器还是旧版** | ⚠️ 优先查 **§14.x 静默 build 失败**（不是浏览器缓存！） |
| 容器越来越占磁盘 | `docker system prune -af` 清未用镜像；建议每月一次 |
| 部署中途网络断了 | 重新 SSH 进 ECS，再跑一次 `deploy.sh` 即可，幂等 |

### 看实时日志

```bash
# 跟某个服务
docker compose -f docker-compose.prod.yml logs -f backend

# 最近 100 行
docker compose -f docker-compose.prod.yml logs --tail=100 backend
```

### 进容器 shell 排查

```bash
docker exec -it manpower-backend sh
# 容器内可以跑 python / alembic / 看文件等
```

### 14.x ⚠️ 静默 build 失败陷阱（必读）

**症状**：改了代码 → `deploy.sh` 跑完显示成功 → 浏览器硬刷 / 无痕窗口 / 改 hosts 试别的浏览器 —— **页面仍然是旧版本**，怎么折腾都不变。

**根因**：`admin-web` / `cockpit-screen` 的 build 流程是 `vue-tsc --noEmit && vite build`。如果代码里有 TypeScript 类型错误，`vue-tsc` 报错就退出，**vite build 根本没机会跑**——但 `docker compose up -d --build` 这条整体命令仍可能返回 0（看 docker 层面），结果 **docker 用了旧的 image layer 缓存，老 image 继续在跑**。从外面看，部署是"成功"的，实际什么都没变。

**确诊方法**——看 docker image 创建时间：

```bash
docker inspect manpower-admin-local --format='{{.Created}}'
# 比较一下当前时间。如果显示几小时前，部署根本没生效
date -u +%FT%TZ
```

**解决方法**——强制无缓存 build，看完整错误：

```bash
cd ~/projects/FDE-Management-Platform
docker compose -f docker-compose.prod.yml build --no-cache --progress=plain admin-web 2>&1 | tail -30
```

会清晰看到 TS 报错，比如：
```
src/views/users/UserManage.vue(71,23): error TS2322: Type 'null' is not assignable to type 'string | undefined'.
```

修代码 → 再跑 deploy.sh 就行。

**长期改进建议**（一直没上）：

1. **deploy.sh 加入 build 时间检查**——build 后比对 image timestamp，如果没更新就报错退出
2. CI 跑 `npm run build` 兜底，git push 前就发现 TS 错（GitHub Actions 一份 workflow 就够）
3. `package.json` 的 build 改成 `vite build`（去掉 `vue-tsc --noEmit`，让类型错误不阻断 build；类型检查独立到 lint）—— 看你团队偏好，**严格类型派**保留 vue-tsc，**部署优先派**去掉

---

## 15. 安全清单（上线前必过）

- [ ] `JWT_SECRET` / `FIELD_ENCRYPTION_KEY` / `POSTGRES_PASSWORD` / `COCKPIT_TOKEN` 全部用 `openssl rand` 生成真随机
- [ ] `DEFAULT_ADMIN_PASSWORD` 首次登录后立刻在用户管理改密
- [ ] 安全组 22 SSH **限源 IP**（你公司公网出口 / 你家 IP），不要 0.0.0.0/0
- [ ] `COCKPIT_ALLOWED_IPS` 真填会议室大屏内网 IP（防外网偷看驾驶舱财务数据）
- [ ] `COCKPIT_TOKEN` 至少每月轮换一次
- [ ] HTTPS 证书有 certbot 自动续期 crontab
- [ ] Postgres 每日备份 + **异地下载**（不是只放 ECS 上）
- [ ] `.env.production` 文件权限 `chmod 600 .env.production`
- [ ] **绝不把 PAT 写进 git remote URL**（用 SSH key）
- [ ] 旧的 GitHub PAT 已 revoke（如果用过的话）

---

## 16. 回滚（出问题时救命）

### 回到上一个 commit

```bash
# ECS 上
cd ~/projects/FDE-Management-Platform
git log --oneline -5         # 看最近 5 个 commit
git reset --hard <旧 commit SHA>
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

### 数据库回滚

```bash
# 找最近一次备份
ls -lh ~/backups/

# 恢复（**警告：会覆盖当前 DB 所有数据**）
gunzip -c ~/backups/manpower-2026-05-28.sql.gz | docker exec -i manpower-pg psql -U manpower -d manpower
```

### 完全重置（最后手段）

```bash
docker compose -f docker-compose.prod.yml down -v   # -v 会删 volume → 删所有 DB 数据，慎用
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

---

## 附录 A：用本地 deploy 别名

本地 `~/.zshrc` 加：

```bash
alias mpdeploy='ssh ubuntu@<ECS_公网_IP> "bash ~/projects/FDE-Management-Platform/deploy.sh"'
alias mplogs='ssh ubuntu@<ECS_公网_IP> "docker compose -f ~/projects/FDE-Management-Platform/docker-compose.prod.yml logs -f backend"'
alias mpstatus='ssh ubuntu@<ECS_公网_IP> "docker ps --format \"table {{.Names}}\t{{.Status}}\""'
```

之后日常：

```bash
mpdeploy        # 部署
mplogs          # 看后端日志
mpstatus        # 看容器状态
```

---

## 附录 B：环境变量速查

| 变量 | 用途 | 生成方式 |
|---|---|---|
| `POSTGRES_PASSWORD` | Postgres 密码 | `openssl rand -hex 24` |
| `JWT_SECRET` | JWT 签名 | `openssl rand -hex 32` |
| `FIELD_ENCRYPTION_KEY` | HKID 等敏感字段 AES 加密 | `openssl rand -base64 32` ⚠️ 改了数据解不出 |
| `COCKPIT_TOKEN` | 驾驶舱临时访问 | `openssl rand -hex 16` |
| `DEFAULT_ADMIN_PASSWORD` | 首次登录用 | `openssl rand -base64 12` |
| `PUBLIC_URL` | CORS / 链接生成 | `https://your-domain` 或 `http://<IP>` |
| `COCKPIT_ALLOWED_IPS` | 哪些 IP 免 token 看大屏 | 逗号分隔的内网 IP |
| `DEBUG` | 调试模式 | **prod 永远 false** |
