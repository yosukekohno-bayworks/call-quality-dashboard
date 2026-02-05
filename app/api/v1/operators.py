from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_operators():
    return {"message": "List operators - not implemented"}


@router.get("/{operator_id}")
async def get_operator(operator_id: str):
    return {"message": f"Get operator {operator_id} - not implemented"}


@router.get("/{operator_id}/stats")
async def get_operator_stats(operator_id: str):
    return {"message": f"Get operator stats {operator_id} - not implemented"}
