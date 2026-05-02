import asyncio


async def ensure_indexes(db):
    """Create all MongoDB indexes in parallel."""
    await asyncio.gather(
        db.users.create_index("id", unique=True),
        db.users.create_index("username", unique=True),
        db.users.create_index("email"),
        db.planets.create_index("id", unique=True),
        db.planets.create_index("owner_id"),
        db.planets.create_index([("position.x", 1), ("position.y", 1)]),
        db.fleets.create_index("id", unique=True),
        db.fleets.create_index("user_id"),
        db.fleets.create_index([("position.x", 1), ("position.y", 1)]),
        db.fleets.create_index("movement_end_time"),
        db.ship_designs.create_index("id", unique=True),
        db.ship_designs.create_index("user_id"),
        db.user_buildings.create_index("user_id", unique=True),
        db.user_research.create_index("user_id", unique=True),
        db.spaceport_ships.create_index("user_id"),
        db.invite_codes.create_index("code", unique=True),
        db.battle_reports.create_index([("attacker_user_id", 1), ("created_at", -1)]),
        db.battle_reports.create_index([("defender_user_id", 1), ("created_at", -1)]),
    )
    # Cleanup: admin_password lives in env, never in DB
    await db.game_config.update_many({}, {"$unset": {"admin_password": ""}})
