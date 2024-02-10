from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr


from src.conf.config import config
from src.services.auth import auth_service


class EmailService:
    conf = ConnectionConfig(
        MAIL_USERNAME=config.MAIL_USERNAME,
        MAIL_PASSWORD=config.MAIL_PASSWORD,
        MAIL_FROM=config.MAIL_FROM,
        MAIL_PORT=config.MAIL_PORT,
        MAIL_SERVER=config.MAIL_SERVER,
        MAIL_FROM_NAME="FastContacts",
        MAIL_STARTTLS=False,
        MAIL_SSL_TLS=True,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
        TEMPLATE_FOLDER=config.BASE_DIR / "templates",
    )
    fm = FastMail(conf)

    async def send_verification_mail(
        self,
        username: EmailStr,
        host: str,
    ):
        try:
            token_verification = await auth_service.create_email_token({"sub": username})
            message = MessageSchema(
                subject="Confirm your email",
                recipients=[username],
                template_body={
                    "host": host,
                    "username": username,
                    "token": token_verification,
                },
                subtype=MessageType.html,
            )
            await self.fm.send_message(message, template_name="verify_email.html")
        except ConnectionErrors as err:
            print(err)

    async def send_request_to_reset_password(self, username: EmailStr, host: str):
        try:
            token_verification = await auth_service.create_email_token(
                {"sub": username}
            )
            message = MessageSchema(
                subject="Change user credentials",
                recipients=[username],
                template_body={
                    "host": host,
                    "username": username,
                    "token": token_verification,
                },
                subtype=MessageType.html,
            )
            await self.fm.send_message(message, template_name="reset_password.html")
        except ConnectionErrors as err:
            print(err)


email_service = EmailService()
