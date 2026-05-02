"""Pydantic models for the game."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app_config import utc_now
from game_constants import TICK_DURATION


# --- AUTH MODELS ---
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserCreateWithInvite(BaseModel):
    username: str
    email: str
    password: str
    invite_code: str


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=utc_now)
    points: int = 0
    spaceport_position: Dict[str, int] = Field(default_factory=lambda: {"x": -1, "y": -1})


# --- AUTHENTIC GAME MODELS ---
class Resources(BaseModel):
    food: int = 0
    metal: int = 0
    hydrogen: int = 0


class Position(BaseModel):
    x: int
    y: int


class Planet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    position: Position
    planet_type: str  # "green", "blue", "brown", "orange"
    name: str
    resources: Resources
    owner_id: Optional[str] = None
    owner_username: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)


# --- BUILDING MODELS ---
class BuildingLevel(BaseModel):
    building_type: str
    level: int = 0
    upgrading: bool = False
    upgrade_start_time: Optional[datetime] = None
    upgrade_end_time: Optional[datetime] = None


class UserBuildings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    buildings: List[BuildingLevel] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class UpgradeBuilding(BaseModel):
    building_type: str


# --- SHIP / FLEET MODELS ---
class ShipComponent(BaseModel):
    component_type: str
    component_name: str
    level: int
    quantity: int


class ShipDesign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    drive: ShipComponent
    shield: ShipComponent
    weapon: ShipComponent
    calculated_stats: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class Fleet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    position: Position
    target_position: Optional[Position] = None
    ships: List[Dict[str, Any]] = Field(default_factory=list)
    movement_start_time: Optional[datetime] = None
    movement_end_time: Optional[datetime] = None
    fleet_speed: int = 0
    stance: str = "defensive"  # "defensive" or "aggressive"
    created_at: datetime = Field(default_factory=utc_now)


class SpaceportShips(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    planet_id: str
    design_id: str
    quantity: int
    created_at: datetime = Field(default_factory=utc_now)


# --- COMBAT SYSTEM MODELS ---
class DebrisField(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    position: Position
    resource_type: str  # "food", "metal", or "hydrogen"
    amount: int
    created_at: datetime = Field(default_factory=utc_now)


class BattleReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tick: int
    position: Position
    attacker_user_id: str
    attacker_username: str
    attacker_fleet_name: str
    attacker_combat_value: int
    attacker_ships_before: List[Dict[str, Any]]
    attacker_ships_lost: List[Dict[str, Any]]
    defender_user_id: str
    defender_username: str
    defender_fleet_name: str
    defender_combat_value: int
    defender_ships_before: List[Dict[str, Any]]
    defender_ships_lost: List[Dict[str, Any]]
    winner: str
    debris_created: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=utc_now)


# --- GAME STATE & CONFIG ---
class GameState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    current_tick: int = 0
    last_tick_time: datetime = Field(default_factory=utc_now)
    next_tick_time: datetime = Field(default_factory=lambda: utc_now() + timedelta(seconds=TICK_DURATION))
    active_players: int = 0
    game_started: bool = False
    created_at: datetime = Field(default_factory=utc_now)


class GameConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    max_players: int = 20
    universe_size: int = 47
    tick_duration: int = 60
    min_planet_resources: int = 10000000
    max_planet_resources: int = 100000000
    mining_efficiency: float = 1.0
    colonization_time_hours: int = 24
    noob_protection_hours: int = 48
    created_at: datetime = Field(default_factory=utc_now)


# --- ADMIN MODELS ---
class InviteCode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    created_by_admin: bool = True
    used_by_user_id: Optional[str] = None
    used_by_username: Optional[str] = None
    used_at: Optional[datetime] = None
    max_uses: int = 1
    current_uses: int = 0
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now)


class AdminLogin(BaseModel):
    password: str


class CreateInviteCode(BaseModel):
    max_uses: int = 1
    expires_in_hours: Optional[int] = None


class UpdateGameConfig(BaseModel):
    max_players: Optional[int] = None
    universe_size: Optional[int] = None
    tick_duration: Optional[int] = None
    min_planet_resources: Optional[int] = None
    max_planet_resources: Optional[int] = None
    mining_efficiency: Optional[float] = None
    colonization_time_hours: Optional[int] = None
    noob_protection_hours: Optional[int] = None


class NewRoundConfig(BaseModel):
    resources_per_planet: int
    planet_count: int
    universe_size: int
    tick_duration: int
    max_players: int


# --- REQUEST MODELS ---
class ObservatoryView(BaseModel):
    center_x: int
    center_y: int


class CreateShipDesign(BaseModel):
    name: str
    drive_type: str
    drive_level: int
    drive_quantity: int
    shield_type: str
    shield_level: int
    shield_quantity: int
    weapon_type: str
    weapon_level: int
    weapon_quantity: int


class BuildFleet(BaseModel):
    planet_id: str
    design_id: str
    quantity: int
    fleet_name: str


class MoveFleet(BaseModel):
    fleet_id: str
    target_position: Position


class BuildShips(BaseModel):
    planet_id: str
    design_id: str
    quantity: int


class CreateFleetFromSpaceport(BaseModel):
    planet_id: str
    fleet_name: str
    ships: List[Dict[str, Any]]


class SetFleetStance(BaseModel):
    fleet_id: str
    stance: str  # "defensive" or "aggressive"


# --- RESEARCH MODELS ---
class ResearchLevel(BaseModel):
    category: str
    technology: str
    level: int = 0
    researching: bool = False
    research_start_time: Optional[datetime] = None
    research_end_time: Optional[datetime] = None


class UserResearch(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    research_levels: List[ResearchLevel] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class StartResearch(BaseModel):
    category: str
    technology: str
