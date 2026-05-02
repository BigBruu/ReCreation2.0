from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException

from app_config import ACCESS_TOKEN_EXPIRE_MINUTES, utc_now
from auth_deps import get_current_user
from database import db
from models import InviteCode, Token, User, UserCreateWithInvite, UserLogin
from security import create_access_token, decode_token, pwd_context, security
from services.config_cache import get_game_config
from services.research import init_user_research
from services.spaceport import assign_spaceport_to_user

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=Token)
async def register(user_data: UserCreateWithInvite):
    invite_code_doc = await db.invite_codes.find_one({"code": user_data.invite_code})
    if not invite_code_doc:
        raise HTTPException(status_code=400, detail="Invalid invite code")

    invite = InviteCode(**invite_code_doc)
    if invite.expires_at and invite.expires_at < utc_now():
        raise HTTPException(status_code=400, detail="Invite code has expired")
    if invite.current_uses >= invite.max_uses:
        raise HTTPException(status_code=400, detail="Invite code has been used up")

    if await db.users.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]}):
        raise HTTPException(status_code=400, detail="Username or email already exists")

    config = await get_game_config()
    if await db.users.count_documents({}) >= config.max_players:
        raise HTTPException(status_code=400, detail=f"Maximum {config.max_players} players reached")

    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=pwd_context.hash(user_data.password),
    )
    await db.users.insert_one(user.dict())
    await db.invite_codes.update_one(
        {"id": invite.id},
        {"$set": {
            "used_by_user_id": user.id,
            "used_by_username": user.username,
            "used_at": utc_now(),
        }, "$inc": {"current_uses": 1}},
    )

    await init_user_research(user.id)
    await assign_spaceport_to_user(db, user.id, user.username)

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"username": user_data.username})
    if not user or not pwd_context.verify(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user["spaceport_position"]["x"] == -1:
        await assign_spaceport_to_user(db, user["id"], user["username"])
    await init_user_research(user["id"])

    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/auth/session")
async def get_auth_session(credentials=Depends(security)):
    payload = decode_token(credentials)
    is_admin = bool(payload.get("admin"))
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    if not is_admin:
        if not await db.users.find_one({"username": username}):
            raise HTTPException(status_code=401, detail="User not found")
    return {"username": username, "admin": is_admin}
