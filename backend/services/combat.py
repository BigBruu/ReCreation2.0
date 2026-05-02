"""Combat resolution between two fleets."""

import random
from typing import Dict, Optional

from database import db
from models import BattleReport, DebrisField, Fleet, GameState, ShipDesign


async def calculate_fleet_combat_value(fleet: Fleet) -> int:
    total = 0
    for ship_group in fleet.ships:
        design = await db.ship_designs.find_one({"id": ship_group["design_id"]})
        if design:
            cv = ShipDesign(**design).calculated_stats.get("combat_value", 0)
            total += cv * ship_group["quantity"]
    return total


async def calculate_fleet_build_cost(fleet: Fleet) -> Dict[str, int]:
    total_cost = {"food": 0, "metal": 0, "hydrogen": 0}
    for ship_group in fleet.ships:
        design = await db.ship_designs.find_one({"id": ship_group["design_id"]})
        if design:
            build_cost = ShipDesign(**design).calculated_stats.get("build_cost", {})
            for resource in ("food", "metal", "hydrogen"):
                total_cost[resource] += build_cost.get(resource, 0) * ship_group["quantity"]
    return total_cost


async def process_combat(attacker_fleet: Fleet, defender_fleet: Fleet, game_state: GameState) -> Optional[BattleReport]:
    """Resolve combat between two fleets and return a battle report."""
    attacker_user = await db.users.find_one({"id": attacker_fleet.user_id})
    defender_user = await db.users.find_one({"id": defender_fleet.user_id})

    if not attacker_user or not defender_user:
        return None

    attacker_cv = await calculate_fleet_combat_value(attacker_fleet)
    defender_cv = await calculate_fleet_combat_value(defender_fleet)

    attacker_ships_before = [s.copy() for s in attacker_fleet.ships]
    defender_ships_before = [s.copy() for s in defender_fleet.ships]

    if attacker_cv + defender_cv == 0:
        return None

    winner = "attacker" if attacker_cv > defender_cv else "defender"

    if winner == "attacker":
        defender_loss_ratio = min(1.0, attacker_cv / max(1, defender_cv) * 0.5)
        attacker_loss_ratio = min(0.8, defender_cv / max(1, attacker_cv) * 0.3)
    else:
        attacker_loss_ratio = min(1.0, defender_cv / max(1, attacker_cv) * 0.5)
        defender_loss_ratio = min(0.8, attacker_cv / max(1, defender_cv) * 0.3)

    attacker_ships_lost, new_attacker_ships = [], []
    for ship_group in attacker_fleet.ships:
        lost = int(ship_group["quantity"] * attacker_loss_ratio)
        remaining = ship_group["quantity"] - lost
        if lost > 0:
            attacker_ships_lost.append({"design_id": ship_group["design_id"], "quantity": lost})
        if remaining > 0:
            new_attacker_ships.append({"design_id": ship_group["design_id"], "quantity": remaining})

    defender_ships_lost, new_defender_ships = [], []
    for ship_group in defender_fleet.ships:
        lost = int(ship_group["quantity"] * defender_loss_ratio)
        remaining = ship_group["quantity"] - lost
        if lost > 0:
            defender_ships_lost.append({"design_id": ship_group["design_id"], "quantity": lost})
        if remaining > 0:
            new_defender_ships.append({"design_id": ship_group["design_id"], "quantity": remaining})

    # Calculate debris (20% of build costs of all destroyed ships)
    total_debris_cost = {"food": 0, "metal": 0, "hydrogen": 0}
    for lost_ship in (*attacker_ships_lost, *defender_ships_lost):
        design = await db.ship_designs.find_one({"id": lost_ship["design_id"]})
        if design:
            build_cost = ShipDesign(**design).calculated_stats.get("build_cost", {})
            for resource in ("food", "metal", "hydrogen"):
                total_debris_cost[resource] += int(build_cost.get(resource, 0) * lost_ship["quantity"] * 0.2)

    debris_info = None
    total_debris = sum(total_debris_cost.values())
    if total_debris > 0:
        debris_resource = random.choice(["food", "metal", "hydrogen"])
        debris_field = DebrisField(
            position=attacker_fleet.position,
            resource_type=debris_resource,
            amount=total_debris,
        )
        await db.debris_fields.insert_one(debris_field.dict())
        debris_info = {"resource_type": debris_resource, "amount": total_debris}

    # Update or destroy fleets
    if new_attacker_ships:
        await db.fleets.update_one({"id": attacker_fleet.id}, {"$set": {"ships": new_attacker_ships}})
    else:
        await db.fleets.delete_one({"id": attacker_fleet.id})

    if new_defender_ships:
        await db.fleets.update_one({"id": defender_fleet.id}, {"$set": {"ships": new_defender_ships}})
    else:
        await db.fleets.delete_one({"id": defender_fleet.id})

    battle_report = BattleReport(
        tick=game_state.current_tick,
        position=attacker_fleet.position,
        attacker_user_id=attacker_fleet.user_id,
        attacker_username=attacker_user["username"],
        attacker_fleet_name=attacker_fleet.name,
        attacker_combat_value=attacker_cv,
        attacker_ships_before=attacker_ships_before,
        attacker_ships_lost=attacker_ships_lost,
        defender_user_id=defender_fleet.user_id,
        defender_username=defender_user["username"],
        defender_fleet_name=defender_fleet.name,
        defender_combat_value=defender_cv,
        defender_ships_before=defender_ships_before,
        defender_ships_lost=defender_ships_lost,
        winner=winner,
        debris_created=debris_info,
    )
    await db.battle_reports.insert_one(battle_report.dict())
    return battle_report
