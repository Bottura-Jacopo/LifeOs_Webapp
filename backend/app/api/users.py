from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.schemas.user import UserOut
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user