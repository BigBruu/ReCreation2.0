from typing import List

from fastapi import APIRouter, Depends, HTTPException

from auth_deps import get_current_user
from database import db
from game_constants import COMPONENT_LEVELS
from models import (BuildShips, CreateShipDesign, Planet, ShipComponent,
                    ShipDesign, SpaceportShips, User, UserBuildings)
from services.ships import calculate_ship_stats

router = APIRouter(prefix="/game", tags=["ships"])


@router.post("/ship-design", response_model=ShipDesign)
async def create_ship_design(design_data: CreateShipDesign, current_user: User = Depends(get_current_user)):
    user_buildings_data = await db.user_buildings.find_one({"user_id": current_user.id})
    werft_level = 0
    if user_buildings_data:
        for building in UserBuildings(**user_buildings_data).buildings:
            if building.building_type == "werft":
                werft_level = building.level
                break

    max_prototypes = werft_level
    current_designs = await db.ship_designs.count_documents({"user_id": current_user.id})
    if current_designs >= max_prototypes:
        raise HTTPException(
            status_code=400,
            detail=f"Prototyp-Limit erreicht! Werft Level {werft_level} erlaubt nur {max_prototypes} Prototypen. Bauen Sie die Werft aus.",
        )

    if design_data.drive_type not in COMPONENT_LEVELS["drives"]:
        raise HTTPException(status_code=400, detail="Invalid drive type")
    if design_data.shield_type not in COMPONENT_LEVELS["shields"]:
        raise HTTPException(status_code=400, detail="Invalid shield type")
    if design_data.weapon_type not in COMPONENT_LEVELS["weapons"]:
        raise HTTPException(status_code=400, detail="Invalid weapon type")

    design = ShipDesign(
        user_id=current_user.id,
        name=design_data.name,
        drive=ShipComponent(component_type="drive", component_name=design_data.drive_type,
                            level=design_data.drive_level, quantity=design_data.drive_quantity),
        shield=ShipComponent(component_type="shield", component_name=design_data.shield_type,
                             level=design_data.shield_level, quantity=design_data.shield_quantity),
        weapon=ShipComponent(component_type="weapon", component_name=design_data.weapon_type,
                             level=design_data.weapon_level, quantity=design_data.weapon_quantity),
        calculated_stats=calculate_ship_stats(design_data),
    )
    await db.ship_designs.insert_one(design.dict())
    return design


@router.get("/ship-designs", response_model=List[ShipDesign])
async def get_ship_designs(current_user: User = Depends(get_current_user)):
    designs = await db.ship_designs.find({"user_id": current_user.id}).to_list(100)
    return [ShipDesign(**design) for design in designs]


@router.get("/component-levels")
async def get_component_levels():
    return COMPONENT_LEVELS


@router.post("/build-ships")
async def build_ships(build_data: BuildShips, current_user: User = Depends(get_current_user)):
    planet = await db.planets.find_one({"id": build_data.planet_id, "owner_id": current_user.id})
    if not planet:
        raise HTTPException(status_code=404, detail="Planet not found or not owned")

    design = await db.ship_designs.find_one({"id": build_data.design_id, "user_id": current_user.id})
    if not design:
        raise HTTPException(status_code=404, detail="Ship design not found")

    design_obj = ShipDesign(**design)
    planet_obj = Planet(**planet)
    total_cost = {
        "food": design_obj.calculated_stats["build_cost"]["food"] * build_data.quantity,
        "metal": design_obj.calculated_stats["build_cost"]["metal"] * build_data.quantity,
        "hydrogen": design_obj.calculated_stats["build_cost"]["hydrogen"] * build_data.quantity,
    }

    if (planet_obj.resources.food < total_cost["food"]
            or planet_obj.resources.metal < total_cost["metal"]
            or planet_obj.resources.hydrogen < total_cost["hydrogen"]):
        raise HTTPException(status_code=400, detail="Insufficient resources")

    await db.planets.update_one(
        {"id": build_data.planet_id},
        {"$inc": {
            "resources.food": -total_cost["food"],
            "resources.metal": -total_cost["metal"],
            "resources.hydrogen": -total_cost["hydrogen"],
        }},
    )
    spaceport_ships = SpaceportShips(
        user_id=current_user.id,
        planet_id=build_data.planet_id,
        design_id=build_data.design_id,
        quantity=build_data.quantity,
    )
    await db.spaceport_ships.insert_one(spaceport_ships.dict())
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"points": build_data.quantity * 50}},
    )
    return {"message": f"{build_data.quantity} Schiffe im Raumhafen produziert", "ships": spaceport_ships.dict()}


@router.get("/spaceport-ships")
async def get_spaceport_ships(current_user: User = Depends(get_current_user)):
    spaceport_ships = await db.spaceport_ships.find({"user_id": current_user.id}).to_list(1000)
    result = {}
    for ship_data in spaceport_ships:
        ship = SpaceportShips(**ship_data)
        planet = await db.planets.find_one({"id": ship.planet_id})
        design = await db.ship_designs.find_one({"id": ship.design_id})
        if not (planet and design):
            continue
        planet_key = f"{planet['name']} ({planet['position']['x']}, {planet['position']['y']})"
        if planet_key not in result:
            result[planet_key] = {
                "planet_id": ship.planet_id,
                "planet_name": planet["name"],
                "position": planet["position"],
                "ships": [],
            }
        result[planet_key]["ships"].append({
            "id": ship.id,
            "design_id": ship.design_id,
            "design_name": design["name"],
            "quantity": ship.quantity,
            "created_at": ship.created_at,
        })
    return result
