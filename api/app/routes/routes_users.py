from fastapi import APIRouter, Depends, HTTPException
from app.auth.cognito_jwt import get_current_user
from app.controllers.controllers_users import get_user_profile

router = APIRouter()


@router.get("/users/me", response_model=dict)
async def read_current_user(current_user: dict = Depends(get_current_user)):
    """
    Returns the raw claims from the validated Cognito JWT.
    """
    return {"claims": current_user}


@router.post("/users/sync-profile", response_model=dict)
async def sync_user_profile(current_user: dict = Depends(get_current_user)):
    """
    On first login, this creates a user profile in the local database.
    On subsequent logins, it fetches the existing profile.
    """
    try:
        profile = await get_user_profile(current_user)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
