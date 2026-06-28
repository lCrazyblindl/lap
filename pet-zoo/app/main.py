from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import storage
from app.models import AnimalSpecies
from app.routers.animals import router as animals_router
from app.routers.species import build_species_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage.ensure_seeded()
    yield


app = FastAPI(title="pet-zoo", description="A small zoo management API", lifespan=lifespan)

for species in AnimalSpecies:
    app.include_router(build_species_router(species))

app.include_router(animals_router)
