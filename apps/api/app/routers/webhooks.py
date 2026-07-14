import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user

router = APIRouter()


@router.get("/")
async def list_webhooks(user: Any = Depends(get_current_user)) -> dict[str, Any]:
    return {"webhooks": [], "total": 0}


@router.post("/", status_code=201)
async def create_webhook(user: Any = Depends(get_current_user)) -> dict[str, Any]:
    return {"status": "not_implemented"}


@router.get("/{webhook_id}")
async def get_webhook(
    webhook_id: uuid.UUID, user: Any = Depends(get_current_user)
) -> dict[str, Any]:
    return {"status": "not_implemented"}


@router.put("/{webhook_id}")
async def update_webhook(
    webhook_id: uuid.UUID, user: Any = Depends(get_current_user)
) -> dict[str, Any]:
    return {"status": "not_implemented"}


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: uuid.UUID, user: Any = Depends(get_current_user)
) -> None:
    return None
