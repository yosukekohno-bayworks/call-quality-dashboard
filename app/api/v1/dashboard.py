from fastapi import APIRouter

router = APIRouter()


@router.get("/summary")
async def get_dashboard_summary():
    return {"message": "Dashboard summary - not implemented"}


@router.get("/trends")
async def get_dashboard_trends():
    return {"message": "Dashboard trends - not implemented"}


@router.get("/rankings")
async def get_dashboard_rankings():
    return {"message": "Dashboard rankings - not implemented"}
