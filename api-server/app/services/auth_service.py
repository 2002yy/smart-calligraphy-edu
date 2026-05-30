import hashlib

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import UserRepository
from app.schemas.auth import LoginRequest


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class AuthService:
    @staticmethod
    def _build_token(user_id: int) -> str:
        return f"dev-token-{user_id}"

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

        return {
            "access_token": AuthService._build_token(user.id),
            "token_type": "bearer",
            "expires_in": 86400,
            "user": AuthService._serialize_user(user),
        }

    @staticmethod
    def current_user(db: Session, authorization: str | None = None) -> dict:
        user_id = 1
        if authorization:
            token = authorization.replace("Bearer ", "").strip()
            if not token.startswith("dev-token-"):
                raise HTTPException(status_code=401, detail="invalid token")
            try:
                user_id = int(token.removeprefix("dev-token-"))
            except ValueError as exc:
                raise HTTPException(status_code=401, detail="invalid token") from exc

        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="user not found")

        return AuthService._serialize_user(user)
