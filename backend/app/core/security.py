import hashlib
import hmac
import secrets
from dataclasses import dataclass
from enum import StrEnum

from app.core.config import Settings


class Role(StrEnum):
    FREE = "free"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"


ROLE_PERMISSIONS: dict[Role, frozenset[str]] = {
    Role.FREE: frozenset({"inference:invoke", "models:read"}),
    Role.ENTERPRISE: frozenset({"inference:invoke", "models:read", "priority:standard"}),
    Role.ADMIN: frozenset(
        {
            "inference:invoke",
            "models:read",
            "models:write",
            "keys:create",
            "keys:revoke",
            "system:manage",
            "priority:high",
        }
    ),
}


@dataclass(frozen=True, slots=True)
class GeneratedApiKey:
    raw_key: str
    key_hash: str
    prefix: str


def generate_api_key(settings: Settings) -> GeneratedApiKey:
    raw_key = f"ih_{secrets.token_urlsafe(32)}"
    return GeneratedApiKey(
        raw_key=raw_key,
        key_hash=hash_api_key(raw_key, settings),
        prefix=raw_key[:12],
    )


def hash_api_key(raw_key: str, settings: Settings) -> str:
    return hmac.new(
        settings.api_key_pepper.encode("utf-8"),
        raw_key.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def constant_time_equal(left: str, right: str) -> bool:
    return hmac.compare_digest(left, right)


def role_has_permission(role: Role, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS[role]


def default_rpm_for_role(role: Role, settings: Settings) -> int:
    match role:
        case Role.ADMIN:
            return settings.default_admin_rpm
        case Role.ENTERPRISE:
            return settings.default_enterprise_rpm
        case Role.FREE:
            return settings.default_free_rpm

