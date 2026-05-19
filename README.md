# Mini Auth

轻量级统一认证服务，为 [Traefik ForwardAuth](https://doc.traefik.io/traefik/middlewares/http/forwardauth/) 提供登录页、会话校验与用户管理。未登录访问受保护站点时，自动跳转到登录页；登录成功后通过 Cookie 维持会话，Traefik 在每次请求前调用 `/verify` 完成鉴权。

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.13+ |
| Web 框架 | [FastAPI](https://fastapi.tiangolo.com/) |
| ORM / 模型 | [SQLModel](https://sqlmodel.tiangolo.com/) + SQLAlchemy 2（异步） |
| 数据库 | SQLite（[aiosqlite](https://github.com/omnilib/aiosqlite)） |
| 缓存 / 会话 | [Redis](https://redis.io/) |
| 数据库迁移 | [Alembic](https://alembic.sqlalchemy.org/) |
| 密码哈希 | [pwdlib](https://github.com/frankie567/pwdlib)（Argon2） |
| 模板 | Jinja2（服务端渲染登录页与管理后台） |
| 前端 | 原生 HTML / CSS / JavaScript |
| CLI | [Typer](https://typer.tiangolo.com/) |
| 反向代理集成 | Traefik ForwardAuth |
| 包管理 | [uv](https://github.com/astral-sh/uv) |
| 容器 | Docker + Docker Compose |

## 功能特性

- **ForwardAuth**：`/verify` 供 Traefik 校验会话，未登录重定向到登录页
- **登录页**：记住我、密码显示切换、明暗主题
- **登录防护**：按 IP 频率限制；密码连续错误 3 次后要求验证码
- **管理后台**：`/admin` 用户 CRUD（需管理员登录）
- **CLI**：命令行创建用户

## 项目结构

```
mini-auth/
├── app/                    # 应用代码
│   ├── app.py              # FastAPI 入口
│   ├── core/               # 配置、数据库、Redis、会话、验证码等
│   └── modules/
│       ├── auth/           # 登录 / 登出 / verify
│       ├── admin/          # 管理后台 API
│       └── user/           # 用户模型与仓储
├── alembic/                # 数据库迁移
├── templates/              # Jinja2 模板
├── static/                 # 静态资源
├── cli.py                  # 命令行工具
├── docker-compose.yml
└── Dockerfile
```

## 快速开始

### 环境要求

- Python 3.13+
- Redis（会话与登录防护依赖）
- [uv](https://github.com/astral-sh/uv)（推荐）或 pip

### 1. 安装依赖

```bash
uv sync
source .venv/bin/activate
```

### 2. 启动 Redis

```bash
# 本地示例
docker run -d --name mini-auth-redis -p 6379:6379 redis:7-alpine
```

### 3. 初始化数据库

首次迁移需根据模型自动生成脚本（**必须带 `--autogenerate`**，否则迁移文件可能为空）：

```bash
alembic revision --autogenerate -m "create table"
alembic upgrade head
```

若已有迁移文件，直接执行：

```bash
alembic upgrade head
```

### 4. 创建管理员

```bash
# 指定用户名和密码
python cli.py create-user admin -p admin123 --admin

# 交互输入密码（会提示确认）
python cli.py create-user alice

# 可选邮箱
python cli.py create-user bob -p secret -e bob@example.com
```

### 5. 启动服务

```bash
uvicorn app.app:app --reload --host 0.0.0.0 --port 4181
```

访问 [http://localhost:4181/login](http://localhost:4181/login)，管理后台：[http://localhost:4181/admin](http://localhost:4181/admin)。

## Docker 部署

```bash
docker compose up -d --build
```

`docker-compose.yml` 已通过 Traefik Labels 暴露服务，默认监听 **4181** 端口。部署前请修改：

- `AUTH_PUBLIC_URL`：登录页对外可访问的完整 URL（`verify` 重定向拼接用）
- `COOKIE_DOMAIN` / `COOKIE_SECURE`：与公网域名、HTTPS 匹配

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `AUTH_PUBLIC_URL` | `http://auth.localhost` | 公网登录页地址 |
| `DB_URL` | `sqlite+aiosqlite:///auth.db` | 数据库连接 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接 |
| `COOKIE_NAME` | `mini_auth_session` | 会话 Cookie 名 |
| `COOKIE_DOMAIN` | — | Cookie 域名（跨子域时设置） |
| `COOKIE_SECURE` | `false` | 是否仅 HTTPS 发送 Cookie |
| `COOKIE_MAX_AGE` | `28800` | 会话 Cookie 有效期（秒） |
| `SESSION_TTL` | `28800` | Redis 会话 TTL（秒） |
| `REMEMBER_ME_MAX_AGE` | `2592000` | 「记住我」时长（秒，默认 30 天） |
| `LOGIN_RATE_LIMIT` | `10` | 每 IP 登录频率上限（次/窗口） |
| `LOGIN_RATE_WINDOW` | `60` | 频率限制窗口（秒） |
| `LOGIN_FAIL_CAPTCHA_AFTER` | `3` | 连续失败几次后显示验证码 |
| `LOGIN_FAIL_WINDOW` | `900` | 失败计数窗口（秒） |
| `CAPTCHA_TTL` | `300` | 验证码有效期（秒） |

## 在 Traefik 中配置

### 推荐：Docker Labels（本项目已内置）

`docker-compose.yml` 中 `auth` 服务已配置路由与 ForwardAuth 中间件，核心要点：

- 认证服务端口：**4181**（非 80）
- ForwardAuth 地址：`http://mini-auth:4181/verify`
- 回传头：`X-Forwarded-User`、`X-Forwarded-Email`、`X-Forwarded-Groups`

其他业务服务只需挂上 `mini-auth` 中间件即可受保护。

### 文件方式：动态配置目录

若使用 Traefik 文件 Provider，可参考如下目录结构：

```
.
├── docker-compose.yml
└── traefik/
    ├── traefik.yml
    ├── dynamic/
    │   ├── mini-auth.yml    # 认证服务路由
    │   └── whoami.yml       # 受保护业务示例
    └── logs/
```

**mini-auth 路由**（`dynamic/mini-auth.yml`）：

```yaml
http:
  routers:
    mini-auth:
      rule: "Host(`auth.example.com`)"
      service: mini-auth-svc
      entryPoints:
        - websecure
      tls: {}

  services:
    mini-auth-svc:
      loadBalancer:
        servers:
          - url: "http://mini-auth:4181"
```

**受保护站点**（`dynamic/whoami.yml`）：

```yaml
http:
  middlewares:
    mini-auth:
      forwardAuth:
        address: "http://mini-auth:4181/verify"
        trustForwardHeader: true
        authResponseHeaders:
          - "X-Forwarded-User"
          - "X-Forwarded-Email"
          - "X-Forwarded-Groups"

  routers:
    whoami:
      rule: "Host(`whoami.example.com`)"
      service: whoami-svc
      entryPoints:
        - websecure
      middlewares:
        - mini-auth
      tls: {}

  services:
    whoami-svc:
      loadBalancer:
        servers:
          - url: "http://whoami:80"
```

### 鉴权流程

```
用户请求 whoami.example.com
        │
        ▼
   Traefik ForwardAuth ──► GET mini-auth:4181/verify
        │                        │
        │                   有有效 Cookie
        │                        ├─► 200 + X-Forwarded-* 头
        │                        │
        │                   无 Cookie / 过期
        │                        └─► 302 到 AUTH_PUBLIC_URL/login?rd=...
        ▼
   放行或拒绝访问后端
```

## 小白指南：HTTP 与 HTTPS 怎么选、怎么配

### 先搞懂两件事

| | HTTP | HTTPS |
|---|------|-------|
| 地址栏 | `http://` 开头 | `https://` 开头，通常有小锁图标 |
| 是否加密 | 否，密码在网络上明文传输 | 是，需要 TLS 证书 |
| 适用场景 | 本机开发、内网调试 | 公网、生产环境 |
| mini-auth 要改什么 | `COOKIE_SECURE=false`，`AUTH_PUBLIC_URL` 用 `http://` | `COOKIE_SECURE=true`，`AUTH_PUBLIC_URL` 用 `https://` |

**记住一条：** 浏览器用什么协议访问登录页，`AUTH_PUBLIC_URL` 就要写成什么协议；Cookie 是否加密（`COOKIE_SECURE`）也要和协议一致，否则会出现「登录成功但马上又跳回登录页」。

---

### 场景一：本机开发（HTTP，最简单）

适合：在自己电脑上跑 `uvicorn`，不经过 Traefik。

**1. 环境变量（可不设，用默认值即可）**

```bash
export AUTH_PUBLIC_URL=http://localhost:4181
export COOKIE_SECURE=false
# COOKIE_DOMAIN 不要设，留空
export REDIS_URL=redis://localhost:6379/0
```

**2. 启动**

```bash
uvicorn app.app:app --reload --host 0.0.0.0 --port 4181
```

**3. 浏览器访问**

- 登录页：<http://localhost:4181/login>
- 管理后台：<http://localhost:4181/admin>

**4. 用 curl 自测登录是否成功**

```bash
# 登录（把用户名密码换成你创建的）
curl -c cookies.txt -X POST http://localhost:4181/login \
  -d "username=admin&password=admin123&rd=/"

# 看 Cookie 里有没有 mini_auth_session
cat cookies.txt

# 带 Cookie 访问 verify（应返回 200，不是 302）
curl -b cookies.txt -i http://localhost:4181/verify
```

---

### 场景二：本机模拟域名（HTTP + hosts）

适合：想和 Traefik 一样用 `auth.localhost` 这种域名调试，但仍用 HTTP。

**1. 改 hosts 文件**

```text
# macOS / Linux: /etc/hosts
# Windows: C:\Windows\System32\drivers\etc\hosts
127.0.0.1 auth.localhost
127.0.0.1 whoami.localhost
```

**2. 环境变量**

```bash
export AUTH_PUBLIC_URL=http://auth.localhost:4181
export COOKIE_SECURE=false
```

**3. 访问**

- <http://auth.localhost:4181/login>

Traefik 转发时一般不带 `:4181`，本机直连服务需要带端口；走 Traefik 时见场景三。

---

### 场景三：公网生产（HTTPS，推荐）

适合：域名已解析到服务器，前面有 Traefik（或其它反向代理）终结 TLS。

```
用户浏览器 ──HTTPS──► Traefik（证书在这里）──HTTP──► mini-auth:4181
```

对外全是 `https://`，容器内 mini-auth 仍监听 4181 即可。

**1. 在 Traefik 上配好证书**

常见做法（任选其一）：

- Let's Encrypt 自动申请（Traefik `certresolver`）
- Cloudflare 等 CDN 提供证书
- 自己上传证书到 Traefik

mini-auth **本身不处理 HTTPS**，证书在 Traefik 层。

**2. docker-compose 环境变量示例**

```yaml
environment:
  AUTH_PUBLIC_URL: https://auth.example.com      # 必须是用户浏览器里看到的完整地址
  COOKIE_SECURE: "true"                          # HTTPS 必须为 true
  COOKIE_DOMAIN: .example.com                    # 可选：多子域共享登录态时设置
  REDIS_URL: redis://redis:6379/0
```

**3. Traefik 路由示例（HTTPS 入口 `websecure`）**

```yaml
# 认证服务对外暴露
traefik.http.routers.mini-auth.rule=Host(`auth.example.com`)
traefik.http.routers.mini-auth.entrypoints=websecure
traefik.http.routers.mini-auth.tls.certresolver=letsencrypt

# 业务站挂 ForwardAuth
traefik.http.middlewares.mini-auth.forwardauth.address=http://mini-auth:4181/verify
```

**4. 浏览器访问**

- 登录页：`https://auth.example.com/login`
- 受保护站：`https://whoami.example.com`（未登录会跳到上面的登录页）

**5. 用 curl 自测（HTTPS）**

```bash
curl -c cookies.txt -X POST https://auth.example.com/login \
  -d "username=admin&password=admin123&rd=https://whoami.example.com/" \
  -L

curl -b cookies.txt -i https://auth.example.com/verify
```

---

### HTTP / HTTPS 配置对照表（复制即用）

| 配置项 | 本机 HTTP | 公网 HTTPS |
|--------|-----------|------------|
| `AUTH_PUBLIC_URL` | `http://localhost:4181` 或 `http://auth.localhost:4181` | `https://auth.example.com` |
| `COOKIE_SECURE` | `false` | `true` |
| `COOKIE_DOMAIN` | 不设（`None`） | 如 `.example.com`（需要跨子域时） |
| Traefik 入口 | 可不使用 | `websecure` + TLS |
| 浏览器地址栏 | `http://` | `https://` |

---

### 常见小白坑

1. **`AUTH_PUBLIC_URL` 写错协议**  
   用户用 `https://` 打开，你却配了 `http://`，登录后会跳到错误的地址。

2. **HTTPS 站点忘了开 `COOKIE_SECURE`**  
   浏览器可能拒绝写入 Cookie，表现为永远登录不上。

3. **`COOKIE_DOMAIN` 设太宽或设错**  
   只在单域名用时建议先不设；确认跨子域需求后再填 `.example.com` 这种父域。

4. **本机直连 4181，却按 Traefik 域名配了 `AUTH_PUBLIC_URL`**  
   本地开发用 `http://localhost:4181`；上线再改成公网 `https://` 地址。

5. **只改了环境变量没重启容器**  
   `docker compose up -d` 或重启 `uvicorn` 后配置才会生效。

---

## 主要 API

| 路径 | 方法 | 说明 |
|------|------|------|
| `/verify` | GET | Traefik ForwardAuth 校验入口 |
| `/login` | GET / POST | 登录页 / 提交登录 |
| `/logout` | GET | 登出 |
| `/admin` | GET | 管理后台页面 |
| `/admin/api/users` | GET / POST / PATCH / DELETE | 用户 CRUD |
| `/health` | GET | 健康检查 |

## 常见问题

**迁移后仍报 `no such table: users`**

检查 `alembic/versions/` 下迁移文件的 `upgrade()` 是否为空；若为空，需用 `--autogenerate` 重新生成或手写建表逻辑后 `alembic upgrade head`。

**登录后立即失效**

确认 Redis 可连接，且 `AUTH_PUBLIC_URL`、`COOKIE_DOMAIN` 与浏览器访问域名一致。

**ForwardAuth 一直跳转登录**

确认 Traefik 将 `X-Forwarded-Proto`、`X-Forwarded-Host`、`X-Forwarded-Uri` 传给 `/verify`，且 Cookie 域名与 HTTPS 设置正确。
