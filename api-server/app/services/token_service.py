"""签名 Token 工具（HMAC-SHA256，零依赖替代 JWT）

Token 格式：base64(json_payload).base64(hmac_signature)
Payload 包含：user_id, role, exp（过期时间戳）
"""

import base64
import hashlib
import hmac
import json
import time

from app.core.config import settings


def _secret() -> bytes:
    return settings.jwt_secret.encode("utf-8")


def create_token(user_id: int, role: str, expires_in: int = 86400) -> str:
    """生成签名 Token，默认 24 小时过期"""
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": int(time.time()) + expires_in,
    }
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=").decode()
    sig = hmac.new(_secret(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_token(token: str) -> dict | None:
    """验证 Token，返回 payload 或 None"""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig = parts

        expected_sig = hmac.new(_secret(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None

        # 补齐 base64 padding
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding

        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None

        return payload
    except Exception:
        return None



def sign_image_path(image_path: str, expires_in: int = 3600) -> str:
    """为图片路径生成签名 token，默认 1 小时过期。"""
    payload = {"path": image_path, "exp": int(time.time()) + expires_in}
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=").decode()
    sig = hmac.new(_secret(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_signed_path(token: str) -> str | None:
    """验证图片签名 token，返回图片路径。"""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig = parts
        expected_sig = hmac.new(_secret(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload.get("path", "")
    except Exception:
        return None
