from fastapi import APIRouter

router = APIRouter()


# Operation Flows
@router.get("/flows")
async def list_flows():
    return {"message": "List flows - not implemented"}


@router.post("/flows")
async def create_flow():
    return {"message": "Create flow - not implemented"}


@router.put("/flows/{flow_id}")
async def update_flow(flow_id: str):
    return {"message": f"Update flow {flow_id} - not implemented"}


@router.delete("/flows/{flow_id}")
async def delete_flow(flow_id: str):
    return {"message": f"Delete flow {flow_id} - not implemented"}


# Analysis Prompts
@router.get("/prompts")
async def list_prompts():
    return {"message": "List prompts - not implemented"}


@router.put("/prompts/{prompt_id}")
async def update_prompt(prompt_id: str):
    return {"message": f"Update prompt {prompt_id} - not implemented"}


# Biztel Settings
@router.get("/biztel")
async def get_biztel_settings():
    return {"message": "Get Biztel settings - not implemented"}


@router.put("/biztel")
async def update_biztel_settings():
    return {"message": "Update Biztel settings - not implemented"}


@router.post("/biztel/test")
async def test_biztel_connection():
    return {"message": "Test Biztel connection - not implemented"}
