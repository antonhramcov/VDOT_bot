from __future__ import annotations

import asyncpg
from aiogram.types import User

from texts import DEFAULT_LANGUAGE, normalize_language


CREATE_BOT_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS bot_users (
    telegram_user_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    language_code TEXT NOT NULL DEFAULT 'en',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


CREATE_USER_VDOT_TABLE = """
CREATE TABLE IF NOT EXISTS user_vdots (
    telegram_user_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    last_vdot DOUBLE PRECISION NOT NULL,
    distance_km DOUBLE PRECISION NOT NULL,
    total_seconds INTEGER NOT NULL,
    race_pace_seconds INTEGER NOT NULL,
    source_text TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


UPSERT_BOT_USER = """
INSERT INTO bot_users (
    telegram_user_id,
    username,
    first_name,
    last_name,
    language_code,
    updated_at
)
VALUES ($1, $2, $3, $4, $5, NOW())
ON CONFLICT (telegram_user_id)
DO UPDATE SET
    username = EXCLUDED.username,
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    updated_at = NOW()
RETURNING language_code;
"""


UPDATE_USER_LANGUAGE = """
INSERT INTO bot_users (
    telegram_user_id,
    username,
    first_name,
    last_name,
    language_code,
    updated_at
)
VALUES ($1, $2, $3, $4, $5, NOW())
ON CONFLICT (telegram_user_id)
DO UPDATE SET
    username = EXCLUDED.username,
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    language_code = EXCLUDED.language_code,
    updated_at = NOW()
RETURNING language_code;
"""


SELECT_USER_VDOT = """
SELECT
    telegram_user_id,
    username,
    first_name,
    last_name,
    last_vdot,
    distance_km,
    total_seconds,
    race_pace_seconds,
    source_text,
    updated_at
FROM user_vdots
WHERE telegram_user_id = $1;
"""


UPSERT_USER_VDOT = """
INSERT INTO user_vdots (
    telegram_user_id,
    username,
    first_name,
    last_name,
    last_vdot,
    distance_km,
    total_seconds,
    race_pace_seconds,
    source_text,
    updated_at
)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
ON CONFLICT (telegram_user_id)
DO UPDATE SET
    username = EXCLUDED.username,
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    last_vdot = EXCLUDED.last_vdot,
    distance_km = EXCLUDED.distance_km,
    total_seconds = EXCLUDED.total_seconds,
    race_pace_seconds = EXCLUDED.race_pace_seconds,
    source_text = EXCLUDED.source_text,
    updated_at = NOW();
"""


async def create_pool(database_url: str) -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=database_url, min_size=1, max_size=5)


async def init_db(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as connection:
        await connection.execute(CREATE_BOT_USERS_TABLE)
        await connection.execute(CREATE_USER_VDOT_TABLE)


async def ensure_user(pool: asyncpg.Pool, user: User) -> str:
    language_code = await pool.fetchval(
        UPSERT_BOT_USER,
        user.id,
        user.username,
        user.first_name,
        user.last_name,
        DEFAULT_LANGUAGE,
    )
    return normalize_language(language_code)


async def set_user_language(
    pool: asyncpg.Pool,
    user: User,
    language_code: str,
) -> str:
    saved_language = await pool.fetchval(
        UPDATE_USER_LANGUAGE,
        user.id,
        user.username,
        user.first_name,
        user.last_name,
        normalize_language(language_code),
    )
    return normalize_language(saved_language)


async def get_latest_vdot(
    pool: asyncpg.Pool,
    telegram_user_id: int,
) -> asyncpg.Record | None:
    return await pool.fetchrow(SELECT_USER_VDOT, telegram_user_id)


async def save_latest_vdot(
    pool: asyncpg.Pool,
    user: User,
    vdot: float,
    distance_km: float,
    total_seconds: int,
    race_pace_seconds: int,
    source_text: str,
) -> None:
    await pool.execute(
        UPSERT_USER_VDOT,
        user.id,
        user.username,
        user.first_name,
        user.last_name,
        round(vdot, 2),
        distance_km,
        total_seconds,
        race_pace_seconds,
        source_text,
    )
