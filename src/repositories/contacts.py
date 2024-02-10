from datetime import datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.contact import ContactModel
from src.models.users import UserModel
from src.schemas.contact import ContactCreateSchema, ContactSchema


class ContactRepo:
    def __init__(self, db):
        """
        The __init__ function is called when the class is instantiated.
        It sets up the database connection and creates a new session for each request.

        :param self: Represent the instance of the class
        :param db: Connect to the database
        :return: Nothing
        """
        self.db: AsyncSession = db

    async def get_all(self, limit: int, offset: int, user: UserModel):
        """
        The get_all function returns all contacts for a given user.


        :param self: Represent the instance of the class
        :param limit: int: Limit the number of contacts returned
        :param offset: int: Specify the number of rows to skip
        :param user: UserModel: Filter the contacts by user
        :return: A list of contactmodel objects
        """
        stmt = select(ContactModel).filter_by(user=user).offset(offset).limit(limit)
        contacts = await self.db.execute(stmt)

        return contacts.scalars().all()

    async def create(self, body: ContactCreateSchema, user: UserModel):
        """
        The create function creates a new contact.
                ---
                tags: [contacts]

        :param self: Represent the instance of the class
        :param body: ContactCreateSchema: Validate the data sent by the user
        :param user: UserModel: Get the user id from the database and store it in the contact table
        :return: A contact
        """
        contact = ContactModel(**body.model_dump(exclude_unset=True), user=user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)

        return contact

    async def get_by_id(self, contact_id: int, user: UserModel):
        """
        The get_by_id function returns a contact by its id.
            Args:
                contact_id (int): The id of the contact to be returned.
                user (UserModel): The user who owns the requested contact.

        :param self: Represent the instance of a class
        :param contact_id: int: Filter the contacts by id
        :param user: UserModel: Check if the user is allowed to access the contact
        :return: A contact object
        """
        stmt = select(ContactModel).filter_by(id=contact_id, user=user)
        contacts = await self.db.execute(stmt)

        return contacts.scalar_one_or_none()

    async def update(self, contact_id: int, body: ContactCreateSchema, user: UserModel):
        """
        The update function updates a contact in the database.
            Args:
                contact_id (int): The id of the contact to update.
                body (ContactCreateSchema): A schema containing all fields that can be updated for a given user's contacts.
                    This is used to validate and deserialize the request body into an object we can use in our function logic.
                    See ContactCreateSchema for more details on what this schema looks like and how it works under-the-hood!

        :param self: Represent the instance of the class
        :param contact_id: int: Identify the contact that will be updated
        :param body: ContactCreateSchema: Validate the data sent in the request body
        :param user: UserModel: Get the user id from the token
        :return: The contact object
        """
        stmt = select(ContactModel).filter_by(id=contact_id, user=user)
        result = await self.db.execute(stmt)
        contact = result.scalar_one_or_none()

        if contact:
            contact.name = body.name
            contact.surname = body.surname
            contact.email = body.email
            contact.phone = body.phone
            contact.birthday = body.birthday
            contact.notes = body.notes
            contact.is_favorite = body.is_favorite
            await self.db.commit()
            await self.db.refresh(contact)

        return contact

    async def delete(self, contact_id: int, user: UserModel):
        """
        The delete function deletes a contact from the database.

        :param self: Represent the instance of the class
        :param contact_id: int: Specify the id of the contact to be deleted
        :param user: UserModel: Make sure that the user is deleting their own contact
        :return: The contact that was deleted
        """
        stmt = select(ContactModel).filter_by(id=contact_id, user=user)
        result = await self.db.execute(stmt)
        contact = result.scalar_one_or_none()
        if contact:
            await self.db.delete(contact)
            await self.db.commit()

        return contact

    async def get_by_name(self, key_name: str, user: UserModel):
        """
        The get_by_name function is used to search for a contact by name.
            The function takes in the key_name and user as parameters.
            It then uses SQLAlchemy's select() method to query the database,
            filtering by user and using LOWER(name) LIKE LOWER(:key_name) as a condition.

        :param self: Represent the instance of the class
        :param key_name: str: Filter the contacts by name
        :param user: UserModel: Filter the results by user
        :return: A list of objects
        """
        stmt = (
            select(ContactModel)
            .filter_by(user=user)
            .where(text("LOWER(name) LIKE LOWER(:key_name)"))
            .params(key_name=f"%{key_name}%")
        )
        result = await self.db.execute(stmt)

        return result.scalars().all()

    async def get_by_surname(self, key_surname: str, user: UserModel):
        """
        The get_by_surname function is used to search for contacts by surname.
            Args:
                key_surname (str): The surname of the contact you are searching for.
                user (UserModel): The user who owns the contact you are searching for.

        :param self: Represent the instance of the class
        :param key_surname: str: Get the surname from the user
        :param user: UserModel: Filter the contacts by user
        :return: A list of contacts that match the surname
        """
        stmt = (
            select(ContactModel)
            .filter_by(user=user)
            .where(text("LOWER(surname) LIKE LOWER(:key_name)"))
            .params(key_name=f"%{key_surname}%")
        )
        result = await self.db.execute(stmt)

        return result.scalars().all()

    async def get_by_email(self, key_email: str, user: UserModel):
        """
        The get_by_email function is used to search for a contact by email.
            The function takes in the key_email and user parameters, which are then used to query the database.
            If there is a match, it returns all of the contacts that match.

        :param self: Make the function an instance method
        :param key_email: str: Filter the results
        :param user: UserModel: Filter the contacts by user
        :return: A list of contacts
        """
        stmt = (
            select(ContactModel)
            .filter_by(user=user)
            .where(text("LOWER(email) LIKE LOWER(:key_name)"))
            .params(key_name=f"%{key_email}%")
        )
        result = await self.db.execute(stmt)

        return result.scalars().all()

    async def get_upcoming_birthday(self, limit: int, offset: int, user: UserModel):
        """
        The get_upcoming_birthday function returns a list of contacts with birthdays in the next week.

        :param self: Represent the instance of the class
        :param limit: int: Limit the number of results returned
        :param offset: int: Skip the number of contacts specified by offset
        :param user: UserModel: Filter the contacts by user
        :return: A list of contact objects
        """
        today = datetime.now().date()
        next_week = today + timedelta(days=7)
        stmt = (
            select(ContactModel)
            .filter_by(user=user)
            .where(ContactModel.birthday.between(today, next_week))
            .offset(offset)
            .limit(limit)
        )
        upcoming_birthdays = await self.db.execute(stmt)

        return upcoming_birthdays.scalars().all()
