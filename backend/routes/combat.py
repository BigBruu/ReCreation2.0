from fastapi import APIRouter, Depends, HTTPException

from auth_deps import get_current_user
from database import db
from models import User

router = APIRouter(prefix="/game", tags=["combat"])


@router.get("/battle-reports")
async def get_battle_reports(current_user: User = Depends(get_current_user)):
    reports = await db.battle_reports.find({
        "$or": [
            {"attacker_user_id": current_user.id},
            {"defender_user_id": current_user.id},
        ]
    }).sort("created_at", -1).to_list(50)

    result = []
    for report in reports:
        report_data = report.copy()
        report_data.pop("_id", None)
        for key in ("attacker_ships_before", "attacker_ships_lost",
                    "defender_ships_before", "defender_ships_lost"):
            enriched = []
            for ship in report_data.get(key, []):
                design = await db.ship_designs.find_one({"id": ship["design_id"]})
                ship_info = ship.copy()
                ship_info["design_name"] = design["name"] if design else "Unbekannt"
                enriched.append(ship_info)
            report_data[key] = enriched
        result.append(report_data)
    return result


@router.get("/debris-fields")
async def get_debris_fields(current_user: User = Depends(get_current_user)):
    debris = await db.debris_fields.find({}).to_list(1000)
    return [
        {"id": d["id"], "position": d["position"], "resource_type": d["resource_type"], "amount": d["amount"]}
        for d in debris
    ]


@router.post("/collect-debris")
async def collect_debris(debris_id: str, current_user: User = Depends(get_current_user)):
    debris = await db.debris_fields.find_one({"id": debris_id})
    if not debris:
        raise HTTPException(status_code=404, detail="Debris field not found")

    fleet = await db.fleets.find_one({
        "user_id": current_user.id,
        "position.x": debris["position"]["x"],
        "position.y": debris["position"]["y"],
        "movement_end_time": None,
    })
    if not fleet:
        raise HTTPException(status_code=400, detail="No stationary fleet at debris position")

    user_planet = await db.planets.find_one({"owner_id": current_user.id})
    if not user_planet:
        raise HTTPException(status_code=400, detail="No planet to store resources")

    resource_type = debris["resource_type"]
    amount = debris["amount"]
    await db.planets.update_one(
        {"id": user_planet["id"]},
        {"$inc": {f"resources.{resource_type}": amount}},
    )
    await db.debris_fields.delete_one({"id": debris_id})
    return {
        "message": f"Collected {amount} {resource_type} from debris",
        "resource_type": resource_type,
        "amount": amount,
    }
