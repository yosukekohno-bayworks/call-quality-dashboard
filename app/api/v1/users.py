from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_users():
    return {"message": "List users - not implemented"}


@router.post("")
async def create_user():
    return {"message": "Create user - not implemented"}


@router.get("/{user_id}")
async def get_user(user_id: str):
    return {"message": f"Get user {user_id} - not implemented"}


@router.put("/{user_id}")
async def update_user(user_id: str):
    return {"message": f"Update user {user_id} - not implemented"}


@router.delete("/{user_id}")
async def delete_user(user_id: str):
    return {"message": f"Delete user {user_id} - not implemented"}
