from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.database import get_db
from src.models.users import UserModel
from src.schemas.contact import ContactCreateSchema, ContactSchema
from src.services.auth import auth_service
from src.services.contact import ContactService

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get(
    "/",
    response_model=list[ContactSchema],
    dependencies=[Depends(RateLimiter(times=3, seconds=20))],
)
async def get_all_contacts(
    limit: int = Query(default=10, ge=10, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(auth_service.get_current_user),
):
    contacts = await ContactService(db=db).get_all_contacts(
        limit=limit, offset=offset, user=user
    )

    return contacts


@router.get("/id/{contact_id}", response_model=ContactSchema)
async def get_contact_by_id(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(auth_service.get_current_user),
):
    contact = await ContactService(db=db).get_by_id(contact_id, user)

    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    return contact


@router.get("/key_word/{key_word}", response_model=list[ContactSchema])
async def find_contacts(
    key_word: str = Path(..., title="Key word"),
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(auth_service.get_current_user),
):
    contact = await ContactService(db=db).find_contacts(key_word, user)

    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    return contact


@router.post(
    "/",
    response_model=ContactSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=3, seconds=20))],
)
async def create_contact(
    body: ContactCreateSchema,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(auth_service.get_current_user),
):
    contact = await ContactService(db=db).create_contact(body, user)

    return contact


@router.put("/{contact_id}", response_model=ContactSchema)
async def update_contact(
    contact_id: int,
    body: ContactCreateSchema,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(auth_service.get_current_user),
):
    contact = await ContactService(db=db).update_contact(contact_id, body, user)

    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(auth_service.get_current_user),
):
    contact = await ContactService(db=db).delete_contact(contact_id, user)

    return contact


@router.get("/birthday", response_model=list[ContactSchema])
async def upcoming_birthday(
    limit: int = Query(default=10, ge=10, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(auth_service.get_current_user),
):
    contacts = await ContactService(db=db).get_upcoming_birthday(
        limit=limit, offset=offset, user=user
    )

    return contacts
