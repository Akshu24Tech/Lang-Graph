import os
import time
import sqlite3
import bcrypt
import jwt
from fastapi import Header, HTTPException

try:
    import psycopg
except ImportError:
    psycopg = None

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-insecure-secret-change-me-in-production")
ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = 60 * 60 * 24 * 30  # 30 days

DATABASE_URL = os.getenv("DATABASE_URL")
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "local_users.db")


def _get_conn():
    if DATABASE_URL and psycopg:
        try:
            return ("postgres", psycopg.connect(DATABASE_URL, autocommit=True, connect_timeout=3))
        except Exception as e:
            print(f"[INFO] Postgres connection failed ({e}). Falling back to local SQLite auth.")
    return ("sqlite", sqlite3.connect(SQLITE_DB_PATH))


def init_users_table():
    """Idempotent — safe to call on every startup."""
    db_type, conn = _get_conn()
    with conn:
        if db_type == "postgres":
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
            print("[OK] Postgres Users table ready")
        else:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS app_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            print("[OK] SQLite Users table ready (local fallback)")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_user(email: str, password: str) -> str:
    """Returns the new user's stable id, formatted as 'user_<n>'."""
    email = email.lower().strip()
    password_hash = hash_password(password)
    db_type, conn = _get_conn()
    with conn:
        try:
            if db_type == "postgres":
                cur = conn.execute(
                    "INSERT INTO app_users (email, password_hash) VALUES (%s, %s) RETURNING id",
                    (email, password_hash),
                )
                new_id = cur.fetchone()[0]
            else:
                cur = conn.execute(
                    "INSERT INTO app_users (email, password_hash) VALUES (?, ?)",
                    (email, password_hash),
                )
                new_id = cur.lastrowid
            return f"user_{new_id}"
        except Exception as e:
            if "unique" in str(e).lower():
                raise ValueError("An account with this email already exists.")
            raise e


def authenticate_user(email: str, password: str) -> str:
    """Returns the user's stable id if credentials are correct."""
    email = email.lower().strip()
    db_type, conn = _get_conn()
    with conn:
        if db_type == "postgres":
            cur = conn.execute(
                "SELECT id, password_hash FROM app_users WHERE email = %s", (email,)
            )
        else:
            cur = conn.execute(
                "SELECT id, password_hash FROM app_users WHERE email = ?", (email,)
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
