"""Cached access to the game configuration (10s TTL)."""

import time
from typing import Optional

from database import db
from models import GameConfig

_config_cache: Optional[GameConfig] = None
_config_cache_time: float = 0.0
_CONFIG_CACHE_TTL: float = 10.0  # seconds


async def init_game_config() -> GameConfig:
    """Insert default config if none exists."""
    existing = await db.game_config.find_one()
    if not existing:
        config = GameConfig()
        await db.game_config.insert_one(config.dict())
        return config
    return GameConfig(**existing)


async def get_game_config() -> GameConfig:
    """Get current game configuration – cached for 10 seconds."""
    global _config_cache, _config_cache_time
    now = time.monotonic()
    if _config_cache is not None and (now - _config_cache_time) < _CONFIG_CACHE_TTL:
        return _config_cache
    config_doc = await db.game_config.find_one()
    if not config_doc:
        config = await init_game_config()
    else:
        config = GameConfig(**config_doc)
    _config_cache = config
    _config_cache_time = now
    return config


def invalidate_config_cache() -> None:
    global _config_cache
    _config_cache = None
