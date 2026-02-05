from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
async def get_current_tenant():
    return {"message": "Get current tenant - not implemented"}


@router.put("/me")
async def update_current_tenant():
    return {"message": "Update current tenant - not implemented"}
