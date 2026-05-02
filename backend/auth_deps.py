"""FastAPI dependencies for authentication and authorization."""

from fastapi import Depends, HTTPException

from database import db
from models import User
from security import decode_token, security


async def get_current_user(credentials=Depends(security)) -> User:
    payload = decode_token(credentials)
    username = payload.get("sub")
    if username is None or payload.get("admin"):
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await db.users.find_one({"username": username})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user)


async def require_admin(credentials=Depends(security)) -> dict:
    """Validate the bearer token and enforce the admin flag."""
    payload = decode_token(credentials)
    if not payload.get("admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload
