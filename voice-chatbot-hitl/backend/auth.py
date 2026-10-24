"""
Simple email/password authentication so memory follows a real account,
not a random per-browser ID. Requires DATABASE_URL (Postgres) — same
connection your LTM store already uses.
"""

import os
import time
import bcrypt
import jwt
import psycopg
from fastapi import Header, HTTPException

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-insecure-secret-change-me-in-production")
ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = 60 * 60 * 24 * 30  # 30 days

DATABASE_URL = os.getenv("DATABASE_URL")


def _get_conn():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is required for login/signup — set it to your Postgres connection string."
        )
    return psycopg.connect(DATABASE_URL, autocommit=True)


def init_users_table():
    """Idempotent — safe to call on every startup."""
    if not DATABASE_URL:
        print(" DATABASE_URL not set — signup/login will not work until it's configured.")
        return
    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT now()
            )
            """
        )
    print("Users table ready")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_user(email: str, password: str) -> str:
    """Returns the new user's stable id, formatted as 'user_<n>'."""
    email = email.lower().strip()
    password_hash = hash_password(password)
    with _get_conn() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO app_users (email, password_hash) VALUES (%s, %s) RETURNING id",
                (email, password_hash),
            )
            new_id = cur.fetchone()[0]
            return f"user_{new_id}"
        except psycopg.errors.UniqueViolation:
            raise ValueError("An account with this email already exists.")


def authenticate_user(email: str, password: str) -> str:
    """Returns the user's stable id if credentials are correct."""
    email = email.lower().strip()
    with _get_conn() as conn:
        cur = conn.execute(
            "SELECT id, password_hash FROM app_users WHERE email = %s", (email,)
        )
        row = cur.fetchone()
        if not row or not verify_password(password, row[1]):
            raise ValueError("Invalid email or password.")
        return f"user_{row[0]}"


def create_token(user_id: str) -> str:
    payload = {"user_id": user_id, "exp": time.time() + TOKEN_TTL_SECONDS}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["user_id"]
    except jwt.PyJWTError:
        raise ValueError("Invalid or expired token.")


def get_current_user_id(authorization: str = Header(None)) -> str:
    """FastAPI dependency — extracts and verifies the Bearer token, returns user_id."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    try:
        return decode_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
