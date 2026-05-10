from fastapi import APIRouter

router = APIRouter()

@router.post("/token")
def create_bootstrap_token():
    return {"token": "todo-generate-token"}
