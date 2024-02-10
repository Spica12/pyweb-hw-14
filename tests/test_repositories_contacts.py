import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy import Date
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.contact import ContactModel
from src.models.users import UserModel
from src.repositories.contacts import ContactRepo
from src.schemas.contact import ContactCreateSchema


class TestAsyncContact(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.user = UserModel(
            id=1, username="user@example.com", password="string564123"
        )
        self.session = AsyncMock(spec=AsyncSession)

        self.contact1 = ContactModel(
            id=1,
            name="test_contact_name_1",
            surname="test_contact_surname_1",
            email="test_email_1@example.com",
            phone="00000000000",
            birthday=datetime(year=2001, month=5, day=7).date(),
            notes="test_notes",
            is_favorite=False,
            user=self.user,
        )
        self.contact2 = ContactModel(
            id=2,
            name="test_contact_name_2",
            surname="test_contact_surname_2",
            email="test_email_2@example.com",
            phone="11111111111",
            birthday=datetime(year=2007, month=4, day=9).date(),
            notes="test_notes_2",
            is_favorite=True,
            user=self.user,
        )

    async def test_get_all(self):
        limit = 10
        offset = 0
        contacts = [self.contact1, self.contact2]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts

        result = await ContactRepo(self.session).get_all(limit, offset, self.user)

        self.assertEqual(result, contacts)

    async def test_create(self):
        body = ContactCreateSchema(
            name="test_name_1",
            surname="test_surname_1",
            email="test_email_1",
            phone="132456789",
            birthday=datetime(year=2001, month=5, day=7).date(),
            notes="test_notes_1",
            is_favorite=True,
        )

        result = await ContactRepo(self.session).create(body, self.user)
        self.assertIsInstance(result, ContactModel)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.surname, body.surname)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.birthday, body.birthday)
        self.assertEqual(result.notes, body.notes)
        self.assertEqual(result.is_favorite, body.is_favorite)

    async def test_get_by_id(self):
        contact = self.contact1
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = contact
        self.session.execute.return_value = mocked_contact

        result = await ContactRepo(self.session).get_by_id(contact_id=1, user=self.user)
        self.assertIsInstance(result, ContactModel)
        self.assertEqual(result.name, contact.name)
        self.assertEqual(result.surname, contact.surname)
        self.assertEqual(result.email, contact.email)
        self.assertEqual(result.phone, contact.phone)
        self.assertEqual(result.birthday, contact.birthday)
        self.assertEqual(result.notes, contact.notes)
        self.assertEqual(result.is_favorite, contact.is_favorite)

    async def test_update(self):
        body = ContactCreateSchema(
            name="test_name_1",
            surname="test_surname_1",
            email="test_email_1",
            phone="132456789",
            birthday=datetime(year=2001, month=5, day=7).date(),
            notes="test_notes_1",
            is_favorite=True,
        )
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = self.contact1
        self.session.execute.return_value = mocked_contact

        result = await ContactRepo(self.session).update(
            contact_id=1, body=body, user=self.user
        )

        self.assertIsInstance(result, ContactModel)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.surname, body.surname)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.birthday, body.birthday)
        self.assertEqual(result.notes, body.notes)
        self.assertEqual(result.is_favorite, body.is_favorite)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once()

    async def test_delet(self):
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = self.contact2
        self.session.execute.return_value = mocked_contact
        result = await ContactRepo(self.session).delete(contact_id=1, user=self.user)
        self.session.delete.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertIsInstance(result, ContactModel)

    async def test_get_by_name(self):
        key_name = "test_user_1"
        contact = self.contact1
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contact
        self.session.execute.return_value = mocked_contacts

        result = await ContactRepo(self.session).get_by_name(
            key_name=key_name, user=self.user
        )

        self.assertIsInstance(result, ContactModel)
        self.assertEqual(result.name, contact.name)
        self.assertEqual(result.surname, contact.surname)
        self.assertEqual(result.email, contact.email)
        self.assertEqual(result.phone, contact.phone)
        self.assertEqual(result.birthday, contact.birthday)
        self.assertEqual(result.notes, contact.notes)
        self.assertEqual(result.is_favorite, contact.is_favorite)

    async def test_get_by_surname(self):
        key_name = "test_surname_1"
        contact = self.contact1
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contact
        self.session.execute.return_value = mocked_contacts

        result = await ContactRepo(self.session).get_by_name(
            key_name=key_name, user=self.user
        )

        self.assertIsInstance(result, ContactModel)
        self.assertEqual(result.name, contact.name)
        self.assertEqual(result.surname, contact.surname)
        self.assertEqual(result.email, contact.email)
        self.assertEqual(result.phone, contact.phone)
        self.assertEqual(result.birthday, contact.birthday)
        self.assertEqual(result.notes, contact.notes)
        self.assertEqual(result.is_favorite, contact.is_favorite)

    async def test_get_by_email(self):
        key_name = "test_email_1"
        contact = self.contact1
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contact
        self.session.execute.return_value = mocked_contacts

        result = await ContactRepo(self.session).get_by_name(
            key_name=key_name, user=self.user
        )

        self.assertIsInstance(result, ContactModel)
        self.assertEqual(result.name, contact.name)
        self.assertEqual(result.surname, contact.surname)
        self.assertEqual(result.email, contact.email)
        self.assertEqual(result.phone, contact.phone)
        self.assertEqual(result.birthday, contact.birthday)
        self.assertEqual(result.notes, contact.notes)
        self.assertEqual(result.is_favorite, contact.is_favorite)

    async def test_get_upcoming_birthday(self):
        limit = 10
        offset = 0
        contacts = [self.contact1, self.contact2]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts

        result = await ContactRepo(self.session).get_all(limit, offset, self.user)

        self.assertEqual(result, contacts)
