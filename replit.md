# TheCreation Authentic — Space Strategy Game

> **Audience:** Other AI coding agents working on this repository. This document is the source of truth for what the app does, how it is structured, and where to make changes.

## 1. Overview

A multiplayer browser-based 4X space strategy game with a tick-based economy, ship design, fleet movement, and combat. The UI is German ("Spieler", "Raumhafen", "Werft", "Forschung"). It is a single, persistent universe (default 47×47) with up to N players (default 20), running an authoritative tick loop on the backend (default 60 s).

- **Language of the UI:** German.
- **Communication with the user:** German preferred.
- **Tech stack:** FastAPI + MongoDB (Motor) backend, React 19 + Tailwind + CRACO frontend.

## 2. Architecture

### 2.1 Backend (FastAPI + Python, port 8000, localhost only)

`backend/server.py` is intentionally small (~40 lines). It only constructs the `FastAPI` app, attaches CORS middleware, registers routers, and wires the lifespan manager. All real logic lives in modules:

```
backend/
├── server.py              # app + middleware + routers (~40 lines)
├── app_config.py          # env validation, CORS origin list, utc_now() helper
├── database.py            # AsyncIOMotorClient + db handle
├── security.py            # JWT encode/decode, bcrypt, admin password compare
├── auth_deps.py           # FastAPI deps: get_current_user, require_admin
├── lifespan.py            # @asynccontextmanager: indexes, init, tick loop
├── indexes.py             # parallel index creation via asyncio.gather
├── models.py              # Pydantic request/response models
├── game_constants.py      # drives, shields, weapons, building defaults
├── services/
│   ├── config_cache.py    # in-memory game_config cache + invalidation
│   ├── universe.py        # planet generation, observatory view
│   ├── spaceport.py       # atomic spaceport assignment on registration
│   ├── buildings.py       # upgrade cost/time, current_bonus computation
│   ├── research.py        # cost/time formula, lab time reduction
│   ├── ships.py           # design stats (speed, CV, weight, build cost/time)
│   ├── combat.py          # battle resolution, debris creation
│   └── tick.py            # main tick: buildings, research, fleets, combat, mining
└── routes/
    ├── auth.py            # /register, /login, /me, /auth/session
    ├── admin.py           # /admin/* (stats, config, users, invites, new-round)
    ├── game.py            # /game/state, /game/observatory, /game/planets, /game/rankings, /game/tick
    ├── buildings.py       # /game/buildings, /game/buildings/upgrade, /game/building-types
    ├── ships.py           # /game/ship-design, /game/ship-designs, /game/build-ships, /game/spaceport-ships, /game/component-levels
    ├── fleets.py          # /game/create-fleet, /game/fleets, /game/move-fleet, /game/fleet/stance
    ├── research.py        # /game/research, /game/research/costs, /game/research/start
    └── combat.py          # /game/battle-reports, /game/debris-fields, /game/collect-debris
```

**Auth model.** JWT (HS256) signed with `SECRET_KEY`. Admin login compares a plaintext-equal password against `ADMIN_PASSWORD` env (no admin password ever stored in DB; legacy `admin_password` field is purged at startup). Tokens carry `{ sub: username, is_admin: bool }`. `get_current_user` rejects admin tokens; `require_admin` rejects user tokens.

**Lifespan startup order:**
1. Create MongoDB indexes in parallel (`asyncio.gather(...)`).
2. Strip any legacy `admin_password` field from `game_config`.
3. Initialize universe if `game_config` does not exist.
4. Spawn the background tick loop task.

**Tick loop.** A single `asyncio.create_task` polls every second. When `now >= next_tick_time`, it advances `current_tick`, runs `services/tick.process_tick`, and persists `next_tick_time = now + tick_duration`.

### 2.2 Frontend (React 19 + Tailwind + CRACO, port 5000, 0.0.0.0)

```
frontend/src/
├── App.js                                # routes: /login, /game, /admin
├── lib/api.js                            # API base URL + getAuthHeaders()
├── context/AuthContext.js                # login, logout, session validation
├── hooks/
│   ├── use-toast.js                      # shadcn toast helper
│   └── useGameData.js                    # central game state, parallel fetch, all action handlers
└── components/
    ├── LoginPage.js
    ├── ProtectedRoute.js                 # ProtectedRoute, AdminRoute
    ├── AdminPanel.js                     # admin shell + state + handlers (~200 lines)
    ├── admin/tabs/
    │   ├── DashboardTab.js
    │   ├── NewRoundTab.js
    │   ├── ConfigTab.js
    │   ├── UsersTab.js
    │   ├── InvitesTab.js
    │   └── ActionsTab.js
    └── game/
        ├── GameInterface.js              # game shell + sidebar + tab dispatcher (~250 lines)
        ├── Observatory.js                # 7×7 grid view, navigation, click handler
        ├── ShipDesignCalculator.js       # modal: design ships from components
        └── tabs/
            ├── SpaceportTab.js           # ships, fleets, battle reports, debris
            ├── ShipyardTab.js            # prototype list, build orders
            ├── BuildingsTab.js           # resource + special buildings, planet overview
            └── ResearchTab.js            # tech tree (drives/shields/weapons)
```

**Data flow.** `useGameData(user)` issues 12 parallel `axios.get` calls every 15 s and exposes `{state, planets, fleets, designs, ..., processTick, saveShipDesign, buildShips, startResearch, upgradeBuilding, setFleetStance, collectDebris, moveFleet, createFleet}`. Tabs are pure presentation: they receive props + handler callbacks and call them. Inputs are mostly uncontrolled (DOM IDs like `fleet-${id}-x`) — preserved from the original.

**API routing in dev.** `frontend/package.json` proxies `/api` to `http://localhost:8000`. `REACT_APP_BACKEND_URL` is intentionally unset in dev so relative `/api` paths flow through the React dev server proxy and the FastAPI port stays private.

## 3. Game Mechanics (Authoritative)

### 3.1 Universe

- Default grid: 47×47.
- `services/universe.generate_universe(size, planet_count, resources_per_planet)`: places planets uniformly at random until `planet_count` is reached.
- Planet types and resource bias: `green` (food-heavy), `blue` (hydrogen-heavy), `brown` (metal-heavy), `orange` (balanced).
- Each player gets one **spaceport planet** at registration via `services/spaceport.assign_spaceport_to_user(db, user_id, username)` — atomic via `find_one_and_update` so concurrent registrations cannot grab the same planet.

### 3.2 Resources

Three resources: `food`, `metal`, `hydrogen`. Stored per-planet. UI shows the player's totals (sum across owned planets) in the header.

### 3.3 Buildings

Six buildings, two categories.

| Building        | Category | Bonus per level                              |
|-----------------|----------|----------------------------------------------|
| `plantage`      | resource | +5 food / tick                                |
| `erzmine`       | resource | +5 metal / tick                               |
| `elektrolysator`| resource | +5 hydrogen / tick                            |
| `werft`         | special  | +1 prototype slot                             |
| `raumhafen`     | special  | +1 fleet slot                                 |
| `forschungslabor` | special | research time × 0.87^level (i.e. ~13 % faster per level, multiplicative) |

**Upgrade cost (metal):** `base_cost · (1 + cost_increase_pct/100)^level`.
**Upgrade time (ticks):** `base_build_time_ticks · (1 + build_time_increase_pct/100)^level`.

When an upgrade finishes during a tick, the level is incremented and the player gets +500 score points.

### 3.4 Research

Three categories: `drives`, `shields`, `weapons`. Each category has multiple technologies (e.g. `ionenstrahl`, `rakete`, `segel`, `fusion` for drives). All start at level 0. Only one research at a time per player.

- **Cost (food):** `base_cost · 0.85^level · (level + 1)` (15 % per-level reduction, then linear ramp).
- **Time (hours):** `base_time_hours · (level + 1) · (0.87^lab_level)`.

When research finishes the level is incremented and the player gets +1000 score points.

### 3.5 Ship Design

A design has exactly one drive, one shield, one weapon component (each: `{ component_name, level, quantity }`).

- **Total weight:** `Σ (component.weight · quantity)`.
- **Speed (pc/tick):** `max(1, (drive.base_speed · drive.level · drive.quantity) / max(1, total_weight / 100))`.
- **Combat value:** `(weapon.attack · weapon.level · weapon.quantity) + (shield.defense · shield.level · shield.quantity)`.
- **Mining capacity:** only present on certain drive/component combinations; expressed per ship.
- **Build time (ticks):** `max(1, total_weight // 100) + sum(component.level)`.
- **Build cost:** primarily metal (scaled by weight × level), hydrogen for weapons, optional food.

Designs are stored in `ship_designs`. Player's max number of prototypes equals `werft.level`.

### 3.6 Production & Spaceport

- Build ships against an existing design via `POST /api/game/build-ships { planet_id, design_id, quantity }`. Cost is deducted from that planet's resources up front.
- Built ships go into the **spaceport** of that planet (grouped by design), not directly into a fleet.
- Player's max number of active fleets equals `raumhafen.level`.

### 3.7 Fleets

- **Create fleet:** `POST /api/game/create-fleet { planet_id, fleet_name, ships: [{design_id, quantity}, …] }`. Pulls from spaceport into a new fleet at the planet's position.
- **Move fleet:** `POST /api/game/move-fleet { fleet_id, target_position: {x, y} }`. Distance is **Chebyshev** (`max(|dx|, |dy|)`). Travel time in ticks is `max(1, (distance · 6000) // fleet_speed)` where `fleet_speed = min(ship.speed for ship in fleet)`.
- **Stance:** `defensive` (default — only retaliates) or `aggressive` (initiates combat with any enemy at its position).

### 3.8 Combat

Combat resolves during the tick at any tile that has fleets from ≥ 2 players where ≥ 1 fleet is `aggressive`.

- **Winner:** higher total combat value (sum across ships).
- **Winner loss rate:** `min(0.8, (loser_cv / winner_cv) · 0.3)`.
- **Loser loss rate:** `min(1.0, (winner_cv / loser_cv) · 0.5)`.
- Ships are destroyed proportionally per design.
- A **battle report** is written and visible to both sides.
- A **debris field** containing 20 % of the destroyed ships' build cost is created at the position. Resource type is randomly one of food/metal/hydrogen.

### 3.9 Debris Collection

A stationary fleet (no ongoing movement) at the same tile as a debris field can collect it via `POST /api/game/collect-debris?debris_id=…`. Resources are added to the player's home spaceport planet.

### 3.10 Mining

Stationary fleets with mining capacity at a planet's tile mine resources each tick: `mined = mining_capacity · mining_efficiency`, distributed proportionally to the planet's current resource ratios. The mined resources are transferred to the player's spaceport planet.

### 3.11 Tick Order (per tick, in `services/tick.process_tick`)

1. Building upgrades that finished → increment level, +500 score.
2. Resource production from buildings → add to each planet.
3. Research that finished → increment level, +1000 score.
4. Fleet movements that arrived → update fleet position, clear `movement_end_time`.
5. Combat at each tile with ≥ 2 player fleets where ≥ 1 is aggressive.
6. Mining for stationary fleets at planet tiles.

## 4. API Reference

All endpoints are mounted under `/api`. Auth header: `Authorization: Bearer <jwt>`.

### 4.1 Auth (`routes/auth.py`)

| Method | Path                | Body / Notes                                    |
|--------|---------------------|--------------------------------------------------|
| POST   | `/register`         | `{ username, email, password, invite_code }`     |
| POST   | `/login`            | `{ username, password, is_admin?: bool }`        |
| GET    | `/me`               | Current user                                     |
| GET    | `/auth/session`     | Validates the bearer token, returns role         |

### 4.2 Game (`routes/game.py`)

| Method | Path                  | Notes                                       |
|--------|-----------------------|---------------------------------------------|
| GET    | `/game/state`         | `current_tick`, `next_tick_time`, `tick_duration`, `active_players`, `game_started` |
| POST   | `/game/observatory`   | `{ center_x, center_y }` → 7×7 view dict    |
| GET    | `/game/planets`       | Owned planets                               |
| GET    | `/game/rankings`      | Highscore list                              |
| POST   | `/game/tick`          | Manual tick (admin/debug)                   |

### 4.3 Buildings (`routes/buildings.py`)

| Method | Path                              | Notes                          |
|--------|-----------------------------------|--------------------------------|
| GET    | `/game/buildings`                 | Player's building levels + bonus |
| POST   | `/game/buildings/upgrade`         | `{ building_type }`            |
| GET    | `/game/building-types`            | Static catalog                 |

### 4.4 Ships & Spaceport (`routes/ships.py`)

| Method | Path                       | Notes                                          |
|--------|----------------------------|------------------------------------------------|
| POST   | `/game/ship-design`        | Create prototype                               |
| GET    | `/game/ship-designs`       | Player's designs                               |
| POST   | `/game/build-ships`        | `{ planet_id, design_id, quantity }`           |
| GET    | `/game/spaceport-ships`    | `{ [planet_key]: { planet_id, planet_name, position, ships:[…] } }` |
| GET    | `/game/component-levels`   | Available components grouped by drive/shield/weapon, per research level |

### 4.5 Fleets (`routes/fleets.py`)

| Method | Path                  | Notes                                           |
|--------|-----------------------|-------------------------------------------------|
| POST   | `/game/create-fleet`  | `{ planet_id, fleet_name, ships:[{design_id, quantity}] }` |
| GET    | `/game/fleets`        | Player's fleets                                 |
| POST   | `/game/move-fleet`    | `{ fleet_id, target_position:{x,y} }` (0..size-1) |
| POST   | `/game/fleet/stance`  | `{ fleet_id, stance: 'defensive' \| 'aggressive' }` |

### 4.6 Research (`routes/research.py`)

| Method | Path                   | Notes                                    |
|--------|------------------------|------------------------------------------|
| GET    | `/game/research`       | `{ research_levels:[{category, technology, level, researching, research_end_time}] }` |
| GET    | `/game/research/costs` | Per-category cost catalog                |
| POST   | `/game/research/start` | `{ category, technology }`               |

### 4.7 Combat (`routes/combat.py`)

| Method | Path                       | Notes                              |
|--------|----------------------------|------------------------------------|
| GET    | `/game/battle-reports`     | Player's recent reports            |
| GET    | `/game/debris-fields`      | Debris visible to the player       |
| POST   | `/game/collect-debris`     | Query `debris_id=…`                |

### 4.8 Admin (`routes/admin.py`)

| Method | Path                          | Notes                                               |
|--------|-------------------------------|-----------------------------------------------------|
| GET    | `/admin/stats`                | Players, planets, fleets, invite counters           |
| GET    | `/admin/config`               | Live `game_config` (no `admin_password` field)      |
| POST   | `/admin/config`               | Patch `game_config`                                  |
| GET    | `/admin/users`                | All users with planet/fleet counts                  |
| DELETE | `/admin/users/{user_id}`      | Delete a user and their entities                    |
| GET    | `/admin/invite-codes`         | All invite codes                                    |
| POST   | `/admin/invite-codes`         | `{ max_uses, expires_in_hours }`                    |
| POST   | `/admin/reset-game`           | Wipes players/planets/fleets, regenerates universe  |
| POST   | `/admin/new-round`            | `{ resources_per_planet, planet_count, universe_size, tick_duration, max_players }` |

## 5. MongoDB Collections

- `users` — `{ id, username, email, password_hash, spaceport_position:{x,y}, score, created_at, … }`
- `planets` — `{ id, name, position:{x,y}, planet_type, resources:{food,metal,hydrogen}, owner_id?, owner_username? }`
- `fleets` — `{ id, owner_id, owner_username, name, position:{x,y}, ships:[{design_id, quantity}], stance, fleet_speed, movement_end_time? }`
- `ship_designs` — per player; `{ id, owner_id, name, drive, shield, weapon, calculated_stats }`
- `spaceport_ships` — `{ id, owner_id, planet_id, design_id, design_name, quantity, created_at }`
- `buildings` — per player + `building_type`; `{ owner_id, building_type, level, upgrading, upgrade_end_time? }`
- `research` — `{ owner_id, research_levels:[{category, technology, level, researching, research_end_time?}] }`
- `battle_reports` — `{ id, tick, position, attacker_*, defender_*, winner, debris_created? }`
- `debris_fields` — `{ id, position, resource_type, amount }`
- `invite_codes` — `{ id, code, max_uses, current_uses, expires_at?, used_by_username? }`
- `game_config` — singleton `{ universe_size, tick_duration, max_players, mining_efficiency, colonization_time_hours, current_tick, last_tick_time, next_tick_time, game_started, … }`

Indexes are created in parallel at startup (see `backend/indexes.py`).

## 6. Environment

| Var                   | Required | Default                              | Notes                              |
|-----------------------|----------|--------------------------------------|------------------------------------|
| `MONGO_URL`           | no       | `mongodb://localhost:27017`          | Local Mongo started by `start.sh`  |
| `DB_NAME`             | no       | `thecreation_authentic`              |                                    |
| `SECRET_KEY`          | **yes**  | —                                    | 32+ bytes hex; JWT signing key. Server refuses to start if missing. |
| `ADMIN_PASSWORD`      | **yes**  | —                                    | Plaintext-equal compare for admin login. |
| `CORS_ORIGINS`        | no       | computed from REPL_DOMAIN if present | Comma-separated override.          |
| `REACT_APP_BACKEND_URL` | no     | unset                                | Leave unset in dev → frontend uses relative `/api` proxy. |

Secrets are managed via Replit Secrets (`environment-secrets` skill). Never log or print secret values.

## 7. Startup (`start.sh`)

1. Stops stale `uvicorn` / `react-scripts` / `node` dev processes from previous runs.
2. Starts MongoDB on `127.0.0.1:27017` if not already running. Data path is `${MONGO_DBPATH:-$HOME/.local/share/mongodb-data}` — **outside** the project so runtime state never gets committed (the previous in-repo `data/mongodb/` was removed; `data/`, `*.wt`, `WiredTiger*`, `journal/` are now in `.gitignore`).
3. Starts FastAPI via `uv run` on `127.0.0.1:8000`.
4. Starts React via `yarn start` on `0.0.0.0:5000` with `CI=true` (avoids interactive port prompts).

The single workflow `Start application` runs `bash start.sh`.

## 8. Package Management

- **Python:** `uv` with `pyproject.toml` / `uv.lock`. Add deps via the `package-management` skill.
- **Node:** `yarn` with `frontend/package.json` / `frontend/yarn.lock`. Use `yarn` (not `npm`).

## 9. Conventions for Future Agents

- **Time:** always use `app_config.utc_now()` (returns timezone-aware UTC). Never use `datetime.utcnow()` (deprecated, naive).
- **Game config reads:** call `services.config_cache.get_game_config()` at most once per request and pass the result down — it is cached in-memory and invalidated on writes.
- **DB calls:** services take `db` as their first argument; routes get `db` via `from database import db`.
- **Auth deps:** routes use `Depends(get_current_user)` for player endpoints and `Depends(require_admin)` for admin endpoints. Do not mix.
- **Frontend tabs:** are pure presentation. New player-side state or actions belong in `useGameData.js`; new admin actions belong in `AdminPanel.js`.
- **API base URL:** import `API` and `getAuthHeaders` from `frontend/src/lib/api.js`. Do not call `localStorage.getItem('token')` directly in components.
- **CRA + CRACO:** the frontend uses CRA via CRACO. Do not migrate to Vite without explicit user request.
- **Inputs:** the existing UI uses many uncontrolled inputs with DOM IDs (`fleet-${id}-x` etc.); preserve this pattern when editing existing tabs to avoid breaking the coordinate-prefill flow from Observatory → Spaceport.

## 10. Known Inactive UI

`GameInterface.js` still renders a `selectedField` info panel, but the field-click handler has only ever wired `setActiveTab('raumhafen')` and `setTargetCoordinates(...)` — `setSelectedField` is never called. The panel is effectively dead code preserved from the original implementation and is **not** a refactor regression. Do not remove it without explicit user approval; do not consider it broken.

## 11. Key Files Cheat-Sheet

- Backend entry: `backend/server.py`
- Backend lifecycle: `backend/lifespan.py`
- Game tick logic: `backend/services/tick.py`
- Combat: `backend/services/combat.py`
- Ship math: `backend/services/ships.py`
- Frontend entry: `frontend/src/App.js`
- Game shell: `frontend/src/components/game/GameInterface.js`
- Game data + actions: `frontend/src/hooks/useGameData.js`
- Admin shell: `frontend/src/components/AdminPanel.js`
- API client: `frontend/src/lib/api.js`
- Auth context: `frontend/src/context/AuthContext.js`
- Startup: `start.sh`
