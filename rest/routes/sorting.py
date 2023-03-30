from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List

from clients.aws import AWSClient
from clients.local_worker import LocalWorkerClient

router = APIRouter()


# TODO - proper input/output data models
@router.get("/run-sorting", response_description="Run Sorting", tags=["sorting"])
def route_run_sorting(
    source_aws_s3_bucket: str,
    source_aws_s3_bucket_folder: str,
    dandiset_s3_file_url: str,
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
    try:
        # TODO - run sorting
        client_local_worker = LocalWorkerClient()
        client_local_worker.run_sorting(
            source_aws_s3_bucket=source_aws_s3_bucket,
            source_aws_s3_bucket_folder=source_aws_s3_bucket_folder,
            dandiset_s3_file_url=dandiset_s3_file_url,
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
        pass
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")
    return JSONResponse(content={"message": "Sorting completed"})