import json
from pathlib import Path

from app.models import Animal, AnimalSpecies, AnimalWrite

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "zoo.json"


def _empty_state() -> dict:
    return {
        "next_id": 1,
        "animals": {species.value: [] for species in AnimalSpecies},
    }


def ensure_seeded() -> None:
    if not DATA_PATH.exists():
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        _save(_empty_state())


def _load() -> dict:
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _record_to_animal(species: AnimalSpecies, record: dict) -> Animal:
    return Animal(species=species, **record)


def list_by_species(species: AnimalSpecies) -> list[Animal]:
    data = _load()
    return [_record_to_animal(species, r) for r in data["animals"][species.value]]


def get_by_id(species: AnimalSpecies, animal_id: int) -> Animal | None:
    data = _load()
    for record in data["animals"][species.value]:
        if record["id"] == animal_id:
            return _record_to_animal(species, record)
    return None


def create(species: AnimalSpecies, payload: AnimalWrite) -> Animal:
    data = _load()
    animal_id = data["next_id"]
    data["next_id"] += 1
    record = {"id": animal_id, **payload.model_dump()}
    data["animals"][species.value].append(record)
    _save(data)
    return _record_to_animal(species, record)


def update(species: AnimalSpecies, animal_id: int, payload: AnimalWrite) -> Animal | None:
    data = _load()
    records = data["animals"][species.value]
    for index, record in enumerate(records):
        if record["id"] == animal_id:
            updated_record = {"id": animal_id, **payload.model_dump()}
            records[index] = updated_record
            _save(data)
            return _record_to_animal(species, updated_record)
    return None


def delete(species: AnimalSpecies, animal_id: int) -> bool:
    data = _load()
    records = data["animals"][species.value]
    for index, record in enumerate(records):
        if record["id"] == animal_id:
            del records[index]
            _save(data)
            return True
    return False


def list_all() -> list[Animal]:
    data = _load()
    animals: list[Animal] = []
    for species in AnimalSpecies:
        animals.extend(_record_to_animal(species, r) for r in data["animals"][species.value])
    return animals
