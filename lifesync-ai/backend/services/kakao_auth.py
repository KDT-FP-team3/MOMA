"""카카오 OAuth 인증 서비스.

카카오 로그인 → 사용자 프로필 조회 → JWT 토큰 발급.

환경변수:
    KAKAO_CLIENT_ID: 카카오 REST API 키
    KAKAO_REDIRECT_URI: 콜백 URL
"""
import os
import time
import hmac
import hashlib
import json
import base64
import secrets
from typing import Optional

import httpx


KAKAO_AUTH_URL = "https://kauth.kakao.com"
KAKAO_API_URL = "https://kapi.kakao.com"

# JWT 비밀키 — .env에서 반드시 설정
import logging as _logging
_logger = _logging.getLogger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET", "")
if not SECRET_KEY:
    if os.getenv("ENV") == "production":
        # 프로덕션에서 JWT_SECRET 없으면 서버 시작 거부
        raise RuntimeError(
            "JWT_SECRET 환경변수가 설정되지 않았습니다. "
            "프로덕션에서는 반드시 설정하세요: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
        )
    # 개발 환경: 임시 키 자동 생성 (서버 재시작 시 세션 무효화됨)
    SECRET_KEY = secrets.token_urlsafe(64)
    _logger.warning(
        "JWT_SECRET 미설정 — 개발용 임시 키 생성됨. "
        "서버 재시작 시 기존 토큰이 무효화됩니다."
    )


def _make_token(user_id: str, nickname: str, email: str = "") -> str:
    """HMAC-SHA256 기반 토큰 생성."""
    payload = {
        "user_id": user_id,
        "nickname": nickname,
        "email": email,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400,  # 1일 (7일에서 단축)
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    sig = hmac.new(SECRET_KEY.encode(), raw, hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(raw).decode() + "." + sig
    return token


def verify_token(token: str) -> Optional[dict]:
    """HMAC-SHA256 토큰 검증 및 payload 반환."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        raw = base64.urlsafe_b64decode(parts[0])
        expected_sig = hmac.new(SECRET_KEY.encode(), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, parts[1]):
            return None
        payload = json.loads(raw)
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def _validate_origin(origin: str) -> str:
    """origin을 CORS_ORIGINS 화이트리스트와 대조 (Open Redirect 방지)."""
    if not origin:
        return ""
    allowed = {o.strip().rstrip("/") for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",")}
    return origin.rstrip("/") if origin.rstrip("/") in allowed else ""


def get_kakao_login_url(origin: str = "") -> str:
    """카카오 로그인 페이지 URL 생성.

    Args:
        origin: 프론트엔드의 현재 origin (예: "https://lifesync-ai.vercel.app")
                빈 문자열이면 .env의 KAKAO_REDIRECT_URI 사용.
    """
    client_id = os.getenv("KAKAO_CLIENT_ID", "")
    safe_origin = _validate_origin(origin)
    if safe_origin:
        redirect_uri = f"{safe_origin}/auth/kakao/callback"
    else:
        redirect_uri = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:5173/auth/kakao/callback")
    return (
        f"{KAKAO_AUTH_URL}/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
    )


async def exchange_code(code: str, origin: str = "") -> dict:
    """인가 코드 → 액세스 토큰 교환.

    Args:
        code: 카카오에서 받은 인가 코드.
        origin: 프론트엔드 origin (redirect_uri와 일치해야 함).
    """
    client_id = os.getenv("KAKAO_CLIENT_ID", "")
    if origin:
        redirect_uri = f"{origin.rstrip('/')}/auth/kakao/callback"
    else:
        redirect_uri = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:5173/auth/kakao/callback")

    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code": code,
    }
    client_secret = os.getenv("KAKAO_CLIENT_SECRET", "")
    if client_secret:
        data["client_secret"] = client_secret

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{KAKAO_AUTH_URL}/oauth/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return resp.json()


async def get_kakao_user(access_token: str) -> dict:
    """카카오 사용자 프로필 조회."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{KAKAO_API_URL}/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = resp.json()

    kakao_id = str(data.get("id", ""))
    profile = data.get("kakao_account", {}).get("profile", {})
    email = data.get("kakao_account", {}).get("email", "")

    return {
        "kakao_id": kakao_id,
        "nickname": profile.get("nickname", "사용자"),
        "profile_image": profile.get("profile_image_url", ""),
        "email": email,
    }


async def kakao_login(code: str, origin: str = "") -> dict:
    """전체 로그인 플로우: 코드 → 토큰 → 사용자 정보 → JWT."""
    token_data = await exchange_code(code, origin)
    access_token = token_data.get("access_token")
    if not access_token:
        raise ValueError(f"카카오 토큰 교환 실패: {token_data}")

    user_info = await get_kakao_user(access_token)
    jwt_token = _make_token(
        user_id=f"kakao_{user_info['kakao_id']}",
        nickname=user_info["nickname"],
        email=user_info.get("email", ""),
    )

    return {
        "token": jwt_token,
        "user": {
            "id": f"kakao_{user_info['kakao_id']}",
            "nickname": user_info["nickname"],
            "profile_image": user_info["profile_image"],
            "email": user_info.get("email", ""),
            "provider": "kakao",
        },
    }
