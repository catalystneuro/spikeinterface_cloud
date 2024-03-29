from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List

from clients.dandi import DandiClient
from core.settings import settings


router = APIRouter()


# TODO - proper input/output data models
@router.get("/get-dandisets-labels", response_description="Get Dandisets Labels", tags=["dandi"])
def route_get_dandisets_labels() -> JSONResponse:
    try:
        dandi_client = DandiClient(token=settings.DANDI_API_KEY)
        labels = sorted(dandi_client.get_all_dandisets_labels())
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    return JSONResponse(content={"labels": labels})


# TODO - proper input/output data models
@router.get("/get-dandiset-metadata", response_description="Get Dandisets Metadata", tags=["dandi"])
def route_get_dandiset_metadata(dandiset_id: str) -> JSONResponse:
    try:
        dandi_client = DandiClient(token=settings.DANDI_API_KEY)
        metadata = dandi_client.get_dandiset_metadata(dandiset_id)
        cleaned_metadata = {
            "name": metadata["name"],
            "url": metadata["url"],
            "description": metadata["description"],
        }
        list_of_files = dandi_client.list_dandiset_files(dandiset_id)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")
    return JSONResponse(content={"metadata": cleaned_metadata, "list_of_files": list_of_files})


# TODO - proper input/output data models
@router.get("/get-nwbfile-info", response_description="Get NWB file Info", tags=["dandi"])
async def route_get_nwbfile_info(dandiset_id: str, file_path: str) -> JSONResponse:
    try:
        dandi_client = DandiClient(token=settings.DANDI_API_KEY)
        # file_info = dandi_client.get_nwbfile_info_ros3(dandiset_id, file_path)
        file_info = dandi_client.get_nwbfile_info_fsspec(dandiset_id, file_path)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")
    return JSONResponse(content={"file_info": file_info})