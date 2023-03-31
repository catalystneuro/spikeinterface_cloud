from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import asyncio

from clients.dandi import DandiClient
from clients.aws import AWSClient
from clients.local_worker import LocalWorkerClient

router = APIRouter()


# TODO - proper input/output data models
@router.get("/run-sorting", response_description="Run Sorting", tags=["sorting"])
def route_run_sorting(
    source_aws_s3_bucket: str,
    source_aws_s3_bucket_folder: str,
    dandiset_id: str,
    dandiset_file_path: str,
    dandiset_file_es_name: str,
    target_aws_s3_bucket: str,
    target_aws_s3_bucket_folder: str,
    data_type: str,
    recording_kwargs: str,
    sorters_names_list: str,
    sorters_kwargs: str,
    test_with_toy_recording: bool,
    test_with_subrecording: bool,
    test_subrecording_n_frames: int,
) -> JSONResponse:
    # Get file url from dandi
    dandi_client = DandiClient()
    dandiset_s3_file_url = dandi_client.get_file_url(
        dandiset_id=dandiset_id, 
        dandiset_file_path=dandiset_file_path
    )
    payload = dict(
        source_aws_s3_bucket=source_aws_s3_bucket,
        source_aws_s3_bucket_folder=source_aws_s3_bucket_folder,
        dandiset_s3_file_url=dandiset_s3_file_url,
        dandiset_file_es_name=dandiset_file_es_name,
        target_aws_s3_bucket=target_aws_s3_bucket,
        target_aws_s3_bucket_folder=target_aws_s3_bucket_folder,
        data_type=data_type,
        recording_kwargs=recording_kwargs,
        sorters_names_list=sorters_names_list,
        sorters_kwargs=sorters_kwargs,
        test_with_toy_recording=test_with_toy_recording,
        test_with_subrecording=test_with_subrecording,
        test_subrecording_n_frames=test_subrecording_n_frames,
    )
    try:
        client_local_worker = LocalWorkerClient()
        asyncio.run(client_local_worker.run_sorting(**payload))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")
    return JSONResponse(content={"message": "Sorting completed"})