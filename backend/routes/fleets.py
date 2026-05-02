from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app_config import utc_now
from auth_deps import get_current_user
from database import db
from game_constants import MOVEMENT_POINTS_NORMAL
from models import (CreateFleetFromSpaceport, Fleet, MoveFleet, Planet,
                    SetFleetStance, ShipDesign, SpaceportShips, User,
                    UserBuildings)
from services.config_cache import get_game_config

router = APIRouter(prefix="/game", tags=["fleets"])


@router.post("/create-fleet")
async def create_fleet_from_spaceport(fleet_data: CreateFleetFromSpaceport, current_user: User = Depends(get_current_user)):
    user_buildings_data = await db.user_buildings.find_one({"user_id": current_user.id})
    raumhafen_level = 0
    if user_buildings_data:
        for building in UserBuildings(**user_buildings_data).buildings:
            if building.building_type == "raumhafen":
                raumhafen_level = building.level
                break

    max_fleets = raumhafen_level
    current_fleets = await db.fleets.count_documents({"user_id": current_user.id})
    if current_fleets >= max_fleets:
        raise HTTPException(
            status_code=400,
            detail=f"Flotten-Limit erreicht! Raumhafen Level {raumhafen_level} erlaubt nur {max_fleets} Flotten. Bauen Sie den Raumhafen aus.",
        )

    planet = await db.planets.find_one({"id": fleet_data.planet_id, "owner_id": current_user.id})
    if not planet:
        raise HTTPException(status_code=404, detail="Planet not found or not owned")

    planet_obj = Planet(**planet)
    fleet_ships = []
    slowest_speed = 999999

    for ship_request in fleet_data.ships:
        design_id = ship_request["design_id"]
        requested_quantity = ship_request["quantity"]

        spaceport_ship = await db.spaceport_ships.find_one({
            "user_id": current_user.id,
            "planet_id": fleet_data.planet_id,
            "design_id": design_id,
        })
        if not spaceport_ship:
            raise HTTPException(status_code=404, detail=f"No ships of design {design_id} found in spaceport")
        spaceport_ship_obj = SpaceportShips(**spaceport_ship)
        if spaceport_ship_obj.quantity < requested_quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough ships. Have {spaceport_ship_obj.quantity}, requested {requested_quantity}",
            )

        design = await db.ship_designs.find_one({"id": design_id})
        if design:
            ship_speed = ShipDesign(**design).calculated_stats.get("speed", 1)
            slowest_speed = min(slowest_speed, ship_speed)

        fleet_ships.append({"design_id": design_id, "quantity": requested_quantity})

        new_quantity = spaceport_ship_obj.quantity - requested_quantity
        if new_quantity > 0:
            await db.spaceport_ships.update_one(
                {"id": spaceport_ship_obj.id},
                {"$set": {"quantity": new_quantity}},
            )
        else:
            await db.spaceport_ships.delete_one({"id": spaceport_ship_obj.id})

    fleet = Fleet(
        user_id=current_user.id,
        name=fleet_data.fleet_name,
        position=planet_obj.position,
        ships=fleet_ships,
        fleet_speed=slowest_speed,
    )
    await db.fleets.insert_one(fleet.dict())
    return {"message": f"Flotte '{fleet_data.fleet_name}' erstellt", "fleet": fleet.dict()}


@router.get("/fleets", response_model=List[Fleet])
async def get_user_fleets(current_user: User = Depends(get_current_user)):
    fleets = await db.fleets.find({"user_id": current_user.id}).to_list(100)
    return [Fleet(**fleet) for fleet in fleets]


@router.post("/move-fleet")
async def move_fleet(move_data: MoveFleet, current_user: User = Depends(get_current_user)):
    fleet = await db.fleets.find_one({"id": move_data.fleet_id, "user_id": current_user.id})
    if not fleet:
        raise HTTPException(status_code=404, detail="Fleet not found")

    fleet_obj = Fleet(**fleet)
    dx = abs(move_data.target_position.x - fleet_obj.position.x)
    dy = abs(move_data.target_position.y - fleet_obj.position.y)
    distance = max(dx, dy)
    movement_points_needed = distance * MOVEMENT_POINTS_NORMAL
    ticks_needed = max(1, movement_points_needed // fleet_obj.fleet_speed)

    config = await get_game_config()
    movement_start_time = utc_now()
    movement_end_time = movement_start_time + timedelta(seconds=ticks_needed * config.tick_duration)

    await db.fleets.update_one(
        {"id": move_data.fleet_id},
        {"$set": {
            "target_position": move_data.target_position.dict(),
            "movement_start_time": movement_start_time,
            "movement_end_time": movement_end_time,
        }},
    )
    return {
        "message": "Fleet movement started",
        "arrival_time": movement_end_time.isoformat(),
        "ticks_needed": ticks_needed,
    }


@router.post("/fleet/stance")
async def set_fleet_stance(stance_data: SetFleetStance, current_user: User = Depends(get_current_user)):
    if stance_data.stance not in ("defensive", "aggressive"):
        raise HTTPException(status_code=400, detail="Invalid stance. Use 'defensive' or 'aggressive'")
    fleet = await db.fleets.find_one({"id": stance_data.fleet_id, "user_id": current_user.id})
    if not fleet:
        raise HTTPException(status_code=404, detail="Fleet not found")
    await db.fleets.update_one({"id": stance_data.fleet_id}, {"$set": {"stance": stance_data.stance}})
    return {
        "message": f"Fleet stance set to {stance_data.stance}",
        "fleet_id": stance_data.fleet_id,
        "stance": stance_data.stance,
    }
