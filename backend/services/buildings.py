"""Building helpers: cost/time formulas, bonuses, initialization."""

from database import db
from game_constants import BUILDING_TYPES
from models import BuildingLevel, UserBuildings


async def init_user_buildings(user_id: str) -> UserBuildings:
    """Initialize all buildings at level 0 for a new user."""
    buildings = [BuildingLevel(building_type=t, level=0) for t in BUILDING_TYPES.keys()]
    user_buildings = UserBuildings(user_id=user_id, buildings=buildings)
    await db.user_buildings.insert_one(user_buildings.dict())
    return user_buildings


def calculate_building_cost(building_type: str, current_level: int) -> int:
    building = BUILDING_TYPES[building_type]
    base_cost = building["base_cost"]
    increase = building["cost_increase_percent"] / 100
    return int(base_cost * ((1 + increase) ** current_level))


def calculate_building_time(building_type: str, current_level: int) -> int:
    building = BUILDING_TYPES[building_type]
    base_time = building["base_build_time_ticks"]
    increase = building["build_time_increase_percent"] / 100
    return int(base_time * ((1 + increase) ** current_level))


def get_building_bonus(building_type: str, level: int) -> dict:
    building = BUILDING_TYPES[building_type]
    bonus = {"type": building_type, "level": level}

    if "resource_bonus_per_level" in building:
        bonus["resource_per_tick"] = building["resource_bonus_per_level"] * level
        bonus["resource_type"] = building["resource_type"]

    if "prototype_slots_per_level" in building:
        bonus["prototype_slots"] = building["prototype_slots_per_level"] * level

    if "fleet_slots_per_level" in building:
        bonus["fleet_slots"] = building["fleet_slots_per_level"] * level

    if "research_time_reduction_percent" in building:
        reduction = 1 - ((1 - building["research_time_reduction_percent"] / 100) ** level)
        bonus["research_time_reduction"] = round(reduction * 100, 1)

    return bonus
