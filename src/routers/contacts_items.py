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
    """
    The get_all_contacts function returns a list of contacts for the current user.

    :param limit: int: Limit the number of contacts returned
    :param ge: Set a minimum value for the limit parameter
    :param le: Limit the number of contacts returned to 500
    :param offset: int: Determine how many contacts to skip
    :param ge: Specify a minimum value for the parameter
    :param db: AsyncSession: Pass in the database session
    :param user: UserModel: Get the current user from the database
    :param : Limit the number of contacts returned by the function
    :return: The following:
    """
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
    """
    The get_contact_by_id function returns a contact by its id.

    :param contact_id: int: Specify the id of the contact we want to retrieve
    :param db: AsyncSession: Pass the database session to the contactservice
    :param user: UserModel: Get the current user from the request
    :param : Get the contact_id from the url
    :return: A contactmodel object
    """
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
    """
    The find_contacts function is used to find contacts in the database.
        It takes a key_word and returns all contacts that match the key_word.


    :param key_word: str: Get the key word from the request body
    :param title: Provide a description of the parameter in the openapi documentation
    :param db: AsyncSession: Get the database connection
    :param user: UserModel: Get the current user from the database
    :param : Pass the key word to search for a contact
    :return: A list of contacts
    """
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
    """
    The create_contact function creates a new contact.
        ---
        post:
          tags: [contacts]
          summary: Creates a new contact.
          description: Creates a new contact and returns the created object.
          requestBody:
            required: true
            content:{application/json}:{schema}ContactCreateSchema{/schema}

    :param body: ContactCreateSchema: Validate the request body against the contactcreateschema schema
    :param db: AsyncSession: Pass the database session to the service layer
    :param user: UserModel: Get the current user from the database
    :param : Get the current user
    :return: A contactmodel object
    """
    contact = await ContactService(db=db).create_contact(body, user)

    return contact


@router.put("/{contact_id}", response_model=ContactSchema)
async def update_contact(
    contact_id: int,
    body: ContactCreateSchema,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(auth_service.get_current_user),
):
    """
    The update_contact function updates a contact in the database.
        Args:
            contact_id (int): The id of the contact to update.
            body (ContactCreateSchema): A schema containing all fields that can be updated for a ContactModel object.
                See ContactCreateSchema for more details on what fields are required and optional, as well as their types and formats.
            db (AsyncSession, optional): An async session with an open connection to the database; defaults to Depends(get_db).
                This is used by SQLAlchemy's ORM layer when querying

    :param contact_id: int: Specify the contact to update
    :param body: ContactCreateSchema: Validate the request body
    :param db: AsyncSession: Pass the database connection to the service
    :param user: UserModel: Get the current user from the auth_service
    :param : Get the contact id
    :return: A contactmodel object
    """
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
    """
    The delete_contact function deletes a contact from the database.

    The delete_contact function takes in a contact_id and uses it to find the
    corresponding ContactModel object in the database. It then deletes that object,
    and returns it as JSON.

    :param contact_id: int: Get the contact id from the url path
    :param db: AsyncSession: Pass the database connection to the service class
    :param user: UserModel: Get the current user from the database
    :param : Get the contact id from the url
    :return: A contactmodel object
    """
    contact = await ContactService(db=db).delete_contact(contact_id, user)

    return contact


@router.get("/birthday", response_model=list[ContactSchema])
async def upcoming_birthday(
    limit: int = Query(default=10, ge=10, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(auth_service.get_current_user),
):
    """
    The upcoming_birthday function returns a list of contacts with upcoming birthdays.

    :param limit: int: Set the limit of contacts to be returned
    :param ge: Specify a minimum value
    :param le: Limit the number of contacts returned
    :param offset: int: Skip a number of records
    :param ge: Specify the minimum value of a parameter
    :param db: AsyncSession: Pass the database session to the contactservice
    :param user: UserModel: Get the current user
    :param : Get the limit of contacts to be returned
    :return: A list of contacts
    """
    contacts = await ContactService(db=db).get_upcoming_birthday(
        limit=limit, offset=offset, user=user
    )

    return contacts
