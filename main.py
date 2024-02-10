import redis.asyncio as redis
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import config
from src.dependencies.database import get_db
from src.routers.auth import router as auth
from src.routers.contacts_items import router as contacts_router
from src.routers.users import router as users_router

app = FastAPI()
app.include_router(auth, prefix="/api")
app.include_router(contacts_router, prefix="/api")
app.include_router(users_router, prefix="/api")

app.mount("/static", StaticFiles(directory=config.BASE_DIR / "static"), name="static")


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """
    The startup function is called when the application starts up.
    It's a good place to initialize things that are used by the app, like databases or caches.

    :return: A list of functions to be run in the background
    """
    r = await redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
        encoding="utf-8",
        decode_responses=True,
    )
    await FastAPILimiter.init(r)


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """
    The healthchecker function is a simple function that checks if the database is up and running.
    It does this by making a request to the database, and checking if it returns any results.
    If it doesn't return any results, then we know something's wrong with our connection.

    :param db: AsyncSession: Pass the database connection to the function
    :return: A dictionary with the key &quot;message&quot; and value &quot;welcome to fastapi!&quot;
    """
    try:
        # Make request
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(
                status_code=500, detail="Database is not configured correctly"
            )
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")
