from fastapi import APIRouter, Depends

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    # dependencies=[Depends(get_current_active_user)] # Add auth later
)

@router.get("/")
async def list_users():
    return [{"username": "placeholder-admin"}]

# Add POST, GET /users/{user_id}, PUT, DELETE later
