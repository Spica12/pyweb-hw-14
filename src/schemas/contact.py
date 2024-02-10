from datetime import date

from pydantic import BaseModel


class ContactSchema(BaseModel):
    id: int
    name: str
    surname: str
    email: str
    phone: str
    birthday: date
    notes: str
    is_favorite: bool

    class Config:
        # orm_mode = True
        from_attributes = True


class ContactCreateSchema(BaseModel):
    name: str
    surname: str
    email: str
    phone: str
    birthday: date
    notes: str
    is_favorite: bool = False
