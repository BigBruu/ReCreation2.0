"""TheCreation Authentic – API entrypoint.

Application setup, middleware, router registration and lifespan only.
All endpoints live in routes/ and all logic lives in services/.
"""

import logging

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app_config import get_cors_origins
from lifespan import lifespan
from routes import (admin as admin_routes, auth as auth_routes,
                    buildings as buildings_routes, combat as combat_routes,
                    fleets as fleets_routes, game as game_routes,
                    research as research_routes, ships as ships_routes)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="TheCreation Authentic", lifespan=lifespan)

api_router = APIRouter(prefix="/api")
for module in (auth_routes, admin_routes, game_routes, ships_routes,
               fleets_routes, combat_routes, buildings_routes, research_routes):
    api_router.include_router(module.router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=get_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)
