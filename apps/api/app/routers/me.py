from fastapi import APIRouter, Depends

from app.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/me", tags=["me"])


@router.get("")
async def get_me(user: CurrentUser = Depends(get_current_user)) -> dict:
    return {"id": user.id, "clerk_id": user.clerk_id, "email": user.email}
