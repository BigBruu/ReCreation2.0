from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException

from app_config import utc_now
from auth_deps import get_current_user
from database import db
from game_constants import RESEARCH_BASE_COSTS
from models import StartResearch, User, UserBuildings, UserResearch
from services.research import (calculate_research_cost,
                               calculate_research_time, init_user_research)

router = APIRouter(prefix="/game", tags=["research"])


@router.get("/research", response_model=UserResearch)
async def get_user_research(current_user: User = Depends(get_current_user)):
    research = await db.user_research.find_one({"user_id": current_user.id})
    if not research:
        return await init_user_research(current_user.id)
    return UserResearch(**research)


@router.post("/research/start")
async def start_research(research_data: StartResearch, current_user: User = Depends(get_current_user)):
    research = await db.user_research.find_one({"user_id": current_user.id})
    research_obj = await init_user_research(current_user.id) if not research else UserResearch(**research)

    tech_research = next(
        (level for level in research_obj.research_levels
         if level.category == research_data.category and level.technology == research_data.technology),
        None,
    )
    if not tech_research:
        raise HTTPException(status_code=404, detail="Technology not found")
    if tech_research.researching:
        raise HTTPException(status_code=400, detail="Technology is already being researched")

    if any(level.researching for level in research_obj.research_levels):
        raise HTTPException(status_code=400, detail="You can only research one technology at a time")

    tech_costs = RESEARCH_BASE_COSTS[research_data.category][research_data.technology]
    actual_cost = calculate_research_cost(tech_costs["base_cost"], tech_research.level)
    base_research_time = calculate_research_time(tech_costs["base_time_hours"], tech_research.level)

    user_buildings_data = await db.user_buildings.find_one({"user_id": current_user.id})
    lab_level = 0
    if user_buildings_data:
        for building in UserBuildings(**user_buildings_data).buildings:
            if building.building_type == "forschungslabor":
                lab_level = building.level
                break

    research_time_reduction = 1 - ((1 - 0.13) ** lab_level)
    research_time = base_research_time * (1 - research_time_reduction)

    user_planets = await db.planets.find({"owner_id": current_user.id}).to_list(100)
    total_food = sum(planet["resources"]["food"] for planet in user_planets)
    if total_food < actual_cost:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient food. Need {actual_cost}, have {total_food}",
        )

    remaining_cost = actual_cost
    for planet in user_planets:
        if remaining_cost <= 0:
            break
        planet_food = planet["resources"]["food"]
        if planet_food > 0:
            deduction = min(planet_food, remaining_cost)
            await db.planets.update_one(
                {"id": planet["id"]},
                {"$inc": {"resources.food": -deduction}},
            )
            remaining_cost -= deduction

    research_start = utc_now()
    research_end = research_start + timedelta(hours=research_time)

    for i, level in enumerate(research_obj.research_levels):
        if level.category == research_data.category and level.technology == research_data.technology:
            research_obj.research_levels[i].researching = True
            research_obj.research_levels[i].research_start_time = research_start
            research_obj.research_levels[i].research_end_time = research_end
            break

    await db.user_research.update_one(
        {"user_id": current_user.id},
        {"$set": research_obj.dict()},
    )
    return {
        "message": f"Research started for {research_data.technology}",
        "cost": actual_cost,
        "completion_time": research_end.isoformat(),
        "duration_hours": research_time,
    }


@router.get("/research/costs")
async def get_research_costs():
    return RESEARCH_BASE_COSTS
