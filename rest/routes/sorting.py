from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime

from ..core.logger import logger
from ..core.settings import settings
from ..clients.dandi import DandiClient
from ..clients.aws import AWSClient
from ..clients.local_docker import LocalDockerClient
from ..clients.database import DatabaseClient
from ..models.sorting import (
    RunKwargs,
    SourceDataKwargs,
    RecordingKwargs,
    PreprocessingKwargs,
    SorterKwargs,
    PostprocessingKwargs,
    CurationKwargs,
    VisualizationKwargs,
    OutputDataKwargs
)


router = APIRouter()


def sorting_background_task(
    run_kwargs: RunKwargs,
    source_data_kwargs: SourceDataKwargs,
    recording_kwargs: RecordingKwargs,
    preprocessing_kwargs: PreprocessingKwargs,
    sorter_kwargs: SorterKwargs,
    postprocessing_kwargs: PostprocessingKwargs,
    curation_kwargs: CurationKwargs,
    visualization_kwargs: VisualizationKwargs,
    output_data_kwargs: OutputDataKwargs,
):
    # Run sorting and update db entry status
    db_client = DatabaseClient(connection_string=settings.DB_CONNECTION_STRING)
    run_at = run_kwargs.run_at
    try:
        logger.info(f"Run job at: {run_at}")
        if run_at == "local":
            client_local_worker = LocalDockerClient()
            client_local_worker.run_sorting(
                run_kwargs=run_kwargs,
                source_data_kwargs=source_data_kwargs,
                recording_kwargs=recording_kwargs,
                preprocessing_kwargs=preprocessing_kwargs,
                sorter_kwargs=sorter_kwargs,
                postprocessing_kwargs=postprocessing_kwargs,
                curation_kwargs=curation_kwargs,
                visualization_kwargs=visualization_kwargs,
                output_data_kwargs=output_data_kwargs,
            )
        elif run_at == "aws":
            # TODO: Implement this
            job_kwargs = {k.upper(): v for k, v in payload.items()}
            job_kwargs["DANDI_API_KEY"] = settings.DANDI_API_KEY
            client_aws = AWSClient()
            client_aws.submit_job(
                job_name=f"sorting-{run_identifier}",
                job_queue=settings.AWS_BATCH_JOB_QUEUE,
                job_definition=settings.AWS_BATCH_JOB_DEFINITION,
                job_kwargs=job_kwargs,
            )
        # db_client.update_run(run_identifier=run_identifier, key="status", value="running")
    except Exception as e:
        logger.exception(f"Error running sorting job: {run_kwargs.run_identifier}.\n {e}")
        db_client.update_run(run_identifier=run_kwargs.run_identifier, key="status", value="fail")


@router.post("/run", response_description="Run Sorting", tags=["sorting"])
async def route_run_sorting(
    run_kwargs: RunKwargs,
    source_data_kwargs: SourceDataKwargs,
    recording_kwargs: RecordingKwargs,
    preprocessing_kwargs: PreprocessingKwargs,
    sorter_kwargs: SorterKwargs,
    postprocessing_kwargs: PostprocessingKwargs,
    curation_kwargs: CurationKwargs,
    visualization_kwargs: VisualizationKwargs,
    output_data_kwargs: OutputDataKwargs,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    try:
        # Create Database entries
        db_client = DatabaseClient(connection_string=settings.DB_CONNECTION_STRING)
        user = db_client.get_user_info(username="admin")
        # TODO: Create data source and run entries in database
        # data_source = db_client.create_data_source(
        #     name=run_kwargs.run_identifier,
        #     description=run_kwargs.run_description,
        #     user_id=user.id,
        #     source=source_data_kwargs.source_name,
        #     source_data_type=source_data_kwargs.source_data_type,
        #     source_data_paths=str(source_data_kwargs.source_data_paths),
        #     recording_kwargs=str(recording_kwargs.dict()),
        # )
        # run = db_client.create_run(
        #     run_at=data.run_at,
        #     identifier=run_identifier,
        #     description=data.run_description,
        #     last_run=datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        #     status="running",
        #     data_source_id=data_source.id,
        #     user_id=user.id,
        #     metadata=str(data.json()),
        #     output_destination=data.output_destination,
        #     output_path=data.output_path,
        # )

        # Run sorting job
        background_tasks.add_task(
            sorting_background_task, 
            run_kwargs=run_kwargs,
            source_data_kwargs=source_data_kwargs,
            recording_kwargs=recording_kwargs,
            preprocessing_kwargs=preprocessing_kwargs,
            sorter_kwargs=sorter_kwargs,
            postprocessing_kwargs=postprocessing_kwargs,
            curation_kwargs=curation_kwargs,
            visualization_kwargs=visualization_kwargs,
            output_data_kwargs=output_data_kwargs,
        )

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")
    return JSONResponse(content={
        "message": "Sorting job submitted",
        "run_identifier": run_kwargs.run_identifier,
    })