import hashlib

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import UserRepository
from app.schemas.auth import LoginRequest
from app.services.token_service import create_token, verify_token

_security = HTTPBearer(auto_error=False)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class AuthService:
    @staticmethod
    def _serialize_user(user) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "role": user.role,
            "school_name": user.school_name,
            "avatar_url": user.avatar_url,
        }

    @staticmethod
    def login(db: Session, payload: LoginRequest) -> dict:
        user = UserRepository.get_by_username(db, payload.username)
        if not user or user.password_hash != _hash_password(payload.password):
            raise HTTPException(status_code=401, detail="username or password invalid")

        token = create_token(user.id, user.role)
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 86400,
            "user": AuthService._serialize_user(user),
        }

    @staticmethod
    def current_user(db: Session, authorization: str | None = None) -> dict:
        """解析 token 并返回用户信息（兼容旧版 dev-token 和新版签名 token）。无 token 时抛 401。"""
        user_id = None
        if authorization:
            token = authorization.replace("Bearer ", "").strip()

            # 新版：签名 token
            payload = verify_token(token)
            if payload:
                user_id = payload["user_id"]
            # 旧版兼容：dev-token-{user_id}
            elif token.startswith("dev-token-"):
                try:
                    user_id = int(token.removeprefix("dev-token-"))
                except ValueError:
                    raise HTTPException(status_code=401, detail="invalid token")
            else:
                raise HTTPException(status_code=401, detail="invalid token")
        else:
            raise HTTPException(status_code=401, detail="缺少 Authorization 请求头，请先登录")

        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="user not found")
        return AuthService._serialize_user(user)


# ─── FastAPI 依赖注入 ──────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
    db: Session = Depends(get_db),
) -> dict:
    """从请求头中解析 Bearer token，返回当前用户信息"""
    token = credentials.credentials if credentials else None
    return AuthService.current_user(db, token)


def require_role(roles: list[str]):
    """角色校验依赖工厂：require_role(["teacher"])"""
    def _check(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in roles:
            raise HTTPException(status_code=403, detail=f"需要 {roles} 角色，当前为 {current_user['role']}")
        return current_user
    return _check
