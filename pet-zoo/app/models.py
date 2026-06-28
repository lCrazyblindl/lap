from enum import Enum

from pydantic import BaseModel, Field


class AnimalSpecies(str, Enum):
    monkey = "monkey"
    lion = "lion"
    tiger = "tiger"
    elephant = "elephant"


class AnimalGender(str, Enum):
    male = "male"
    female = "female"


class AnimalWrite(BaseModel):
    name: str = Field(min_length=1)
    age: int = Field(ge=0)
    gender: AnimalGender


class Animal(AnimalWrite):
    id: int
    species: AnimalSpecies
