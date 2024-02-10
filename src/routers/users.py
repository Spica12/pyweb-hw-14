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
async def send_default_avatar(
    # user: UserModel = Depends(auth_service.get_current_user),
):
    return FileResponse(
        "src/static/avatar-person.svg",
        media_type="image/svg",
        content_disposition_type="inline",
    )
