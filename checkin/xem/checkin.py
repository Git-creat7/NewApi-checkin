# token
# 本地重复签到测试：token测试通过
#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timezone

# Windows 控制台 UTF-8 输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from curl_cffi import requests


BASE_URL = os.getenv("XEM_BASE_URL", "http://new.xem8k5.top:3000").rstrip("/")
SESSION = os.getenv("XEM_SESSION", "").strip()
API_USER = os.getenv("XEM_API_USER", "").strip()
SYSTEM_ACCESS_TOKEN = os.getenv("XEM_SYSTEM_ACCESS_TOKEN", "").strip()
# 推送环境变量
PUSH_KEY = os.getenv("PUSH_KEY", "").strip()
TIMEOUT = int(os.getenv("XEM_TIMEOUT", "30"))
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN", "").strip()


class ApiError(RuntimeError):
    pass


def send_pushplus(title: str, content: str) -> None:
    if not PUSHPLUS_TOKEN:
        return

    try:
        response = requests.post(
            "https://www.pushplus.plus/send",
            json={
                "token": PUSHPLUS_TOKEN,
                "title": title,
                "content": content,
                "template": "markdown",
            },
            impersonate="chrome124",
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        print(f"PushPlus response: {response.text[:300]}")
    except Exception as exc:
        print(f"PushPlus send failed: {exc}", file=sys.stderr)


def current_day() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")


def make_session_with_token() -> requests.Session:
    """使用 system_access_token 认证"""
    if not SYSTEM_ACCESS_TOKEN:
        raise ApiError("XEM_SYSTEM_ACCESS_TOKEN is required.")
    if not API_USER:
        raise ApiError("XEM_API_USER is required when using system_access_token.")

    session = requests.Session(impersonate="chrome124", timeout=TIMEOUT)
    session.headers.update(
        {
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"Bearer {SYSTEM_ACCESS_TOKEN}",
            "new-api-user": API_USER,
            "Origin": BASE_URL,
            "Referer": f"{BASE_URL}/console",
        }
    )
    return session


def make_session_with_cookie(include_api_user: bool = True) -> requests.Session:
    """使用 session cookie 认证"""
    if not SESSION:
        raise ApiError("XEM_SESSION is required.")

    from urllib.parse import urlparse
    domain = urlparse(BASE_URL).netloc

    session = requests.Session(impersonate="chrome124", timeout=TIMEOUT)
    session.cookies.set("session", SESSION, domain=domain)
    session.headers.update(
        {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": BASE_URL,
            "Referer": f"{BASE_URL}/console",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Cookie": f"session={SESSION}",
        }
    )
    if include_api_user and API_USER:
        session.headers["new-api-user"] = API_USER
    return session


def ensure_json_response(response, label: str) -> dict:
    try:
        data = response.json()
    except Exception as exc:
        raise ApiError(f"{label} returned invalid JSON: {response.text[:200]}") from exc
    print(f"{label}: {response.text[:300]}")
    return data


def fetch_site_status(session: requests.Session) -> dict:
    response = session.get(f"{BASE_URL}/api/status")
    data = ensure_json_response(response, "站点状态响应")
    if not data.get("success"):
        raise ApiError(data.get("message") or "Failed to fetch site status.")
    return data.get("data") or {}


def fetch_self(session: requests.Session) -> dict:
    response = session.get(f"{BASE_URL}/api/user/self")
    data = ensure_json_response(response, "用户信息响应")
    if not data.get("success"):
        raise ApiError(data.get("message") or "Authentication failed.")

    user = data.get("data") or {}
    actual_id = str(user.get("id", "")).strip()
    if API_USER and actual_id and API_USER != actual_id:
        raise ApiError(
            f"XEM_API_USER={API_USER} 与当前登录账号 id={actual_id} 不一致，请改成 {actual_id}。"
        )
    return user


def fetch_checkin_status(session: requests.Session) -> dict:
    response = session.get(f"{BASE_URL}/api/user/checkin")
    return ensure_json_response(response, "XEM 签到状态响应")


def post_checkin(session: requests.Session) -> dict:
    response = session.post(f"{BASE_URL}/api/user/checkin")
    return ensure_json_response(response, "XEM 签到动作响应")


def run_once(session: requests.Session) -> int:
    site_status = fetch_site_status(session)
    if not site_status.get("checkin_enabled"):
        print("ℹ️ 签到功能未开启")
        return 0
    if site_status.get("turnstile_check"):
        print("⚠️ 站点启用了 Turnstile，继续尝试签到...")

    user = fetch_self(session)
    print(f"当前账号: id={user.get('id')} display_name={user.get('display_name')}")

    result = post_checkin(session)
    message = result.get("message") or result.get("msg") or ""
    success = bool(result.get("success") or result.get("ret") == 1)

    if not success and ("已经签到" in message or "已签到" in message):
        print(f"✅ 今日已签到: {message}")
        return 0

    if not success and "turnstile" in message.lower():
        raise ApiError(f"签到失败，需要 Turnstile 验证: {message}")

    if not success:
        raise ApiError(message or "Check-in failed.")

    # 默认接口 data 直接返回奖励额度
    reward = result.get("data")
    if reward is not None:
        try:
            reward = int(reward)
        except (TypeError, ValueError):
            reward = None

    if reward is not None:
        print(f"✅ 签到成功！今日奖励={reward}")
    else:
        print(f"✅ 签到成功: {message or result}")
    return 0


def main() -> int:
    # 优先使用 system_access_token，回退到 session cookie
    if SYSTEM_ACCESS_TOKEN:
        print("🔑 使用 system_access_token 认证")
        try:
            session = make_session_with_token()
            code = run_once(session)
            send_pushplus(
                "XEM 签到结果",
                f"### XEM 签到成功\n\n- 站点: `{BASE_URL}`\n- 时间: `{current_day()}`\n- 认证: `system_access_token`",
            )
            return code
        except ApiError as exc:
            msg = str(exc)
            print(f"⚠️ system_access_token 认证失败: {msg}")
            if not SESSION:
                send_pushplus(
                    "XEM 签到失败",
                    f"### XEM 签到失败\n\n- 站点: `{BASE_URL}`\n- 时间: `{current_day()}`\n- 认证: `system_access_token`\n- 错误: `{msg}`",
                )
                raise
            print("🔄 回退到 session cookie 认证...")

    if not SESSION:
        raise ApiError("未配置 XEM_SYSTEM_ACCESS_TOKEN 或 XEM_SESSION，无法认证。")

    print("🍪 使用 session cookie 认证")
    try:
        session = make_session_with_cookie(include_api_user=True)
        code = run_once(session)
        send_pushplus(
            "XEM 签到结果",
            f"### XEM 签到成功\n\n- 站点: `{BASE_URL}`\n- 时间: `{current_day()}`",
        )
        return code
    except ApiError as exc:
        msg = str(exc)
        if API_USER and "insufficient privileges" in msg.lower():
            print("⚠️ 使用 new-api-user 头失败，尝试仅凭 session 重试一次...")
            session = make_session_with_cookie(include_api_user=False)
            code = run_once(session)
            send_pushplus(
                "XEM 签到结果",
                f"### XEM 签到成功\n\n- 站点: `{BASE_URL}`\n- 时间: `{current_day()}`\n- 备注: `new-api-user` 回退为仅使用 session",
            )
            return code
        send_pushplus(
            "XEM 签到失败",
            f"### XEM 签到失败\n\n- 站点: `{BASE_URL}`\n- 时间: `{current_day()}`\n- 错误: `{msg}`",
        )
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ApiError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        raise SystemExit(1)