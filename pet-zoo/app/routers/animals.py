from fastapi import APIRouter

from app import storage
from app.models import Animal

router = APIRouter(tags=["Animals"])


@router.get("/animals", response_model=list[Animal], summary="List all animals across every species")
def list_all_animals() -> list[Animal]:
    return storage.list_all()
