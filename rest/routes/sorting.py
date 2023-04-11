from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime

from core.logger import logger
from core.settings import settings
from clients.dandi import DandiClient
from clients.aws import AWSClient
from clients.local_worker import LocalWorkerClient
from clients.database import DatabaseClient
from models.sorting import SortingData


router = APIRouter()


def sorting_background_task(payload, run_identifier):
    # Run sorting and update db entry status
    db_client = DatabaseClient(connection_string=settings.DB_CONNECTION_STRING)
    run_at = payload.get("run_at", None)
    try:
        logger.info(f"Run job at: {run_at}")
        if run_at == "local":
            client_local_worker = LocalWorkerClient()
            client_local_worker.run_sorting(**payload)
        elif run_at == "aws":
            job_kwargs = {k.upper(): v for k, v in payload.items()}
            client_aws = AWSClient()
            client_aws.submit_job(
                job_name=f"sorting-{run_identifier}",
                job_queue=settings.AWS_BATCH_JOB_QUEUE,
                job_definition=settings.AWS_BATCH_JOB_DEFINITION,
                job_kwargs=job_kwargs,
            )
        db_client.update_run(run_identifier=run_identifier, key="status", value="running")
    except Exception as e:
        logger.exception(f"Error running sorting job: {run_identifier}.\n {e}")
        db_client.update_run(run_identifier=run_identifier, key="status", value="fail")


@router.post("/run", response_description="Run Sorting", tags=["sorting"])
async def route_run_sorting(data: SortingData, background_tasks: BackgroundTasks) -> JSONResponse:
    if not data.run_identifier:
        run_identifier = datetime.now().strftime("%Y%m%d%H%M%S")
    else:
        run_identifier = data.run_identifier
    payload = data.dict()
    try:
        # Create Database entries
        db_client = DatabaseClient(connection_string=settings.DB_CONNECTION_STRING)
        user = db_client.get_user_info(username="admin")
        data_source = db_client.create_data_source(
            name=data.run_identifier,
            description=data.run_description,
            user_id=user.id,
            source=data.source,
            source_data_type=data.source_data_type,
            source_data_urls=",".join(data.source_data_urls),
            recording_kwargs=str(data.recording_kwargs),
        )
        run = db_client.create_run(
            run_at=data.run_at,
            identifier=run_identifier,
            description=data.run_description,
            last_run=datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            status="running",
            data_source_id=data_source.id,
            user_id=user.id,
            metadata=str(payload),
            output_path=data.output_path,
        )

        # Run sorting job
        background_tasks.add_task(sorting_background_task, payload, run_identifier=run_identifier)

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")
    return JSONResponse(content={
        "message": "Sorting job submitted",
        "run_identifier": run.identifier,
    })