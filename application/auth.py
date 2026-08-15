"""
User authentication and account management system.
Supports JWT tokens, password hashing, and role-based access control.
"""

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hash a password using PBKDF2. Returns (hash, salt)."""
    if salt is None:
        salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    hash_hex = hash_obj.hex()
    return hash_hex, salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verify a password against a hash."""
    test_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(test_hash, password_hash)


class User:
    """Represents a user account."""

    def __init__(
        self,
        username: str,
        password_hash: str,
        salt: str,
        role: str = "user",
        created_at: str = None,
        last_login: str = None,
    ):
        self.username = username
        self.password_hash = password_hash
        self.salt = salt
        self.role = role
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.last_login = last_login

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            username=data["username"],
            password_hash=data["password_hash"],
            salt=data["salt"],
            role=data.get("role", "user"),
            created_at=data.get("created_at"),
            last_login=data.get("last_login"),
        )

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "salt": self.salt,
            "role": self.role,
            "created_at": self.created_at,
            "last_login": self.last_login,
        }

    def verify_password(self, password: str) -> bool:
        return verify_password(password, self.password_hash, self.salt)

    def update_last_login(self):
        self.last_login = datetime.now(timezone.utc).isoformat()


class UserStore:
    """Manages user persistence in JSON file."""

    def __init__(self, db_path: str | Path = "data/users.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_default_user()

    def _ensure_default_user(self):
        """Ensure a default admin user exists."""
        if self.db_path.exists():
            return

        # Create default admin user with password 'admin'
        default_user = User("admin", *hash_password("admin"), role="admin")
        users = {"admin": default_user.to_dict()}
        self._save_users(users)
        print("Created default admin user. Change password immediately!")

    def _load_users(self) -> dict:
        if not self.db_path.exists():
            return {}
        try:
            data = json.loads(self.db_path.read_text(encoding="utf-8"))
            return data.get("users", {})
        except Exception:
            return {}

    def _save_users(self, users: dict):
        data = {"users": users}
        self.db_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def get_user(self, username: str) -> Optional[User]:
        users = self._load_users()
        if username not in users:
            return None
        return User.from_dict(users[username])

    def create_user(self, username: str, password: str, role: str = "user") -> User:
        users = self._load_users()
        if username in users:
            raise ValueError(f"User {username} already exists")

        password_hash, salt = hash_password(password)
        user = User(username, password_hash, salt, role)
        users[username] = user.to_dict()
        self._save_users(users)
        return user

    def update_user(self, user: User):
        users = self._load_users()
        users[user.username] = user.to_dict()
        self._save_users(users)

    def delete_user(self, username: str):
        users = self._load_users()
        if username in users:
            del users[username]
            self._save_users(users)

    def list_users(self) -> list[User]:
        users = self._load_users()
        return [User.from_dict(data) for data in users.values()]

    def change_password(self, username: str, new_password: str):
        user = self.get_user(username)
        if not user:
            raise ValueError(f"User {username} not found")
        password_hash, salt = hash_password(new_password)
        user.password_hash = password_hash
        user.salt = salt
        self.update_user(user)


class JWTTokenManager:
    """Manage JWT tokens for authentication."""

    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)

    def create_token(self, username: str, role: str = "user", expires_in_hours: int = 24) -> str:
        """Create a JWT token (simplified, not production-grade)."""
        import base64

        payload = {
            "username": username,
            "role": role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
        }

        # Simplified JWT - in production use PyJWT library
        payload_json = json.dumps(
            {
                "username": payload["username"],
                "role": payload["role"],
                "exp": payload["exp"].isoformat(),
            }
        )
        payload_b64 = base64.b64encode(payload_json.encode()).decode()

        signature = hmac.new(
            self.secret_key.encode(), payload_b64.encode(), "sha256"
        ).hexdigest()

        return f"{payload_b64}.{signature}"

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode a JWT token."""
        import base64

        try:
            payload_b64, signature = token.split(".")
            expected_sig = hmac.new(
                self.secret_key.encode(), payload_b64.encode(), "sha256"
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_sig):
                return None

            payload_json = base64.b64decode(payload_b64).decode()
            payload = json.loads(payload_json)

            # Check expiration
            exp = datetime.fromisoformat(payload["exp"])
            if exp < datetime.now(timezone.utc):
                return None

            return payload
        except Exception:
            return None


class AuthenticationManager:
    """Coordinate user authentication and session management."""

    def __init__(self, user_store: UserStore = None, jwt_secret: str = None):
        self.user_store = user_store or UserStore()
        self.jwt_manager = JWTTokenManager(jwt_secret)

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate a user and return a JWT token."""
        user = self.user_store.get_user(username)
        if not user:
            return None

        if not user.verify_password(password):
            return None

        user.update_last_login()
        self.user_store.update_user(user)

        token = self.jwt_manager.create_token(username, user.role)
        return token

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify a token and return the payload."""
        return self.jwt_manager.verify_token(token)

    def create_user(self, username: str, password: str, admin_only: bool = False) -> User:
        """Create a new user (admin only by default)."""
        role = "admin" if admin_only else "user"
        return self.user_store.create_user(username, password, role)

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change a user's password."""
        if not self.authenticate(username, old_password):
            return False
        self.user_store.change_password(username, new_password)
        return True
