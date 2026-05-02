import secrets
import string
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app_config import ACCESS_TOKEN_EXPIRE_MINUTES, utc_now
from auth_deps import require_admin
from database import db
from models import (AdminLogin, CreateInviteCode, GameConfig, InviteCode,
                    NewRoundConfig, UpdateGameConfig)
from security import create_access_token, verify_admin_password
from services.config_cache import (get_game_config, init_game_config,
                                   invalidate_config_cache)
from services.universe import generate_universe, init_game_state

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login")
async def admin_login(admin_data: AdminLogin):
    if not verify_admin_password(admin_data.password):
        raise HTTPException(status_code=401, detail="Invalid admin password")
    access_token = create_access_token(
        data={"sub": "admin", "admin": True},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer", "admin": True}


@router.get("/config", response_model=GameConfig)
async def get_admin_config(_: dict = Depends(require_admin)):
    return await get_game_config()


@router.post("/config")
async def update_admin_config(config_update: UpdateGameConfig, _: dict = Depends(require_admin)):
    update_data = {k: v for k, v in config_update.dict().items() if v is not None}
    await db.game_config.update_one({}, {"$set": update_data})
    invalidate_config_cache()
    return {"message": "Configuration updated successfully"}


@router.post("/invite-codes", response_model=InviteCode)
async def create_invite_code(invite_data: CreateInviteCode, _: dict = Depends(require_admin)):
    code = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    expires_at = utc_now() + timedelta(hours=invite_data.expires_in_hours) if invite_data.expires_in_hours else None
    invite_code = InviteCode(code=code, max_uses=invite_data.max_uses, expires_at=expires_at)
    await db.invite_codes.insert_one(invite_code.dict())
    return invite_code


@router.get("/invite-codes", response_model=List[InviteCode])
async def get_invite_codes(_: dict = Depends(require_admin)):
    codes = await db.invite_codes.find().sort("created_at", -1).to_list(100)
    return [InviteCode(**code) for code in codes]


@router.delete("/invite-codes/{code_id}")
async def delete_invite_code(code_id: str, _: dict = Depends(require_admin)):
    result = await db.invite_codes.delete_one({"id": code_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Invite code not found")
    return {"message": "Invite code deleted successfully"}


@router.get("/users")
async def get_all_users(_: dict = Depends(require_admin)):
    users = await db.users.find().sort("created_at", -1).to_list(100)
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
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "points": user.get("points", 0),
            "planets": planet_counts.get(user["id"], 0),
            "fleets": fleet_counts.get(user["id"], 0),
            "created_at": user["created_at"],
            "spaceport_position": user.get("spaceport_position", {"x": -1, "y": -1}),
        }
        for user in users
    ]


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, _: dict = Depends(require_admin)):
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    await db.planets.update_many(
        {"owner_id": user_id},
        {"$set": {"owner_id": None, "owner_username": None}},
    )
    await db.fleets.delete_many({"user_id": user_id})
    await db.ship_designs.delete_many({"user_id": user_id})
    await db.user_buildings.delete_one({"user_id": user_id})
    await db.user_research.delete_one({"user_id": user_id})
    await db.spaceport_ships.delete_many({"user_id": user_id})

    return {"message": "User deleted successfully"}


@router.post("/reset-game")
async def reset_game(_: dict = Depends(require_admin)):
    for collection in (
        db.users, db.planets, db.fleets, db.ship_designs,
        db.user_buildings, db.user_research, db.spaceport_ships,
        db.battle_reports, db.debris_fields, db.game_state,
    ):
        await collection.delete_many({})
    invalidate_config_cache()
    await init_game_state()
    return {"message": "Game reset successfully"}


@router.post("/new-round")
async def start_new_round(cfg: NewRoundConfig, _: dict = Depends(require_admin)):
    if not (15 <= cfg.universe_size <= 50):
        raise HTTPException(status_code=422, detail="Spielfeldgröße muss zwischen 15 und 50 liegen")
    if not (10 <= cfg.tick_duration <= 60):
        raise HTTPException(status_code=422, detail="Tick-Dauer muss zwischen 10 und 60 Sekunden liegen")
    if cfg.planet_count < 1:
        raise HTTPException(status_code=422, detail="Planetenanzahl muss mindestens 1 sein")
    if cfg.resources_per_planet < 1:
        raise HTTPException(status_code=422, detail="Ressourcen pro Planet müssen mindestens 1 sein")
    if cfg.max_players < 1:
        raise HTTPException(status_code=422, detail="Maximale Spieleranzahl muss mindestens 1 sein")

    for collection in (
        db.users, db.planets, db.fleets, db.ship_designs,
        db.user_buildings, db.user_research, db.spaceport_ships,
        db.battle_reports, db.debris_fields, db.game_state,
    ):
        await collection.delete_many({})

    await db.game_config.update_one(
        {},
        {"$set": {
            "universe_size":        cfg.universe_size,
            "tick_duration":        cfg.tick_duration,
            "max_players":          cfg.max_players,
            "min_planet_resources": cfg.resources_per_planet,
            "max_planet_resources": cfg.resources_per_planet,
        }},
        upsert=True,
    )
    invalidate_config_cache()
    await init_game_state()
    await generate_universe(
        explicit_planet_count=cfg.planet_count,
        explicit_resource_amount=cfg.resources_per_planet,
    )

    actual_planets = await db.planets.count_documents({})
    return {
        "message": "Neue Runde erfolgreich gestartet",
        "universe_size":        f"{cfg.universe_size}x{cfg.universe_size}",
        "planets_created":      actual_planets,
        "resources_per_planet": cfg.resources_per_planet,
        "tick_duration":        f"{cfg.tick_duration}s",
        "max_players":          cfg.max_players,
    }


@router.get("/stats")
async def get_admin_stats(_: dict = Depends(require_admin)):
    config = await get_game_config()
    user_count = await db.users.count_documents({})
    planet_count = await db.planets.count_documents({})
    occupied_planets = await db.planets.count_documents({"owner_id": {"$ne": None}})
    fleet_count = await db.fleets.count_documents({})
    invite_codes = await db.invite_codes.count_documents({})
    return {
        "players": {"current": user_count, "max": config.max_players},
        "planets": {"total": planet_count, "occupied": occupied_planets},
        "fleets": fleet_count,
        "invite_codes": invite_codes,
        "universe_size": f"{config.universe_size}x{config.universe_size}",
        "tick_duration": f"{config.tick_duration}s",
    }
