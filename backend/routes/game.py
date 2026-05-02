from fastapi import APIRouter, Depends

from auth_deps import get_current_user
from database import db
from game_constants import MAX_PLAYERS, OBSERVATORY_VIEW_SIZE, UNIVERSE_SIZE
from models import Fleet, ObservatoryView, Planet, User
from services.config_cache import get_game_config
from services.tick import process_tick
from services.universe import init_game_state

router = APIRouter(prefix="/game", tags=["game"])


@router.get("/state")
async def get_game_state():
    game_state = await init_game_state()
    config = await get_game_config()
    state_dict = game_state.dict()
    state_dict["tick_duration"] = config.tick_duration
    return state_dict


@router.post("/observatory")
async def get_observatory_view(view_data: ObservatoryView, current_user: User = Depends(get_current_user)):
    center_x, center_y = view_data.center_x, view_data.center_y
    view = {}
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            x, y = center_x + dx, center_y + dy
            if 0 <= x < UNIVERSE_SIZE and 0 <= y < UNIVERSE_SIZE:
                view[f"{x},{y}"] = {"position": {"x": x, "y": y}, "planet": None, "fleets": []}

    planets = await db.planets.find({
        "position.x": {"$gte": center_x - 3, "$lte": center_x + 3},
        "position.y": {"$gte": center_y - 3, "$lte": center_y + 3},
    }).to_list(100)
    for planet_data in planets:
        planet = Planet(**planet_data)
        key = f"{planet.position.x},{planet.position.y}"
        if key in view:
            view[key]["planet"] = planet.dict()

    fleets = await db.fleets.find({
        "position.x": {"$gte": center_x - 3, "$lte": center_x + 3},
        "position.y": {"$gte": center_y - 3, "$lte": center_y + 3},
    }).to_list(100)
    for fleet_data in fleets:
        fleet = Fleet(**fleet_data)
        key = f"{fleet.position.x},{fleet.position.y}"
        if key in view:
            user = await db.users.find_one({"id": fleet.user_id})
            fleet_info = fleet.dict()
            fleet_info["username"] = user["username"] if user else "Unknown"
            view[key]["fleets"].append(fleet_info)

    return {"view": view, "center": {"x": center_x, "y": center_y}, "size": OBSERVATORY_VIEW_SIZE}


@router.get("/user-spaceport")
async def get_user_spaceport(current_user: User = Depends(get_current_user)):
    return {"spaceport_position": current_user.spaceport_position, "username": current_user.username}


@router.get("/planets")
async def get_user_planets(current_user: User = Depends(get_current_user)):
    planets = await db.planets.find({"owner_id": current_user.id}).to_list(100)
    return [Planet(**planet) for planet in planets]


@router.get("/rankings")
async def get_rankings():
    users = await db.users.find().sort("points", -1).to_list(MAX_PLAYERS)
    user_ids = [u["id"] for u in users]

    planet_pipeline = [
        {"$match": {"owner_id": {"$in": user_ids}}},
        {"$group": {"_id": "$owner_id", "count": {"$sum": 1}}},
    ]
    fleet_pipeline = [
        {"$match": {"user_id": {"$in": user_ids}}},
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
    ]
    planet_counts = {doc["_id"]: doc["count"] async for doc in db.planets.aggregate(planet_pipeline)}
    fleet_counts = {doc["_id"]: doc["count"] async for doc in db.fleets.aggregate(fleet_pipeline)}

    return [
        {
            "rank": i + 1,
            "username": user["username"],
            "points": user.get("points", 0),
            "planets": planet_counts.get(user["id"], 0),
            "fleets": fleet_counts.get(user["id"], 0),
        }
        for i, user in enumerate(users)
    ]


@router.post("/tick")
async def manual_tick():
    """Manual tick processing (debug / admin use)."""
    await process_tick()
    return {"message": "Tick processed successfully"}
