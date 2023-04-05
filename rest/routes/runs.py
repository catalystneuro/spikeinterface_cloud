from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.logger import logger
from core.settings import settings
from clients.database import DatabaseClient
from clients.aws import AWSClient
from clients.local_worker import LocalWorkerClient


router = APIRouter()

map_aws_batch_status_to_rest_status = {
    "SUBMITTED": "running",
    "PENDING": "running",
    "RUNNABLE": "running",
    "STARTING": "running",
    "RUNNING": "running",
    "SUCCEEDED": "success",
    "FAILED": "fail",
}


def get_run_info(run_id: str):
    db_client = DatabaseClient(connection_string=settings.DB_CONNECTION_STRING)
    run_info = db_client.get_run_info(run_id=run_id)
    if run_info["status"] == "running":
        # Get status and logs
        logger.info(f"Getting run status and logs: {run_info['identifier']}")
        try:
            if run_info["run_at"] == "aws":
                aws_client = AWSClient()
                status, run_logs = aws_client.get_job_status_and_logs_by_name(job_name=f"sorting-{run_info['identifier']}", job_queue=settings.AWS_BATCH_JOB_QUEUE)
                status = map_aws_batch_status_to_rest_status[status]
                if status == "success":
                    if "Error running sorter" in run_logs:
                        status = "fail"
            elif run_info["run_at"] == "local":
                local_worker_client = LocalWorkerClient()
                status, run_logs = local_worker_client.get_run_logs(run_identifier=run_info['identifier'])
            else:
                status = "running"
                run_logs = "No logs for this run"
        except Exception as e:
            logger.exception(f"Error getting run logs: {run_info['identifier']}. {e}")
            run_logs = f"Error getting run logs: {run_info['identifier']}. {e}"
            status = "running"
        run_info["status"] = status
        db_client.update_run(run_identifier=run_info["identifier"], key="status", value=status)
        db_client.update_run(run_identifier=run_info["identifier"], key="logs", value=run_logs)
        run_info["logs"] = run_logs
    return run_info


@router.get("/list", response_description="Get runs", tags=["runs"])
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


@router.get("/info", response_description="Get run", tags=["runs"])
def route_get_run_info(run_id: str) -> JSONResponse:
    logger.info(f"Getting run info: {run_id}")
    run_info = get_run_info(run_id=run_id)
    return JSONResponse({
        "message": "Success",
        "run": run_info
    })


@router.delete("/{run_identifier}", response_description="Delete run", tags=["runs"])
def route_delete_run(run_identifier: str) -> JSONResponse:
    logger.info(f"Deleting run: {run_identifier}")
    db_client = DatabaseClient(connection_string=settings.DB_CONNECTION_STRING)
    response = db_client.delete_run(run_identifier=run_identifier)
    if response:
        return JSONResponse({
            "message": "Success"
        })  
    else:
        raise HTTPException(status_code=400, detail="Run not found")