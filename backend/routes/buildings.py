from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException

from app_config import utc_now
from auth_deps import get_current_user
from database import db
from game_constants import BUILDING_TYPES
from models import UpgradeBuilding, User, UserBuildings
from services.buildings import (calculate_building_cost,
                                calculate_building_time, get_building_bonus,
                                init_user_buildings)
from services.config_cache import get_game_config

router = APIRouter(prefix="/game", tags=["buildings"])


@router.get("/buildings")
async def get_user_buildings(current_user: User = Depends(get_current_user)):
    buildings_data = await db.user_buildings.find_one({"user_id": current_user.id})
    if not buildings_data:
        user_buildings = await init_user_buildings(current_user.id)
    else:
        user_buildings = UserBuildings(**buildings_data)

    return [
        {
            "building_type": b.building_type,
            "name": BUILDING_TYPES[b.building_type]["name"],
            "description": BUILDING_TYPES[b.building_type]["description"],
            "category": BUILDING_TYPES[b.building_type]["category"],
            "level": b.level,
            "upgrading": b.upgrading,
            "upgrade_end_time": b.upgrade_end_time.isoformat() if b.upgrade_end_time else None,
            "upgrade_cost_metal": calculate_building_cost(b.building_type, b.level),
            "upgrade_time_ticks": calculate_building_time(b.building_type, b.level),
            "current_bonus": get_building_bonus(b.building_type, b.level),
        }
        for b in user_buildings.buildings
    ]


@router.post("/buildings/upgrade")
async def upgrade_building(upgrade_data: UpgradeBuilding, current_user: User = Depends(get_current_user)):
    if upgrade_data.building_type not in BUILDING_TYPES:
        raise HTTPException(status_code=400, detail="Invalid building type")

    buildings_data = await db.user_buildings.find_one({"user_id": current_user.id})
    if not buildings_data:
        user_buildings = await init_user_buildings(current_user.id)
    else:
        user_buildings = UserBuildings(**buildings_data)

    target_building = None
    building_index = -1
    for i, b in enumerate(user_buildings.buildings):
        if b.building_type == upgrade_data.building_type:
            target_building, building_index = b, i
            break
    if not target_building:
        raise HTTPException(status_code=404, detail="Building not found")
    if target_building.upgrading:
        raise HTTPException(status_code=400, detail="Dieses Gebäude wird bereits ausgebaut")

    upgrade_cost = calculate_building_cost(upgrade_data.building_type, target_building.level)

    user_planets = await db.planets.find({"owner_id": current_user.id}).to_list(100)
    total_metal = sum(planet["resources"]["metal"] for planet in user_planets)
    if total_metal < upgrade_cost:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient metal. Need {upgrade_cost}, have {total_metal}",
        )

    remaining_cost = upgrade_cost
    for planet in user_planets:
        if remaining_cost <= 0:
            break
        planet_metal = planet["resources"]["metal"]
        if planet_metal > 0:
            deduction = min(planet_metal, remaining_cost)
            await db.planets.update_one(
                {"id": planet["id"]},
                {"$inc": {"resources.metal": -deduction}},
            )
            remaining_cost -= deduction

    config = await get_game_config()
    upgrade_time_ticks = calculate_building_time(upgrade_data.building_type, target_building.level)
    upgrade_time_seconds = upgrade_time_ticks * config.tick_duration
    upgrade_start = utc_now()
    upgrade_end = upgrade_start + timedelta(seconds=upgrade_time_seconds)

    user_buildings.buildings[building_index].upgrading = True
    user_buildings.buildings[building_index].upgrade_start_time = upgrade_start
    user_buildings.buildings[building_index].upgrade_end_time = upgrade_end

    await db.user_buildings.update_one(
        {"user_id": current_user.id},
        {"$set": {"buildings": [b.dict() for b in user_buildings.buildings]}},
    )
    return {
        "message": f"Upgrade started for {BUILDING_TYPES[upgrade_data.building_type]['name']}",
        "cost": upgrade_cost,
        "completion_time": upgrade_end.isoformat(),
        "duration_ticks": upgrade_time_ticks,
    }


@router.get("/building-types")
async def get_building_types():
    return BUILDING_TYPES
