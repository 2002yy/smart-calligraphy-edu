"""Tests for the auth service layer.

Covers login validation, token parsing, and error handling without
going through the HTTP router.
"""

import pytest
from fastapi import HTTPException

from app.schemas.auth import LoginRequest
from app.services.auth_service import AuthService


class TestLogin:
    def test_success_with_valid_credentials(self, db_session, teacher_user):
        result = AuthService.login(db_session, LoginRequest(username="teacher01", password="test_pass"))
        from app.services.token_service import verify_token
        payload = verify_token(result["access_token"])
        assert payload is not None, "token should be valid signed token"
        assert payload["user_id"] == 1
        assert payload["role"] == "teacher"
        assert result["token_type"] == "bearer"
        assert result["expires_in"] == 86400
        assert result["user"]["username"] == "teacher01"
        assert result["user"]["role"] == "teacher"

    def test_fails_with_wrong_password(self, db_session, teacher_user):
        with pytest.raises(HTTPException) as exc:
            AuthService.login(db_session, LoginRequest(username="teacher01", password="wrong_pass"))
        assert exc.value.status_code == 401

    def test_fails_with_unknown_username(self, db_session):
        with pytest.raises(HTTPException) as exc:
            AuthService.login(db_session, LoginRequest(username="nobody", password="anything"))
        assert exc.value.status_code == 401


class TestCurrentUser:
    def test_returns_user_for_valid_token(self, db_session, teacher_user):
        result = AuthService.current_user(db_session, "Bearer dev-token-1")
        assert result["username"] == "teacher01"
        assert result["name"] == "刘老师"
        assert result["role"] == "teacher"

    def test_returns_user_for_teacher_id_2(self, db_session, teacher_user):
        from app.models.user import User
        user = User(username="teacher02", password_hash="p", name="王老师", role="teacher", school_name="四川大学")
        db_session.add(user)
        db_session.commit()

        result = AuthService.current_user(db_session, "Bearer dev-token-2")
        assert result["username"] == "teacher02"

    def test_fails_with_malformed_token(self, db_session):
        with pytest.raises(HTTPException) as exc:
            AuthService.current_user(db_session, "Bearer invalid-token-abc")
        assert exc.value.status_code == 401

    def test_accepts_token_without_bearer_prefix(self, db_session, teacher_user):
        """current_user accepts "dev-token-1" without "Bearer " prefix."""
        result = AuthService.current_user(db_session, "dev-token-1")
        assert result["id"] == 1

    def test_fails_with_nonexistent_user(self, db_session):
        with pytest.raises(HTTPException) as exc:
            AuthService.current_user(db_session, "Bearer dev-token-999")
        assert exc.value.status_code == 404

    def test_defaults_to_user_1_without_header(self, db_session):
        """无 token 时应抛出 401。"""
        with pytest.raises(HTTPException) as exc:
            AuthService.current_user(db_session, authorization=None)
        assert exc.value.status_code == 401

    def test_defaults_to_user_1_with_empty_string(self, db_session):
        """空 token 时应抛出 401。"""
        with pytest.raises(HTTPException) as exc:
            AuthService.current_user(db_session, authorization="")
        assert exc.value.status_code == 401
