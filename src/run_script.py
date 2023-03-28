import boto3
import botocore
import os
import json
import shutil
import requests
from pathlib import Path
import spikeinterface.extractors as se
from spikeinterface.sorters import run_sorter_local
import spikeinterface.comparison as sc


# TODO - complete with more data types
DATA_TYPE_TO_READER = {
    "spikeglx": se.read_spikeglx,
    "nwb": se.read_nwb_recording,
}

# # TODO - create data models for inputs of each data type reader
# DATA_TYPE_READER_DATA_MODELS = {
#     "spikeglx": ,
#     "nwb": ,
# }

# # TODO - complete with more sorters
# SORTER_DATA_MODELS = {
#     "kilosort3": ,
#     "kilosort2_5":,
# }


def download_file_from_url(url):
    # ref: https://stackoverflow.com/a/39217788/11483674
    local_filename = "data/filename.nwb"
    with requests.get(url, stream=True) as r:
        with open(local_filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)


def download_all_files_from_bucket_folder(
    client:botocore.client.BaseClient, 
    bucket_name:str, 
    bucket_folder:str
):    
    # List files in folder, download all files with content
    res = client.list_objects_v2(Bucket=bucket_name, Prefix=bucket_folder)
    for f in res["Contents"]:
        if f["Size"] > 0:
            file_name = f["Key"].split("/")[-1]
            client.download_file(
                Bucket=bucket_name, 
                Key=f["Key"], 
                Filename=f"data/{file_name}"
            )


def upload_all_files_to_bucket_folder(
    client:botocore.client.BaseClient, 
    bucket_name:str, 
    bucket_folder:str,
    local_folder:str
):
    # List files from results, upload them to S3
    files_list = [f for f in Path(local_folder).rglob("*") if f.is_file()]
    for f in files_list:
        print(f"Uploading {str(f)}...")
        client.upload_file(
            Filename=str(f),
            Bucket=bucket_name,
            Key=f"{bucket_folder}{str(f)}",
        )


if __name__ == '__main__':
    """
    This script should run in an ephemeral Docker container and will:
    1. download a dataset with raw electrophysiology traces from a specfied location
    2. run a SpikeInterface pipeline on the raw traces
    3. save the results in a target S3 bucket

    The arguments for this script are passsed as ENV variables:
    - SOURCE_AWS_S3_BUCKET : S3 bucket name for source data.
    - SOURCE_AWS_S3_BUCKET_FOLDER : Folder path within bucket for source data.
    - DANDISET_S3_FILE_URL : Url for S3 path of input data, if it comes from a NWB file hosted in DANDI archive.
    - TARGET_AWS_S3_BUCKET : S3 bucket name for saving results.
    - TARGET_AWS_S3_BUCKET_FOLDER : Folder path within bucket for saving results.
    - DATA_TYPE : Data type to be read.
    - READ_RECORDING_KWARGS : Keyword arguments specific to chosen dataset type.
    - SORTERS : List of sorters to run on source data, stored as comma-separated values.
    - SORTERS_PARAMS : Parameters for each sorter, stored as a dictionary.
    - TEST_WITH_TOY_RECORDING : Runs script with a toy dataset.
    - TEST_WITH_SUB_RECORDING : Runs script with the first 4 seconds of target dataset.
    - SUB_RECORDING_N_FRAMES : Number of frames to use for sub-recording.

    If running this in any AWS service (e.g. Batch, ECS, EC2...) the access to other AWS services 
    such as S3 storage can be given to the container by an IAM role.
    Otherwise, if running this outside of AWS, these ENV variables should be present in the running container:
    - AWS_REGION_NAME
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    """

    # Arguments are retrieved from ENV vars
    source_bucket_name = os.environ.get("SOURCE_AWS_S3_BUCKET", None)
    source_bucket_folder = os.environ.get("SOURCE_AWS_S3_BUCKET_FOLDER", None)
    dandiset_s3_file_url = os.environ.get("DANDISET_S3_FILE_URL", None)
    data_type = os.environ.get("DATA_TYPE", "nwb")
    read_recording_kwargs = json.loads(os.environ.get("READ_RECORDING_KWARGS", "{}"))
    target_bucket_name = os.environ.get("TARGET_AWS_S3_BUCKET", None)
    target_bucket_folder = os.environ.get("TARGET_AWS_S3_BUCKET_FOLDER", None)
    sorters_names_list = os.environ.get("SORTERS", "kilosort3").split(",")
    sorters_params = eval(os.environ.get("SORTERS_PARAMS", "{}"))
    test_toy = bool(os.environ.get("TEST_WITH_TOY_RECORDING", False))
    test_subrecording = bool(os.environ.get("TEST_WITH_SUB_RECORDING", False))
    test_subrecording_n_frames = int(os.environ.get("SUB_RECORDING_N_FRAMES", 300000))


    if (source_bucket_name is None or source_bucket_folder is None) and (dandiset_s3_file_url is None) and (not test_toy):
        raise Exception("Missing either: \n- AWS_S3_BUCKET and AWS_S3_BUCKET_FOLDER, or \n- DANDISET_S3_FILE_URL")

    s3_client = boto3.client('s3')

    if source_bucket_name and source_bucket_folder:
        print(f"Downloading dataset: {source_bucket_name}/{source_bucket_folder}")
        download_all_files_from_bucket_folder(
            client=s3_client,
            bucket_name=source_bucket_name, 
            bucket_folder=source_bucket_folder
        )

        print("Reading recording...")
        # E.g.: se.read_spikeglx(folder_path="/data", stream_id="imec.ap")
        recording = DATA_TYPE_TO_READER.get(data_type)(
            folder_path="/data",
            **read_recording_kwargs
        )

    elif dandiset_s3_file_url:
        if not dandiset_s3_file_url.startswith("https://dandiarchive.s3.amazonaws.com"):
            raise Exception(f"DANDISET_S3_FILE_URL should be a valid Dandiset S3 url. Value received was: {dandiset_s3_file_url}")

        if not test_subrecording:            
            print(f"Downloading dataset: {dandiset_s3_file_url}")
            download_file_from_url(dandiset_s3_file_url)
            
            print("Reading recording from NWB...")
            recording = se.read_nwb_recording(
                file_path="data/filename.nwb",
                **read_recording_kwargs
            )
        else:
            print("Reading recording from NWB...")
            recording = se.read_nwb_recording(
                file_path=dandiset_s3_file_url,
                stream_mode="fsspec",
                **read_recording_kwargs
            )

    elif test_toy:
        recording, _ = se.toy_example(
            duration=10,
            seed=0,
            num_channels=64,
            num_segments=1
        )

    if test_subrecording:
        n_frames = int(min(test_subrecording_n_frames, recording.get_num_frames()))
        recording = recording.frame_slice(start_frame=0, end_frame=n_frames)
    
    # Preprocessing ----------------------------------------------------------------------
    #  TODO
    # ------------------------------------------------------------------------------------

    # Run sorters
    n_jobs = int(os.cpu_count())
    sorting_list = list()
    for sorter_name in sorters_names_list:
        try:
            print(f"Running {sorter_name}...")
            sorter_job_kwargs = sorters_params.get(sorter_name, {})
            sorter_job_kwargs["n_jobs"] = min(n_jobs, sorter_job_kwargs.get("n_jobs", n_jobs))
            output_folder = f"/results/sorting/{sorter_name}"
            sorting = run_sorter_local(
                sorter_name, 
                recording, 
                output_folder=output_folder,
                remove_existing_folder=True, 
                delete_output_folder=True,
                verbose=True, 
                raise_error=True, 
                with_output=True,
                **sorter_job_kwargs
            )
            sorting_list.append(sorting)
            sorting.save_to_folder(folder=f'/results/sorter_exported_{sorter_name}')

            # Upload sorting results to S3
            upload_all_files_to_bucket_folder(
                client=s3_client, 
                bucket_name=target_bucket_name, 
                bucket_folder=target_bucket_folder,
                local_folder=f'/results/sorter_exported_{sorter_name}'
            )
        except Exception as e:
            print(f"Error running sorter {sorter_name}: {e}")
            # upload error logs to S3
            upload_all_files_to_bucket_folder(
                client=s3_client,
                bucket_name=target_bucket_name,
                bucket_folder=target_bucket_folder,
                local_folder=output_folder
            )


    # Post sorting operations
    if len(sorters_names_list) > 1:
        print("Running sorters comparison...")
        mcmp = sc.compare_multiple_sorters(
            sorting_list=sorting_list,
            name_list=sorters_names_list,
            verbose=True,
        )
        print("Matching results:")
        print(mcmp.comparisons[tuple(sorters_names_list)].get_matching())


# Known issues:
#
# Kilosort3:
# Error using accumarray - First input SUBS must contain positive integer subscripts.
# https://github.com/MouseLand/Kilosort/issues/463