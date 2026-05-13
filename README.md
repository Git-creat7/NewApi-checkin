# NewApi 多平台自动签到

本项目用于 New API / One API 架构站点的自动签到，适合部署在 GitHub Actions 中按天定时运行。

## 支持的平台

| 平台 | 脚本路径 | 认证方式 | 主要环境变量 |
|:-----|:--------|:--------|:------------|
| [Boxying](https://www.boxying.com/register?aff=henf) | `checkin/boxying/checkin.py` | Session Cookie | `BOXYING_SESSION` `BOXYING_API_USER` |
| [ABRDNS](https://new-api.abrdns.com) | `checkin/abrdns/checkin.py` | 令牌 | `ABRDNS_ACCESS_TOKEN` `ABRDNS_API_USER` |
| [AINI8](https://api.aini8.com) | `checkin/aini8/checkin.py` | 令牌 | `AINI8_ACCESS_TOKEN` `AINI8_API_USER` |
| [Elysiver](https://elysiver.h-e.top) | `checkin/elysiver/checkin.py` | 令牌 | `ELYSIVER_ACCESS_TOKEN` `ELYSIVER_API_USER` |
| [Huan666](http://ai.huan666.de) | `checkin/huan666/checkin.py` | 令牌/Session | `HUAN666_ACCESS_TOKEN` `HUAN666_SESSION` `HUAN666_API_USER` |
| [XEM](http://new.xem8k5.top:3000/register?aff=Byib) | `checkin/xem/checkin.py` | 令牌/Session | `XEM_SYSTEM_ACCESS_TOKEN` `XEM_SESSION` `XEM_API_USER` |

## 运行环境

- Python `3.10+`
- 依赖见 `requirements.txt`

```bash
pip install -r requirements.txt
```

## 认证方式说明

### 令牌认证（推荐）

在网站 **个人设置 → 账户管理 → 安全设置** 中点击 **生成令牌**，复制后填入对应的 `*_ACCESS_TOKEN`。令牌不会自动过期，比 Session Cookie 更稳定。

需要同时提供 `*_API_USER`（用户 ID），可从浏览器 F12 → Application → Local Storage → `user` → `id` 获取。

### Session Cookie 认证

部分站点不支持令牌认证时使用。从浏览器 F12 → Application → Cookies 中复制 `session` 值。Session 可能过期，失效后需重新获取。

## 环境变量说明

### 通用（可选）

- `PUSHPLUS_TOKEN` — PushPlus 推送 Token（仅 Boxying 和 XEM 脚本支持）

### Boxying

- `BOXYING_SESSION` — 浏览器 Cookie 中的 `session`
- `BOXYING_API_USER` — 用户 ID
- `BOXYING_TIMEOUT` — 请求超时秒数，默认 `30`

### ABRDNS

- `ABRDNS_ACCESS_TOKEN` — 系统访问令牌
- `ABRDNS_API_USER` — 用户 ID
- `ABRDNS_TIMEOUT` — 请求超时秒数，默认 `30`

### AINI8

- `AINI8_ACCESS_TOKEN` — 系统访问令牌
- `AINI8_API_USER` — 用户 ID
- `AINI8_TIMEOUT` — 请求超时秒数，默认 `30`

### Elysiver

- `ELYSIVER_ACCESS_TOKEN` — 系统访问令牌
- `ELYSIVER_API_USER` — 用户 ID
- `ELYSIVER_TIMEOUT` — 请求超时秒数，默认 `30`

### Huan666

- `HUAN666_ACCESS_TOKEN` — 系统访问令牌（优先）
- `HUAN666_SESSION` — Session Cookie（令牌失败时回退）
- `HUAN666_API_USER` — 用户 ID
- `HUAN666_TIMEOUT` — 请求超时秒数，默认 `30`

### XEM

- `XEM_SYSTEM_ACCESS_TOKEN` — 系统访问令牌（优先）
- `XEM_SESSION` — Session Cookie（令牌失败时回退）
- `XEM_API_USER` — 用户 ID
- `XEM_TIMEOUT` — 请求超时秒数，默认 `30`

## GitHub Actions 配置

### 方式一：使用脚本批量设置（推荐）

```bash
# 安装并登录 gh CLI
gh auth login

# 运行配置脚本
bash setup-secrets.sh
```

### 方式二：手动设置

进入仓库的 `Settings → Secrets and variables → Actions`，按需添加：

| Secret 名称 | 用途 |
|:------------|:-----|
| `BOXYING_SESSION` | Boxying 登录 Session |
| `BOXYING_API_USER` | Boxying 用户 ID |
| `ABRDNS_ACCESS_TOKEN` | ABRDNS 系统访问令牌 |
| `ABRDNS_API_USER` | ABRDNS 用户 ID |
| `AINI8_ACCESS_TOKEN` | AINI8 系统访问令牌 |
| `AINI8_API_USER` | AINI8 用户 ID |
| `ELYSIVER_ACCESS_TOKEN` | Elysiver 系统访问令牌 |
| `ELYSIVER_API_USER` | Elysiver 用户 ID |
| `HUAN666_ACCESS_TOKEN` | Huan666 系统访问令牌（可选） |
| `HUAN666_SESSION` | Huan666 Session Cookie |
| `HUAN666_API_USER` | Huan666 用户 ID |
| `XEM_SYSTEM_ACCESS_TOKEN` | XEM 系统访问令牌（可选） |
| `XEM_SESSION` | XEM Session Cookie |
| `XEM_API_USER` | XEM 用户 ID |
| `PUSHPLUS_TOKEN` | PushPlus 推送 Token（可选） |

### 方式三：命令行设置

```bash
gh secret set ABRDNS_ACCESS_TOKEN -b "你的令牌"
gh secret set ABRDNS_API_USER -b "你的用户ID"
```

## 工作流

当前仓库包含六个工作流文件：

- `.github/workflows/boxying.yml`
- `.github/workflows/abrdns.yml`
- `.github/workflows/aini8.yml`
- `.github/workflows/elysiver.yml`
- `.github/workflows/huan666.yml`
- `.github/workflows/xem.yml`

每个工作流在北京时间 9:00-12:00 之间触发，并随机延迟 0-180 分钟后执行签到，避免扎堆。也支持手动触发 `workflow_dispatch`。

## 本地运行

PowerShell 示例：

```powershell
$env:ABRDNS_ACCESS_TOKEN="你的令牌"; $env:ABRDNS_API_USER="你的ID"; python checkin/abrdns/checkin.py
$env:AINI8_ACCESS_TOKEN="你的令牌"; $env:AINI8_API_USER="你的ID"; python checkin/aini8/checkin.py
$env:ELYSIVER_ACCESS_TOKEN="你的令牌"; $env:ELYSIVER_API_USER="你的ID"; python checkin/elysiver/checkin.py
```

Git Bash 示例：

```bash
ABRDNS_ACCESS_TOKEN="你的令牌" ABRDNS_API_USER="你的ID" python checkin/abrdns/checkin.py
```

## 免责声明

1. 本项目仅供学习与研究自动化流程使用。
2. 自动签到可能违反目标站点服务条款，请自行评估风险。
3. 因使用本项目导致的账号、额度或其他损失，由使用者自行承担。
