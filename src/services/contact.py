from sqlalchemy.ext.asyncio import AsyncSession

from src.models.users import UserModel
from src.repositories.contacts import ContactRepo
from src.schemas.contact import ContactCreateSchema, ContactSchema


class ContactService:
    def __init__(self, db: AsyncSession):
        """
        The __init__ function is called when the class is instantiated.
        It's used to initialize variables and do other setup tasks that need to be done every time an object of this class is created.

        :param self: Represent the instance of the class
        :param db: AsyncSession: Create a connection to the database
        :return: Nothing
        """
        self.repo = ContactRepo(db=db)

    async def get_all_contacts(self, limit: int, offset: int, user: UserModel):
        """
        The get_all_contacts function returns all contacts from the database.
                Args:
                    limit (int): The maximum number of contacts to return.
                    offset (int): The starting point for the query, used for pagination.
                    user (UserModel): A UserModel object representing a user in the database.
                Returns:
                    list[Contact]: A list of Contact objects representing all contacts in the database.

        :param self: Represent the instance of the class
        :param limit: int: Limit the number of contacts returned from the database
        :param offset: int: Specify the number of records to skip
        :param user: UserModel: Get the user id from the database
        :return: All contacts from the database
        """
        all_contacts_from_db = await self.repo.get_all(
            limit=limit,
            offset=offset,
            user=user,
        )

        return all_contacts_from_db

    async def get_by_id(self, contact_id, user: UserModel):
        """
        The get_by_id function returns a contact by its id.
            Args:
                contact_id (int): The id of the contact to be returned.
                user (UserModel): The user who is requesting the data.
            Returns:
                ContactModel: A single ContactModel object that matches the given id and belongs to the given user.

        :param self: Represent the instance of a class
        :param contact_id: Get the contact by id
        :param user: UserModel: Get the user_id from the usermodel class
        :return: A contact
        """
        contact = await self.repo.get_by_id(contact_id, user)

        return contact

    async def create_contact(self, body: ContactCreateSchema, user: UserModel):
        """
        The create_contact function creates a new contact.
            Args:
                body (ContactCreateSchema): The schema for the request body.
                user (UserModel): The current user making the request.

        :param self: Represent the instance of the class
        :param body: ContactCreateSchema: Validate the data that is passed in
        :param user: UserModel: Identify the user who is creating the contact
        :return: The contact object
        """
        contact = await self.repo.create(body, user)

        return contact

    async def update_contact(self, contact_id, body, user: UserModel):
        """
        The update_contact function updates a contact in the database.
            Args:
                contact_id (int): The id of the contact to update.
                body (dict): A dictionary containing all of the fields that need to be updated for this user.
                    Example: {'first_name': 'John', 'last_name': 'Doe'}
                user (UserModel): The current logged in user, used for authorization purposes only.

        :param self: Represent the instance of a class
        :param contact_id: Identify the contact to be updated
        :param body: Update the contact
        :param user: UserModel: Get the user_id from the user object
        :return: The contact object
        """
        contact = await self.repo.update(contact_id, body, user)

        return contact

    async def delete_contact(self, contact_id, user: UserModel):
        """
        The delete_contact function deletes a contact from the database.
            Args:
                contact_id (int): The id of the contact to delete.
                user (UserModel): The user who is deleting this contact.
            Returns:
                ContactModel: A model representing the deleted Contact.

        :param self: Represent the instance of a class
        :param contact_id: Identify the contact that is to be deleted
        :param user: UserModel: Pass the user object to the repo layer
        :return: The contact that was deleted
        """
        contact = await self.repo.delete(contact_id, user=user)

        return contact

    async def find_contacts(self, key_word: str, user: UserModel):
        """
        The find_contacts function searches for contacts by name, surname and email.


        :param self: Represent the instance of the class
        :param key_word: str: Search for the contacts by name, surname or email
        :param user: UserModel: Get the user's contacts
        :return: A list of contacts
        """
        contacts = set()

        contacts_by_name = await self.repo.get_by_name(key_word, user)
        contacts.update(contacts_by_name)

        contacts_by_surname = await self.repo.get_by_surname(key_word, user)
        contacts.update(contacts_by_surname)

        contacts_by_email = await self.repo.get_by_email(key_word, user)
        contacts.update(contacts_by_email)

        return list(contacts)

    async def get_upcoming_birthday(self, limit: int, offset: int, user: UserModel):
        """
        The get_upcoming_birthday function returns a list of contacts with upcoming birthdays.


        :param self: Represent the instance of the class
        :param limit: int: Limit the number of contacts returned
        :param offset: int: Skip the first n records
        :param user: UserModel: Get the user id from the usermodel class
        :return: A list of contacts with upcoming birthdays
        """
        contacts = await self.repo.get_upcoming_birthday(limit=limit, offset=offset, user=user)

        return contacts
