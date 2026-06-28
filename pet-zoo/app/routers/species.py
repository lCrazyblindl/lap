from fastapi import APIRouter, HTTPException, status

from app import storage
from app.models import Animal, AnimalSpecies, AnimalWrite


def build_species_router(species: AnimalSpecies) -> APIRouter:
    plural = f"{species.value}s"
    article = "an" if species.value[0] in "aeiou" else "a"
    router = APIRouter(prefix=f"/{plural}", tags=[plural.capitalize()])

    @router.get("", response_model=list[Animal], summary=f"List all {plural}")
    def list_animals() -> list[Animal]:
        return storage.list_by_species(species)

    @router.get("/{animal_id}", response_model=Animal, summary=f"Get {article} {species.value} by id")
    def get_animal(animal_id: int) -> Animal:
        animal = storage.get_by_id(species, animal_id)
        if animal is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"{species.value} {animal_id} not found")
        return animal

    @router.post(
        "",
        response_model=Animal,
        status_code=status.HTTP_201_CREATED,
        summary=f"Create a new {species.value}",
    )
    def create_animal(payload: AnimalWrite) -> Animal:
        return storage.create(species, payload)

    @router.put("/{animal_id}", response_model=Animal, summary=f"Replace {article} {species.value} by id")
    def update_animal(animal_id: int, payload: AnimalWrite) -> Animal:
        animal = storage.update(species, animal_id, payload)
        if animal is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"{species.value} {animal_id} not found")
        return animal

    @router.delete(
        "/{animal_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary=f"Delete {article} {species.value} by id",
    )
    def delete_animal(animal_id: int) -> None:
        if not storage.delete(species, animal_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"{species.value} {animal_id} not found")

    return router
