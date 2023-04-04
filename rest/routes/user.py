from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.logger import logger
from core.settings import settings
from clients.database import DatabaseClient


router = APIRouter()

@router.get("/user", response_description="Get user", tags=["user"])
def route_get_user(username: str) -> JSONResponse:
    logger.info(f"Getting user info: {username}")
    db_client = DatabaseClient(connection_string=settings.DB_CONNECTION_STRING)
    user = db_client.get_user_info(username=username)
    
    return JSONResponse({
        "message": "Get user",
        "user": f"{user.username} psswd: {user.password}"
    })