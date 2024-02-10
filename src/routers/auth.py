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
