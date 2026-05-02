"""Ship statistics calculation."""

from typing import Any, Dict

from game_constants import COMPONENT_LEVELS
from models import CreateShipDesign


def calculate_ship_stats(design: CreateShipDesign) -> Dict[str, Any]:
    """Authentic ship statistics – Abbaueinheit is a weapon type with mining."""
    drive_data = COMPONENT_LEVELS["drives"][design.drive_type]
    shield_data = COMPONENT_LEVELS["shields"][design.shield_type]
    weapon_data = COMPONENT_LEVELS["weapons"][design.weapon_type]

    drive_weight = drive_data["weight"] * design.drive_quantity
    shield_weight = shield_data["weight"] * design.shield_quantity
    weapon_weight = weapon_data["weight"] * design.weapon_quantity
    total_weight = drive_weight + shield_weight + weapon_weight

    base_speed = drive_data["speed_base"] * design.drive_level * design.drive_quantity
    speed = max(1, int(base_speed / max(1, total_weight / 100)))

    attack_power = weapon_data["attack_base"] * design.weapon_level * design.weapon_quantity
    defense_power = shield_data["defense_base"] * design.shield_level * design.shield_quantity
    combat_value = attack_power + defense_power

    mining_capacity = 0
    if "mining_base" in weapon_data:
        mining_capacity = weapon_data["mining_base"] * design.weapon_level * design.weapon_quantity

    base_food_cost = 0
    base_metal_cost = (drive_weight + weapon_weight) * design.drive_level * 10 + (shield_weight + weapon_weight) * design.shield_level * 5
    base_hydrogen_cost = weapon_weight * design.weapon_level * 2

    build_time_ticks = max(1, total_weight // 100) + design.drive_level + design.shield_level + design.weapon_level

    return {
        "speed": speed,
        "combat_value": combat_value,
        "mining_capacity": mining_capacity,
        "total_weight": total_weight,
        "build_cost": {
            "food": base_food_cost,
            "metal": base_metal_cost,
            "hydrogen": base_hydrogen_cost,
        },
        "build_time_ticks": build_time_ticks,
    }
