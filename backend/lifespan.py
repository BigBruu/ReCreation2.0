"""FastAPI lifespan – replaces deprecated on_event hooks."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import client, db
from indexes import ensure_indexes
from services.config_cache import init_game_config
from services.tick import (start_automatic_tick_system,
                           stop_automatic_tick_system)
from services.universe import generate_universe, init_game_state

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Startup and shutdown logic for the game server."""
    await ensure_indexes(db)
    logger.info("MongoDB indexes created")

    await init_game_state()
    logger.info("TheCreation Authentic Game Engine started!")

    planet_count = await db.planets.count_documents({})
    logger.info(f"Found {planet_count} planets in database")
    if planet_count == 0:
        logger.info("Generating universe with planets...")
        await generate_universe()
        final_count = await db.planets.count_documents({})
        logger.info(f"Generated {final_count} planets")

    config = await init_game_config()
    logger.info(
        f"Game config: {config.max_players} max players, "
        f"{config.universe_size}x{config.universe_size} universe"
    )

    await start_automatic_tick_system()
    logger.info(f"Automatic tick system started with {config.tick_duration}s interval")

    yield

    await stop_automatic_tick_system()
    client.close()
    logger.info("TheCreation server shutdown complete")
