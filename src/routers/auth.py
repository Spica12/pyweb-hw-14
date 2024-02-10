from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Security,
    BackgroundTasks,
    Request,
    status,
)
from fastapi.responses import RedirectResponse
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.database import get_db
from src.schemas.user import (
    TokenSchema,
    UserCreateSchema,
    UserReadSchema,
    UserResetPasswordSchema,
)
from src.services.auth import auth_service
from src.services.email import email_service

router = APIRouter(prefix="/auth", tags=["auth"])
get_refresh_token = HTTPBearer()


@router.post(
    "/signup", response_model=UserReadSchema, status_code=status.HTTP_201_CREATED
)
async def signup(
    body: UserCreateSchema,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
    dependencies=[Depends(RateLimiter(times=1, seconds=20))],
):
    """
    The signup function creates a new user in the database.
        It also sends an email to the user with a link to verify their account.
        The function takes in three arguments: body, background_tasks, and request.

    :param body: UserCreateSchema: Validate the request body
    :param background_tasks: BackgroundTasks: Add a task to the background queue
    :param request: Request: Get the base url of the server
    :param db: AsyncSession: Get the database session
    :param dependencies: Add the rate limiter to the signup function
    :param seconds: Set the time limit for the rate limiter
    :param : Get the user's username and base_url to send a verification email
    :return: A user object
    """
    exist_user = await auth_service.get_user_by_username(body.username, db=db)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )
    body.password = auth_service.get_password_hash(body.password)
    new_user = await auth_service.create_user(body, db)
    background_tasks.add_task(
        email_service.send_verification_mail, new_user.username, request.base_url
    )

    return new_user
    # return {"user": new_user, 'detail': 'User successfully created. Check your email for confirmation.'}


@router.post(
    "/login",
    response_model=TokenSchema,
    dependencies=[Depends(RateLimiter(times=1, seconds=20))],
)
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    The login function is used to authenticate a user.
    It takes in the username and password of the user, and returns an access token if successful.
    The access token can be used to make authenticated requests against protected endpoints.

    :param body: OAuth2PasswordRequestForm: Get the username and password from the request body
    :param db: AsyncSession: Get the database session
    :return: A dictionary of the access token, refresh token and the bearer type
    """
    user = await auth_service.get_user_by_username(body.username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username"
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
        )
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )
    access_token = await auth_service.create_access_token(data={"sub": user.username})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.username})

    await auth_service.update_refresh_token(user, refresh_token, db)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/refresh_token", response_model=TokenSchema)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(get_refresh_token),
    db: AsyncSession = Depends(get_db),
):
    """
    The refresh_token function is used to refresh the access token.

    :param credentials: HTTPAuthorizationCredentials: Get the refresh token from the authorization header
    :param db: AsyncSession: Get the database session
    :param : Get the refresh token from the header
    :return: A dict with the access_token, refresh_token and token_type
    """
    token = credentials.credentials
    username = await auth_service.decode_refresh_token(token)
    user = await auth_service.get_user_by_username(username, db)
    refresh_token = await auth_service.get_refresh_token_by_user(user, db)
    if refresh_token != token:
        await auth_service.update_refresh_token(user, None, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    access_token = await auth_service.create_access_token(data={"sub": user.username})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.username})

    await auth_service.update_refresh_token(user, refresh_token, db)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    The confirmed_email function is used to confirm a user's email address.
        It takes in the token that was sent to the user's email and uses it to get their username, which is then used
        to find their account in the database. If no account exists with that username, an error message will be returned.
        If there is an account with that username but it has already been confirmed, a message saying so will be returned.
        Otherwise, if there is an unconfirmed account with that username, its status will be changed from unconfirmed
         (False) to confirmed (True). A success message

    :param token: str: Get the token from the url
    :param db: AsyncSession: Pass the database session to the function
    :return: A dictionary with a message
    """
    email = await auth_service.get_email_from_token(token)
    user = await auth_service.get_user_by_username(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await auth_service.confirmed_email(email, db)

    return {"message": "Email confirmed"}


@router.get("/forgot_password/{username}")
async def forgot_password(
    username: str,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    The forgot_password function is used to send a password reset email to the user.
        The function takes in the username of the user and sends an email with a link that allows them
        to reset their password.

    :param username: str: Get the username of the user that is requesting to reset their password
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base_url of the application
    :param db: AsyncSession: Get the database session
    :param : Send an email to the user
    :return: A json response
    """
    user = await auth_service.get_user_by_username(username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email not found"
        )
    background_tasks.add_task(
        email_service.send_request_to_reset_password, username, request.base_url
    )

    return {
        "message": "A password reset email was sent to your email address. Check your email."
    }


@router.get("/reset_password/{token}")
async def reset_password(token: str, db: AsyncSession = Depends(get_db)):
    """
    The reset_password function is used to reset a user's password.
        It takes in the token that was sent to the user's email address and uses it
        to get their email address, which is then used to find their account in the database.

        If no account with that email exists, an HTTP 400 error will be raised.

        Otherwise, a redirect response will be returned.

    :param token: str: Get the token from the url
    :param db: AsyncSession: Get the database session from the dependency injection
    :return: A redirectresponse, which is a subclass of response
    """
    email = await auth_service.get_email_from_token(token)
    user = await auth_service.get_user_by_username(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )

    return RedirectResponse(url="/api/auth/reset_password")


@router.post("/reset_password")
async def reset_password(
    body: UserResetPasswordSchema,
    db: AsyncSession = Depends(get_db),
    dependencies=[Depends(RateLimiter(times=1, seconds=20))],
):
    """
    The reset_password function allows a user to reset their password.
        The function takes in the following parameters:
            body (UserResetPasswordSchema): A UserResetPasswordSchema object containing the username, password, and confirm_password of the user.
            db (AsyncSession): An AsyncSession object that is used to connect to our database. This parameter is optional and defaults to Depends(get_db).

    :param body: UserResetPasswordSchema: Validate the request body
    :param db: AsyncSession: Get the database connection
    :param dependencies: Add a dependency to the function
    :param seconds: Set the time limit for the rate limiter
    :param : Get the user's username and password
    :return: A dict
    """
    exist_user = await auth_service.get_user_by_username(body.username, db=db)
    if not exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account not found"
        )
    if body.password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Password is not correct"
        )

    body.password = auth_service.get_password_hash(body.password)

    await auth_service.change_password(body, db)

    return {"message": "You have changed your password!"}
