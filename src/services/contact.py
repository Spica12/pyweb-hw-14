from sqlalchemy.ext.asyncio import AsyncSession

from src.models.users import UserModel
from src.repositories.contacts import ContactRepo
from src.schemas.contact import ContactCreateSchema, ContactSchema


class ContactService:
    def __init__(self, db: AsyncSession):
        self.repo = ContactRepo(db=db)

    async def get_all_contacts(self, limit: int, offset: int, user: UserModel):
        all_contacts_from_db = await self.repo.get_all(
            limit=limit,
            offset=offset,
            user=user,
        )

        return all_contacts_from_db

    async def get_by_id(self, contact_id, user: UserModel):
        contact = await self.repo.get_by_id(contact_id, user)

        return contact

    async def create_contact(self, body: ContactCreateSchema, user: UserModel):
        contact = await self.repo.create(body, user)

        return contact

    async def update_contact(self, contact_id, body, user: UserModel):
        contact = await self.repo.update(contact_id, body, user)

        return contact

    async def delete_contact(self, contact_id, user: UserModel):
        contact = await self.repo.delete(contact_id, user=user)

        return contact

    async def find_contacts(self, key_word: str, user: UserModel):
        contacts = set()

        contacts_by_name = await self.repo.get_by_name(key_word, user)
        contacts.update(contacts_by_name)

        contacts_by_surname = await self.repo.get_by_surname(key_word, user)
        contacts.update(contacts_by_surname)

        contacts_by_email = await self.repo.get_by_email(key_word, user)
        contacts.update(contacts_by_email)

        return list(contacts)

    async def get_upcoming_birthday(self, limit: int, offset: int, user: UserModel):
        contacts = await self.repo.get_upcoming_birthday(limit=limit, offset=offset, user=user)

        return contacts
