# session
# 本地重复签到测试：token测试❌ session测试✅
#!/usr/bin/env python3
import os
import sys

# Windows 控制台 UTF-8 输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from curl_cffi import requests
from urllib.parse import urlparse


BASE_URL = os.getenv("HUAN666_BASE_URL", "http://ai.huan666.de").rstrip("/")
ACCESS_TOKEN = os.getenv("HUAN666_ACCESS_TOKEN", "").strip()
SESSION = os.getenv("HUAN666_SESSION", "").strip()
API_USER = os.getenv("HUAN666_API_USER", "").strip()
TIMEOUT = int(os.getenv("HUAN666_TIMEOUT", "30"))


class ApiError(RuntimeError):
    pass


def make_session_with_token() -> requests.Session:
    if not ACCESS_TOKEN:
        raise ApiError("HUAN666_ACCESS_TOKEN is required.")
    if not API_USER:
        raise ApiError("HUAN666_API_USER is required.")

    session = requests.Session(impersonate="chrome124", timeout=TIMEOUT)
    session.headers.update(
        {
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "new-api-user": API_USER,
            "Origin": BASE_URL,
            "Referer": f"{BASE_URL}/console",
        }
    )
    return session


def make_session_with_cookie() -> requests.Session:
    if not SESSION:
        raise ApiError("HUAN666_SESSION is required.")
    if not API_USER:
        raise ApiError("HUAN666_API_USER is required.")

    domain = urlparse(BASE_URL).netloc
    session = requests.Session(impersonate="chrome124", timeout=TIMEOUT)
    session.cookies.set("session", SESSION, domain=domain)
    session.headers.update(
        {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Cookie": f"session={SESSION}",
            "new-api-user": API_USER,
            "Origin": BASE_URL,
            "Referer": f"{BASE_URL}/console",
        }
    )
    return session


def ensure_json(response, label: str) -> dict:
    try:
        data = response.json()
    except Exception as exc:
        raise ApiError(f"{label}: invalid JSON - {response.text[:200]}") from exc
    print(f"{label}: {response.text[:300]}")
    return data


def fetch_self(session: requests.Session) -> dict:
    data = ensure_json(session.get(f"{BASE_URL}/api/user/self"), "用户信息")
    if not data.get("success"):
        raise ApiError(data.get("message") or "Authentication failed.")
    return data.get("data") or {}


def post_checkin(session: requests.Session) -> dict:
    return ensure_json(session.post(f"{BASE_URL}/api/user/checkin"), "签到")


def run_once(session: requests.Session) -> int:
    user = fetch_self(session)
    print(f"当前账号: id={user.get('id')} name={user.get('display_name')}")

    result = post_checkin(session)
    message = result.get("message") or result.get("msg") or ""
    success = bool(result.get("success") or result.get("ret") == 1)

    if not success and ("已经签到" in message or "已签到" in message):
        print(f"✅ 今日已签到: {message}")
        return 0

    if not success:
        raise ApiError(message or "Check-in failed.")

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
    # 优先令牌，回退 session cookie
    if ACCESS_TOKEN:
        print("🔑 使用令牌认证")
        try:
            return run_once(make_session_with_token())
        except ApiError as exc:
            print(f"⚠️ 令牌认证失败: {exc}")
            if not SESSION:
                raise
            print("🔄 回退到 session cookie...")

    if not SESSION:
        raise ApiError("未配置 HUAN666_ACCESS_TOKEN 或 HUAN666_SESSION，无法认证。")

    print("🍪 使用 session cookie 认证")
    return run_once(make_session_with_cookie())


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ApiError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        raise SystemExit(1)
