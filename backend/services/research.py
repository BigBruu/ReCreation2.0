"""Research helpers: cost/time formulas, initialization."""

from database import db
from game_constants import RESEARCH_BASE_COSTS
from models import ResearchLevel, UserResearch


async def init_user_research(user_id: str) -> UserResearch:
    """Initialize research levels for a new user – all start at level 0."""
    existing = await db.user_research.find_one({"user_id": user_id})
    if existing:
        return UserResearch(**existing)

    research_levels = [
        ResearchLevel(category=category, technology=tech_name, level=0)
        for category, technologies in RESEARCH_BASE_COSTS.items()
        for tech_name in technologies
    ]
    user_research = UserResearch(user_id=user_id, research_levels=research_levels)
    await db.user_research.insert_one(user_research.dict())
    return user_research


def calculate_research_cost(base_cost: int, current_level: int) -> int:
    """Cost grows with (level+1) but each level shrinks the per-unit cost by 15%."""
    reduction_factor = 0.85 ** current_level
    return int(base_cost * reduction_factor * (current_level + 1))


def calculate_research_time(base_time_hours: float, current_level: int) -> float:
    return base_time_hours * (current_level + 1)
