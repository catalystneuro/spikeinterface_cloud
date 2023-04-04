from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from datetime import datetime
import asyncio

from core.logger import logger
from core.settings import settings
from clients.dandi import DandiClient
from clients.aws import AWSClient
from clients.local_worker import LocalWorkerClient
from clients.database import DatabaseClient

router = APIRouter()


class SortingData(BaseModel):
    run_at: str = "local"
    run_identifier: str = None
    run_description: str = None
    source_aws_s3_bucket: str = None
    source_aws_s3_bucket_folder: str = None
    dandiset_id: str = None
    dandiset_file_path: str = None
    dandiset_file_es_name: str = None
    target_output_type: str = None
    target_aws_s3_bucket: str = None
    target_aws_s3_bucket_folder: str = None
    data_type: str = None
    recording_kwargs: dict = None
    sorters_names_list: list = None
    sorters_kwargs: dict = None
    test_with_toy_recording: bool = None
    test_with_subrecording: bool = None
    test_subrecording_n_frames: int = None
    log_to_file: bool = None


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
    # Get file url from dandi
    dandi_client = DandiClient()
    dandiset_s3_file_url = dandi_client.get_file_url(
        dandiset_id=data.dandiset_id, 
        file_path=data.dandiset_file_path
    )
    payload = dict(
        run_at=data.run_at,
        run_identifier=run_identifier,
        run_description=data.run_description,
        source_aws_s3_bucket=data.source_aws_s3_bucket,
        source_aws_s3_bucket_folder=data.source_aws_s3_bucket_folder,
        dandiset_s3_file_url=dandiset_s3_file_url,
        dandiset_file_es_name=data.dandiset_file_es_name,
        target_output_type=data.target_output_type,
        target_aws_s3_bucket=data.target_aws_s3_bucket,
        target_aws_s3_bucket_folder=data.target_aws_s3_bucket_folder,
        data_type=data.data_type,
        recording_kwargs=data.recording_kwargs,
        sorters_names_list=data.sorters_names_list,
        sorters_kwargs=data.sorters_kwargs,
        test_with_toy_recording=data.test_with_toy_recording,
        test_with_subrecording=data.test_with_subrecording,
        test_subrecording_n_frames=data.test_subrecording_n_frames,
        log_to_file=data.log_to_file,
    )
    try:
        # Create Database entries
        db_client = DatabaseClient(connection_string=settings.DB_CONNECTION_STRING)
        user = db_client.get_user_info(username="admin")
        dataset = db_client.create_dataset(
            name=data.dandiset_id + " - " + data.dandiset_file_path,
            description="",
            user_id=user.id,
            source="dandi",
            source_metadata=str({
                "dandiset_id": data.dandiset_id,
                "dandiset_file_path": data.dandiset_file_path,
                "dandiset_file_es_name": data.dandiset_file_es_name,
            }),
        )
        run = db_client.create_run(
            run_at=data.run_at,
            identifier=run_identifier,
            description=data.run_description,
            last_run=datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            status="running",
            dataset_id=dataset.id,
            user_id=user.id,
            metadata=str(payload),
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