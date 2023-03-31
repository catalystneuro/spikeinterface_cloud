from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import asyncio

from core.logger import logger
from clients.dandi import DandiClient
from clients.aws import AWSClient
from clients.local_worker import LocalWorkerClient

router = APIRouter()


class SortingData(BaseModel):
    source_aws_s3_bucket: str = None
    source_aws_s3_bucket_folder: str = None
    dandiset_id: str = None
    dandiset_file_path: str = None
    dandiset_file_es_name: str = None
    target_output_type: str = None
    target_aws_s3_bucket: str = None
    target_aws_s3_bucket_folder: str = None
    data_type: str = None
    recording_kwargs: str = None
    sorters_names_list: list = None
    sorters_kwargs: dict = None
    test_with_toy_recording: bool = None
    test_with_subrecording: bool = None
    test_subrecording_n_frames: int = None


@router.post("/run", response_description="Run Sorting", tags=["sorting"])
def route_run_sorting(data: SortingData) -> JSONResponse:
    # Get file url from dandi
    dandi_client = DandiClient()
    dandiset_s3_file_url = dandi_client.get_file_url(
        dandiset_id=data.dandiset_id, 
        file_path=data.dandiset_file_path
    )
    payload = dict(
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
    )
    try:
        client_local_worker = LocalWorkerClient()
        asyncio.run(client_local_worker.run_sorting(**payload))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")
    return JSONResponse(content={"message": "Sorting job submitted"})