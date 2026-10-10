import hashlib
import hmac
import os
import secrets

import jwt
from fastapi import Cookie, Depends, HTTPException

PRODUCTION = os.environ.get("IMVEST_ENV") == "production" or bool(os.environ.get("VERCEL"))
SECRET = os.environ.get("IMVEST_JWT_SECRET", "dev-only-change-me-please-use-32-bytes-min")
if PRODUCTION and SECRET.startswith("dev-only"):
    # Satu variabel cukup: turunkan secret JWT dari IMVEST_SEED_PASSWORD (tak pernah disimpan/di-log).
    _seed = os.environ.get("IMVEST_SEED_PASSWORD")
    if not _seed:
        raise RuntimeError("Set IMVEST_SEED_PASSWORD (atau IMVEST_JWT_SECRET >=32 byte) di produksi")
    SECRET = hmac.new(b"imvest-jwt-v1", _seed.encode(), hashlib.sha256).hexdigest()
RANK = {"INVESTOR": 0, "RM": 1, "ANALYST": 2, "ADMIN": 3}


def hash_password(pw: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    return salt.hex() + ":" + hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1).hex()


def verify_password(pw: str, stored: str) -> bool:
    salt_hex, digest = stored.split(":")
    return hmac.compare_digest(hash_password(pw, bytes.fromhex(salt_hex)).split(":")[1], digest)


def make_token(user_id: int, role: str) -> str:
    return jwt.encode({"sub": str(user_id), "role": role}, SECRET, algorithm="HS256")


def current_user(session: str | None = Cookie(default=None)) -> dict:
    if not session:
        raise HTTPException(401, {"code": "UNAUTHENTICATED", "message": "login required"})
    try:
        c = jwt.decode(session, SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, {"code": "UNAUTHENTICATED", "message": "invalid session"})
    return {"id": int(c["sub"]), "role": c["role"]}


def require(min_role: str):
    def dep(user: dict = Depends(current_user)) -> dict:
        if RANK[user["role"]] < RANK[min_role]:
            raise HTTPException(403, {"code": "FORBIDDEN", "message": f"{min_role} required"})
        return user
    return dep
