import pickle
from fastapi import APIRouter, Depends, Response, UploadFile, File
from fastapi.responses import FileResponse
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
import cloudinary
import cloudinary.uploader

from src.dependencies.database import get_db
from src.models.users import UserModel
from src.schemas.user import UserReadSchema
from src.services.auth import auth_service
from src.services.users import UserService

from src.conf.config import config


router = APIRouter(prefix="/users", tags=["users"])
cloudinary.config(
    cloud_name=config.CLOUDINARY_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET,
    secure=True,
)


@router.get(
    "/profile",
    response_model=UserReadSchema,
    dependencies=[Depends(RateLimiter(times=3, seconds=20))],
)
async def get_current_user(user: UserModel = Depends(auth_service.get_current_user)):
    """
    The get_current_user function is a dependency that will be injected into the
        get_current_user endpoint. It will return the user object of the currently
        authenticated user, or None if no authentication token was provided in the request.

    :param user: UserModel: Get the current user
    :return: The current user
    """
    return user


@router.patch(
    "/avatar",
    response_model=UserReadSchema,
    dependencies=[Depends(RateLimiter(times=3, seconds=20))],
)
async def upload_avatar(
    file: UploadFile = File(),
    user: UserModel = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    The upload_avatar function uploads a user's avatar to Cloudinary and updates the database with the new URL.

    :param file: UploadFile: Get the file from the request body
    :param user: UserModel: Get the current user from the database
    :param db: AsyncSession: Create a database session, which is used to interact with the database
    :param : Get the current user from the database
    :return: A usermodel object
    """
    public_id = f"fastcontacts/{user.username}"
    res = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
    res_url = cloudinary.CloudinaryImage(public_id).build_url(
        width=250, height=250, crop="fill", version=res.get("version")
    )
    user = await UserService(db).update_avatar(user.username, res_url)
    auth_service.cache.set(user.username, pickle.dumps(user))
    auth_service.cache.expire(user.username, 300)

    return user


@router.get("/default_avatar")
async def send_default_avatar():
    """
    The send_default_avatar function is a route that returns the default avatar image.


    :param # user: UserModel: Get the current user from the database
    :param : Get the current user from the database
    :return: A fileresponse object
    """
    return FileResponse(
        "src/static/avatar-person.svg",
        media_type="image/svg",
        content_disposition_type="inline",
    )
