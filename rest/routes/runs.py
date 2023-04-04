from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.logger import logger
from core.settings import settings
from clients.database import DatabaseClient
from clients.aws import AWSClient
from clients.local_worker import LocalWorkerClient


router = APIRouter()


def get_run_info(run_id: str):
    db_client = DatabaseClient(connection_string=settings.DB_CONNECTION_STRING)
    run_info = db_client.get_run_info(run_id=run_id)
    logger.info(f"Getting run logs: {run_info['identifier']}")
    if settings.WORKER_DEPLOY_MODE == "aws":
        aws_client = AWSClient()
        run_logs = aws_client.get_run_logs_s3(run_id=run_id)
    elif settings.WORKER_DEPLOY_MODE == "compose":
        local_worker_client = LocalWorkerClient()
        run_logs = local_worker_client.get_run_logs(run_identifier=run_info['identifier'])
    return {
        "logs": run_logs,
        **run_info
    }


@router.get("/list", response_description="Get runs", tags=["run"])
def route_get_runs_list() -> JSONResponse:
    logger.info("Getting runs list")
    db_client = DatabaseClient(connection_string=settings.DB_CONNECTION_STRING)
    user = db_client.get_user_info(username="admin")
    runs = [
        get_run_info(run_id=obj.id) for obj in db_client.query_runs_by_user(user_id=user.id)
    ]
    return JSONResponse({
        "message": "Success",
        "runs": runs
    })


@router.get("/info", response_description="Get run", tags=["run"])
def route_get_run_info(run_id: str) -> JSONResponse:
    logger.info(f"Getting run info: {run_id}")
    run_info = get_run_info(run_id=run_id)
    return JSONResponse({
        "message": "Success",
        "run": run_info
    })