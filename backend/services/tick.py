"""Tick processing engine: runs every config.tick_duration seconds."""

import asyncio
import logging
from datetime import timedelta
from typing import Optional

from app_config import utc_now
from database import db
from models import Fleet, Planet, ShipDesign, UserBuildings, UserResearch
from services.combat import process_combat
from services.config_cache import get_game_config
from services.universe import init_game_state

logger = logging.getLogger(__name__)


async def _process_completed_building_upgrades(current_time):
    all_buildings = await db.user_buildings.find({}).to_list(1000)
    for buildings_data in all_buildings:
        user_buildings = UserBuildings(**buildings_data)
        updated = False
        for i, building in enumerate(user_buildings.buildings):
            if building.upgrading and building.upgrade_end_time and building.upgrade_end_time <= current_time:
                user_buildings.buildings[i].level += 1
                user_buildings.buildings[i].upgrading = False
                user_buildings.buildings[i].upgrade_start_time = None
                user_buildings.buildings[i].upgrade_end_time = None
                updated = True
                await db.users.update_one(
                    {"id": user_buildings.user_id},
                    {"$inc": {"points": 500}},
                )
        if updated:
            await db.user_buildings.update_one(
                {"user_id": user_buildings.user_id},
                {"$set": {"buildings": [b.dict() for b in user_buildings.buildings]}},
            )


async def _apply_resource_building_bonuses():
    all_users = await db.users.find({}).to_list(1000)
    for user_data in all_users:
        user_id = user_data["id"]
        user_buildings_data = await db.user_buildings.find_one({"user_id": user_id})
        if not user_buildings_data:
            continue
        user_buildings = UserBuildings(**user_buildings_data)

        food_bonus = metal_bonus = hydrogen_bonus = 0
        for building in user_buildings.buildings:
            if building.building_type == "plantage":
                food_bonus = building.level * 5
            elif building.building_type == "erzmine":
                metal_bonus = building.level * 5
            elif building.building_type == "elektrolysator":
                hydrogen_bonus = building.level * 5

        if food_bonus or metal_bonus or hydrogen_bonus:
            user_planets = await db.planets.find({"owner_id": user_id}).to_list(100)
            for planet in user_planets:
                await db.planets.update_one(
                    {"id": planet["id"]},
                    {"$inc": {
                        "resources.food": food_bonus,
                        "resources.metal": metal_bonus,
                        "resources.hydrogen": hydrogen_bonus,
                    }},
                )


async def _process_completed_research(current_time):
    all_research = await db.user_research.find({}).to_list(1000)
    for research_data in all_research:
        research_obj = UserResearch(**research_data)
        updated = False
        for i, level in enumerate(research_obj.research_levels):
            if level.researching and level.research_end_time and level.research_end_time <= current_time:
                research_obj.research_levels[i].level += 1
                research_obj.research_levels[i].researching = False
                research_obj.research_levels[i].research_start_time = None
                research_obj.research_levels[i].research_end_time = None
                updated = True
                await db.users.update_one(
                    {"id": research_obj.user_id},
                    {"$inc": {"points": 1000}},
                )
        if updated:
            await db.user_research.update_one(
                {"user_id": research_obj.user_id},
                {"$set": research_obj.dict()},
            )


async def _land_arriving_fleets(current_time):
    fleets = await db.fleets.find({"movement_end_time": {"$lte": current_time}}).to_list(1000)
    for fleet_data in fleets:
        fleet = Fleet(**fleet_data)
        if fleet.target_position:
            await db.fleets.update_one(
                {"id": fleet.id},
                {"$set": {
                    "position": fleet.target_position.dict(),
                    "target_position": None,
                    "movement_start_time": None,
                    "movement_end_time": None,
                }},
            )


async def _resolve_combat():
    game_state = await init_game_state()
    all_fleets = await db.fleets.find({"movement_end_time": None}).to_list(1000)

    fleets_by_position: dict = {}
    for fleet_data in all_fleets:
        fleet = Fleet(**fleet_data)
        pos_key = f"{fleet.position.x},{fleet.position.y}"
        fleets_by_position.setdefault(pos_key, []).append(fleet)

    processed = set()
    for pos_key, position_fleets in fleets_by_position.items():
        if len(position_fleets) < 2:
            continue
        for i, fleet1 in enumerate(position_fleets):
            if fleet1.id in processed:
                continue
            for fleet2 in position_fleets[i + 1:]:
                if fleet2.id in processed:
                    continue
                if fleet1.user_id == fleet2.user_id:
                    continue
                if fleet1.stance != "aggressive" and fleet2.stance != "aggressive":
                    continue
                attacker, defender = (fleet1, fleet2) if fleet1.stance == "aggressive" else (fleet2, fleet1)
                report = await process_combat(attacker, defender, game_state)
                if report:
                    processed.add(fleet1.id)
                    processed.add(fleet2.id)
                    logger.info(f"Combat at ({pos_key}): {attacker.name} vs {defender.name} - Winner: {report.winner}")


async def _process_mining(config):
    stationary_fleets = await db.fleets.find({"movement_end_time": None}).to_list(1000)
    for fleet_data in stationary_fleets:
        fleet = Fleet(**fleet_data)

        planet = await db.planets.find_one({
            "position.x": fleet.position.x,
            "position.y": fleet.position.y,
        })
        if not planet:
            continue
        planet_obj = Planet(**planet)

        total_mining_capacity = 0
        for ship_group in fleet.ships:
            design = await db.ship_designs.find_one({"id": ship_group["design_id"]})
            if design:
                mc = ShipDesign(**design).calculated_stats.get("mining_capacity", 0)
                total_mining_capacity += mc * ship_group["quantity"]

        if total_mining_capacity <= 0:
            continue

        actual_mining = int(total_mining_capacity * config.mining_efficiency)
        total_resources = (planet_obj.resources.food + planet_obj.resources.metal +
                           planet_obj.resources.hydrogen)
        if total_resources <= 0:
            continue

        food_ratio = planet_obj.resources.food / total_resources
        metal_ratio = planet_obj.resources.metal / total_resources
        hydrogen_ratio = planet_obj.resources.hydrogen / total_resources

        food_mined = min(int(actual_mining * food_ratio), planet_obj.resources.food)
        metal_mined = min(int(actual_mining * metal_ratio), planet_obj.resources.metal)
        hydrogen_mined = min(int(actual_mining * hydrogen_ratio), planet_obj.resources.hydrogen)

        await db.planets.update_one(
            {"id": planet_obj.id},
            {"$inc": {
                "resources.food": -food_mined,
                "resources.metal": -metal_mined,
                "resources.hydrogen": -hydrogen_mined,
            }},
        )

        miner_user = await db.users.find_one({"id": fleet.user_id})
        if miner_user:
            spaceport_pos = miner_user.get("spaceport_position", {})
            home_planet = await db.planets.find_one({
                "owner_id": fleet.user_id,
                "position.x": spaceport_pos.get("x", -1),
                "position.y": spaceport_pos.get("y", -1),
            })
            if not home_planet:
                home_planet = await db.planets.find_one({"owner_id": fleet.user_id})

            if home_planet and home_planet["id"] != planet_obj.id:
                await db.planets.update_one(
                    {"id": home_planet["id"]},
                    {"$inc": {
                        "resources.food": food_mined,
                        "resources.metal": metal_mined,
                        "resources.hydrogen": hydrogen_mined,
                    }},
                )

        resources_value = food_mined + metal_mined + hydrogen_mined
        if resources_value > 0:
            await db.users.update_one(
                {"id": fleet.user_id},
                {"$inc": {"points": resources_value // 1000}},
            )


async def process_tick() -> None:
    """Process a single game tick."""
    config = await get_game_config()
    current_time = utc_now()

    await _process_completed_building_upgrades(current_time)
    await _apply_resource_building_bonuses()
    await _process_completed_research(current_time)
    await _land_arriving_fleets(current_time)
    await _resolve_combat()
    await _process_mining(config)

    next_tick_time = utc_now() + timedelta(seconds=config.tick_duration)
    await db.game_state.update_one(
        {},
        {"$inc": {"current_tick": 1},
         "$set": {"last_tick_time": utc_now(), "next_tick_time": next_tick_time}},
    )


# --- Automatic tick scheduler ---
_automatic_tick_task: Optional[asyncio.Task] = None


async def _automatic_tick_loop():
    while True:
        try:
            config = await get_game_config()
            await asyncio.sleep(config.tick_duration)
            await process_tick()
            logger.info(f"[TICK] Automatic tick processed at {utc_now()}")
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error(f"[TICK] Automatic tick failed: {exc}")
            await asyncio.sleep(60)


async def start_automatic_tick_system() -> None:
    global _automatic_tick_task
    if _automatic_tick_task is None or _automatic_tick_task.done():
        _automatic_tick_task = asyncio.create_task(_automatic_tick_loop())
        logger.info("[TICK] Automatic tick system started")


async def stop_automatic_tick_system() -> None:
    global _automatic_tick_task
    if _automatic_tick_task:
        _automatic_tick_task.cancel()
        _automatic_tick_task = None
        logger.info("[TICK] Automatic tick system stopped")
