from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_calls():
    return {"message": "List calls - not implemented"}


@router.get("/{call_id}")
async def get_call(call_id: str):
    return {"message": f"Get call {call_id} - not implemented"}


@router.post("/upload")
async def upload_call():
    return {"message": "Upload call - not implemented"}


@router.get("/{call_id}/analysis")
async def get_call_analysis(call_id: str):
    return {"message": f"Get call analysis {call_id} - not implemented"}


@router.post("/{call_id}/reanalyze")
async def reanalyze_call(call_id: str):
    return {"message": f"Reanalyze call {call_id} - not implemented"}
