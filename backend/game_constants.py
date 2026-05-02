"""Authentic game constants – fixed game data, never changes at runtime."""

UNIVERSE_SIZE = 47
OBSERVATORY_VIEW_SIZE = 7  # 7x7 view centered on spaceport
MAX_PLAYERS = 20
TICK_DURATION = 60  # 1 minute per tick (default; can be overridden by config)
MOVEMENT_POINTS_NORMAL = 6000
MOVEMENT_POINTS_DIAGONAL = 7200

# Planet Types with Authentic Resources (NO SILICON - only Food, Metal, Hydrogen)
PLANET_TYPES = {
    "green": {
        "color": "green",
        "base_resources": {"food": 50000000, "metal": 30000000, "hydrogen": 15000000},
    },
    "blue": {
        "color": "blue",
        "base_resources": {"food": 20000000, "metal": 60000000, "hydrogen": 50000000},
    },
    "brown": {
        "color": "brown",
        "base_resources": {"food": 15000000, "metal": 70000000, "hydrogen": 35000000},
    },
    "orange": {
        "color": "orange",
        "base_resources": {"food": 35000000, "metal": 45000000, "hydrogen": 50000000},
    },
}

# Maps planet type to user-visible resource name
PLANET_TYPE_TO_NAME = {
    "green": "Nahrung",
    "blue": "Wasserstoff",
    "brown": "Metall",
    "orange": "Wasserstoff",
}

# Building System Configuration
BUILDING_TYPES = {
    "plantage": {
        "name": "Plantage",
        "description": "Produziert Nahrung pro Tick",
        "base_cost": 500,
        "cost_increase_percent": 5,
        "base_build_time_ticks": 5,
        "build_time_increase_percent": 5,
        "resource_bonus_per_level": 5,
        "resource_type": "food",
        "category": "resource",
    },
    "erzmine": {
        "name": "Erzmine",
        "description": "Produziert Metall pro Tick",
        "base_cost": 500,
        "cost_increase_percent": 5,
        "base_build_time_ticks": 5,
        "build_time_increase_percent": 5,
        "resource_bonus_per_level": 5,
        "resource_type": "metal",
        "category": "resource",
    },
    "elektrolysator": {
        "name": "Elektrolysator",
        "description": "Produziert Wasserstoff pro Tick",
        "base_cost": 500,
        "cost_increase_percent": 5,
        "base_build_time_ticks": 5,
        "build_time_increase_percent": 5,
        "resource_bonus_per_level": 5,
        "resource_type": "hydrogen",
        "category": "resource",
    },
    "werft": {
        "name": "Werft",
        "description": "+1 Prototyp-Slot pro Level",
        "base_cost": 5000,
        "cost_increase_percent": 10,
        "base_build_time_ticks": 15,
        "build_time_increase_percent": 5,
        "prototype_slots_per_level": 1,
        "category": "special",
    },
    "raumhafen": {
        "name": "Raumhafen",
        "description": "+1 Flotte pro Level",
        "base_cost": 10000,
        "cost_increase_percent": 15,
        "base_build_time_ticks": 20,
        "build_time_increase_percent": 5,
        "fleet_slots_per_level": 1,
        "category": "special",
    },
    "forschungslabor": {
        "name": "Forschungslabor",
        "description": "-13% Forschungszeit pro Level",
        "base_cost": 15000,
        "cost_increase_percent": 8,
        "base_build_time_ticks": 30,
        "build_time_increase_percent": 5,
        "research_time_reduction_percent": 13,
        "category": "special",
    },
}

# Authentic Component Levels and Stats
COMPONENT_LEVELS = {
    "drives": {
        "ionenstrahl": {"levels": [1, 2, 3, 4], "speed_base": 350, "weight": 50},
        "rakete": {"levels": [1, 2, 3], "speed_base": 20, "weight": 2},
        "segel": {"levels": [1, 2, 3, 4, 5], "speed_base": 200, "weight": 20},
        "fusion": {"levels": [1, 2, 3, 4, 5, 6], "speed_base": 2000, "weight": 500},
        "antimaterie": {"levels": [1, 2, 3, 4, 5, 6, 7], "speed_base": 10000, "weight": 1000},
    },
    "shields": {
        "stahl": {"levels": [1, 2, 3, 4, 5], "defense_base": 5, "weight": 2},
        "aluminium": {"levels": [1, 2, 3, 4, 5], "defense_base": 5, "weight": 1},
        "quarz": {"levels": [1, 2, 3, 4, 5, 6], "defense_base": 20, "weight": 5},
        "titan": {"levels": [1, 2, 3, 4, 5, 6], "defense_base": 70, "weight": 50},
        "diamant": {"levels": [1, 2, 3, 4, 5, 6], "defense_base": 25, "weight": 20},
        "kupfer": {"levels": [1, 2, 3, 4, 5, 6], "defense_base": 500, "weight": 400},
        "keramik": {"levels": [1, 2, 3, 4, 5, 6], "defense_base": 1500, "weight": 600},
        "chrom": {"levels": [1, 2, 3, 4, 5, 6], "defense_base": 200, "weight": 150},
    },
    "weapons": {
        "laser": {"levels": [1, 2, 3, 4, 5, 6], "attack_base": 20, "weight": 60},
        "projektil": {"levels": [1, 2, 3, 4], "attack_base": 7, "weight": 1},
        "konventionell": {"levels": [1, 2, 3, 4, 5], "attack_base": 60, "weight": 50},
        "emp": {"levels": [1, 2, 3, 4, 5, 6], "attack_base": 25, "weight": 150},
        "plasma": {"levels": [1, 2, 3, 4, 5, 6], "attack_base": 50, "weight": 250},
        "abbaueinheit": {"levels": [1, 2, 3, 4, 5], "attack_base": 10, "weight": 2000, "mining_base": 100},
    },
    "special": {
        "kolonieeinheit": {"levels": [1], "weight": 5000},
    },
}

# Research costs and times (authentic from original)
RESEARCH_BASE_COSTS = {
    "drives": {
        "segel": {"base_cost": 5000, "base_time_hours": 1},
        "fusion": {"base_cost": 750000, "base_time_hours": 24},
        "antimaterie": {"base_cost": 10000000, "base_time_hours": 72},
        "ionenstrahl": {"base_cost": 100000, "base_time_hours": 12},
        "rakete": {"base_cost": 1000, "base_time_hours": 0.5},
    },
    "shields": {
        "stahl": {"base_cost": 2000, "base_time_hours": 0.5},
        "aluminium": {"base_cost": 2500, "base_time_hours": 0.5},
        "quarz": {"base_cost": 50000, "base_time_hours": 6},
        "titan": {"base_cost": 200000, "base_time_hours": 18},
        "diamant": {"base_cost": 500000, "base_time_hours": 24},
        "kupfer": {"base_cost": 1000000, "base_time_hours": 36},
        "keramik": {"base_cost": 2500000, "base_time_hours": 48},
        "chrom": {"base_cost": 800000, "base_time_hours": 30},
    },
    "weapons": {
        "projektil": {"base_cost": 1500, "base_time_hours": 0.5},
        "laser": {"base_cost": 500000, "base_time_hours": 18},
        "konventionell": {"base_cost": 25000, "base_time_hours": 4},
        "emp": {"base_cost": 1500000, "base_time_hours": 36},
        "plasma": {"base_cost": 7500000, "base_time_hours": 60},
        "abbaueinheit": {"base_cost": 50000, "base_time_hours": 8},
    },
}
