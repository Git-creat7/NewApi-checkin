#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timezone

# Windows 控制台 UTF-8 输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from curl_cffi import requests


BASE_URL = os.getenv("ABRDNS_BASE_URL", "https://new-api.abrdns.com").rstrip("/")
SESSION = os.getenv("ABRDNS_SESSION", "").strip()
API_USER = os.getenv("ABRDNS_API_USER", "").strip()
# 推送环境变量
PUSH_KEY = os.getenv("PUSH_KEY", "").strip()
TIMEOUT = int(os.getenv("ABRDNS_TIMEOUT", "30"))
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


def make_session(include_api_user: bool = True) -> requests.Session:
    if not SESSION:
        raise ApiError("ABRDNS_SESSION is required.")

    session = requests.Session(impersonate="chrome124", timeout=TIMEOUT)
    session.cookies.set("session", SESSION, domain="new-api.abrdns.com")
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
            f"ABRDNS_API_USER={API_USER} 与当前登录账号 id={actual_id} 不一致，请改成 {actual_id}。"
        )
    return user


def fetch_checkin_status(session: requests.Session) -> dict:
    response = session.get(f"{BASE_URL}/api/user/checkin")
    # 典型返回: {"success":true, "message":"...", "data": 100}
    return ensure_json_response(response, "ABRDNS 签到状态响应")


def post_checkin(session: requests.Session) -> dict:
    # 经典路径不需要 seed/proof，直接 POST 即可
    response = session.post(f"{BASE_URL}/api/user/checkin")
    return ensure_json_response(response, "ABRDNS 签到动作响应")


def run_once(include_api_user: bool) -> int:
    session = make_session(include_api_user=include_api_user)

    site_status = fetch_site_status(session)
    if not site_status.get("checkin_enabled"):
        print("ℹ️ 签到功能未开启")
        return 0
    if site_status.get("turnstile_check"):
        print("⚠️ 站点启用了 Turnstile，继续尝试使用现有 session 签到...")

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
    try:
        code = run_once(include_api_user=True)
        send_pushplus(
            "ABRDNS 签到结果",
            f"### ABRDNS 签到成功\n\n- 站点: `{BASE_URL}`\n- 时间: `{current_day()}`",
        )
        return code
    except ApiError as exc:
        msg = str(exc)
        if API_USER and "insufficient privileges" in msg.lower():
            print("⚠️ 使用 new-api-user 头失败，尝试仅凭 session 重试一次...")
            code = run_once(include_api_user=False)
            send_pushplus(
                "ABRDNS 签到结果",
                f"### ABRDNS 签到成功\n\n- 站点: `{BASE_URL}`\n- 时间: `{current_day()}`\n- 备注: `new-api-user` 回退为仅使用 session",
            )
            return code
        send_pushplus(
            "ABRDNS 签到失败",
            f"### ABRDNS 签到失败\n\n- 站点: `{BASE_URL}`\n- 时间: `{current_day()}`\n- 错误: `{msg}`",
        )
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ApiError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        raise SystemExit(1)
