"""Universe generation and game state initialization."""

import random
import uuid
from typing import Optional

from app_config import utc_now
from database import db
from game_constants import PLANET_TYPE_TO_NAME, PLANET_TYPES
from models import GameState
from services.config_cache import get_game_config, init_game_config


async def generate_universe(
    explicit_planet_count: Optional[int] = None,
    explicit_resource_amount: Optional[int] = None,
) -> None:
    """Generate planets across the universe.

    When called from /admin/new-round the explicit values override the config defaults.
    """
    existing_planets = await db.planets.count_documents({})
    if existing_planets > 0:
        return

    config = await get_game_config()
    universe_size = config.universe_size
    min_resources = explicit_resource_amount or config.min_planet_resources
    max_resources = explicit_resource_amount or config.max_planet_resources

    planet_count = explicit_planet_count or int((universe_size * universe_size) * 0.08)
    planet_count = min(planet_count, universe_size * universe_size)

    occupied: set = set()
    planets_to_create = []

    for _ in range(planet_count):
        x = random.randint(0, universe_size - 1)
        y = random.randint(0, universe_size - 1)
        if (x, y) in occupied:
            continue
        occupied.add((x, y))

        planet_type = random.choice(list(PLANET_TYPES.keys()))
        base_resources = PLANET_TYPES[planet_type]["base_resources"].copy()

        resource_multiplier = random.uniform(min_resources / 50000000, max_resources / 50000000)
        for resource in base_resources:
            base_resources[resource] = int(base_resources[resource] * resource_multiplier)

        planets_to_create.append({
            "id": str(uuid.uuid4()),
            "position": {"x": x, "y": y},
            "planet_type": planet_type,
            "name": PLANET_TYPE_TO_NAME[planet_type],
            "resources": base_resources,
            "owner_id": None,
            "owner_username": None,
            "created_at": utc_now(),
        })

    if planets_to_create:
        await db.planets.insert_many(planets_to_create)


async def init_game_state() -> GameState:
    existing_state = await db.game_state.find_one()
    if existing_state:
        return GameState(**existing_state)

    game_state = GameState()
    await db.game_state.insert_one(game_state.dict())
    await generate_universe()
    await init_game_config()
    return game_state
