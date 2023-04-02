from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.logger import logger
from core.settings import settings
from clients.database import DatabaseClient
from clients.aws import AWSClient
from clients.local_worker import LocalWorkerClient


router = APIRouter()

@router.get("/info", response_description="Get run", tags=["run"])
def route_get_run_info(run_id: str) -> JSONResponse:
    logger.info(f"Getting run info: {run_id}")
    db_client = DatabaseClient(connection_string=settings.db_connection_string)
    run = db_client.get_run_info(run_id=run_id)

    logger.info(f"Getting run logs: {run_id}")
    if settings.WORKER_DEPLOY_MODE == "aws":
        aws_client = AWSClient()
        run_logs = aws_client.get_run_logs_s3(run_id=run_id)
    elif settings.WORKER_DEPLOY_MODE == "compose":
        local_worker_client = LocalWorkerClient()
        run_logs = local_worker_client.get_run_logs(run_id=run_id)

    return JSONResponse({
        "message": "Success",
        "run": {
            "id": run.id,
            "name": run.name,
            "last_run": run.last_run,
            "status": run.status,
            "dataset_id": run.dataset_id,
            "metadata": run.metadata,
            "logs": run_logs,
        }
    })