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
        """
        The send_verification_mail function sends a verification email to the user's email address.
            The function takes in two parameters: username and host.
            The username parameter is the user's email address, which is used as both the recipient of
            the verification mail and as part of a token that will be sent with it.

            The host parameter is used to create an absolute URL for use in verifying that a user has
            clicked on their verification link.

        :param self: Represent the instance of the class
        :param username: EmailStr: Pass in the user's email address
        :param host: str: Generate the link to verify the email
        :param : Create a token for the user
        :return: A message
        """
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
        """
        The send_request_to_reset_password function sends a request to reset the password of a user.
            Args:
                username (str): The email address of the user who wants to reset their password.
                host (str): The hostname where this service is running, e.g., &quot;localhost&quot; or &quot;127.0.0.2&quot;.

        :param self: Represent the instance of the class
        :param username: EmailStr: Specify the username of the user who is requesting to reset their password
        :param host: str: Pass the hostname of the server to send_request_to_reset_password function
        :return: A token_verification
        """
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
