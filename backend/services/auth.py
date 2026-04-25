import hashlib
import hmac
import urllib.parse
from datetime import datetime, timedelta, timezone

from jose import jwt

from config import settings


def validate_init_data(init_data: str) -> dict | None:
    try:
        parsed = dict(urllib.parse.parse_qsl(init_data))
    except Exception:
        return None

    hash_val = parsed.pop("hash", None)
    if not hash_val:
        return None

    check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

    secret_key = hmac.new(
        b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256
    ).digest()

    computed = hmac.new(
        secret_key, check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed, hash_val):
        return None

    auth_date = int(parsed.get("auth_date", 0))
    if datetime.now(timezone.utc).timestamp() - auth_date > 86400:
        return None

    return parsed


def parse_user_data(user_data: str) -> dict:
    import json
    return json.loads(user_data)


def create_jwt(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_jwt(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return int(payload.get("sub"))
    except Exception:
        return None