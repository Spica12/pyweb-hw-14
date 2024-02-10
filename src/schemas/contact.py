from datetime import date

from pydantic import BaseModel, ConfigDict


class ContactSchema(BaseModel):
    id: int
    name: str
    surname: str
    email: str
    phone: str
    birthday: date
    notes: str
    is_favorite: bool

    cmodel_config = ConfigDict(from_attributes = True)


class ContactCreateSchema(BaseModel):
    name: str
    surname: str
    email: str
    phone: str
    birthday: date
    notes: str
    is_favorite: bool = False
