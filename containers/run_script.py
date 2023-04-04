import boto3
import botocore
import os
import json
import shutil
import requests
import logging
import sys
from datetime import datetime
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


class Tee(object):
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self) :
        for f in self.files:
            f.flush()


def make_logger(run_identifier: str):
    logging.basicConfig()
    logger = logging.getLogger("sorting_worker")
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s -- %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Add a logging handler for the log file
    fileHandler = logging.FileHandler(
        filename=f"/logs/sorting_worker_{run_identifier}.log",
        mode="a",
    )
    fileHandler.setFormatter(log_formatter)
    fileHandler.setLevel(level=logging.DEBUG)
    logger.addHandler(fileHandler)

    # Add a logging handler for stdout
    stdoutHandler = logging.StreamHandler(sys.stdout)
    stdoutHandler.setLevel(logging.DEBUG)
    stdoutHandler.setFormatter(log_formatter)
    logger.addHandler(stdoutHandler)
    
    # Redirect stdout to a file-like object that writes to both stdout and the log file
    stdout_log_file = open(f"/logs/sorting_worker_{run_identifier}.log", "a")
    sys.stdout = Tee(sys.stdout, stdout_log_file)

    # # Handler to print to console as well
    # handler = logging.StreamHandler(sys.stdout)
    # handler.setLevel(logging.DEBUG)
    # handler.setFormatter(log_formatter)
    # logger.addHandler(handler)
    return logger


def download_file_from_url(url):
    # ref: https://stackoverflow.com/a/39217788/11483674
    local_filename = "/data/filename.nwb"
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
                Filename=f"/data/{file_name}"
            )


def upload_all_files_to_bucket_folder(
    logger:logging.Logger,
    client:botocore.client.BaseClient, 
    bucket_name:str, 
    bucket_folder:str,
    local_folder:str
):
    # List files from results, upload them to S3
    files_list = [f for f in Path(local_folder).rglob("*") if f.is_file()]
    for f in files_list:
        logger.info(f"Uploading {str(f)}...")
        client.upload_file(
            Filename=str(f),
            Bucket=bucket_name,
            Key=f"{bucket_folder}{str(f)}",
        )


def main(
    run_identifier:str = None,
    source_aws_s3_bucket:str = None,
    source_aws_s3_bucket_folder:str = None,
    dandiset_s3_file_url:str = None,
    dandiset_file_es_name:str = None,
    target_output_type:str = None,
    target_aws_s3_bucket:str = None,
    target_aws_s3_bucket_folder:str = None,
    data_type:str = None,
    recording_kwargs:dict = None,
    sorters_names_list:list = None,
    sorters_kwargs:dict = None,
    test_with_toy_recording:bool = None,
    test_with_subrecording:bool = None,
    test_subrecording_n_frames:int = None,
    log_to_file:bool = None,
):
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

    # Order of priority for definition of running arguments:
    # 1. passed by function
    # 2. retrieved from ENV vars
    # 3. default value
    if not run_identifier:
        run_identifier = os.environ.get("RUN_IDENTIFIER", datetime.now().strftime("%Y%m%d%H%M%S"))
    if not source_aws_s3_bucket:
        source_aws_s3_bucket = os.environ.get("SOURCE_AWS_S3_BUCKET", None)
    if not source_aws_s3_bucket_folder:
        source_aws_s3_bucket_folder = os.environ.get("SOURCE_AWS_S3_BUCKET_FOLDER", None)
    if not dandiset_s3_file_url:
        dandiset_s3_file_url = os.environ.get("DANDISET_S3_FILE_URL", None)
    if not dandiset_file_es_name:
        dandiset_file_es_name = os.environ.get("DANDISET_FILE_ES_NAME", "ElectricalSeries")
    if not target_output_type:
        target_output_type = os.environ.get("TARGET_OUTPUT_TYPE", "s3")
    if not target_aws_s3_bucket:
        target_aws_s3_bucket = os.environ.get("TARGET_AWS_S3_BUCKET", None)
    if not target_aws_s3_bucket_folder:
        target_aws_s3_bucket_folder = os.environ.get("TARGET_AWS_S3_BUCKET_FOLDER", None)
    if not data_type:
        data_type = os.environ.get("DATA_TYPE", "nwb")
    if not recording_kwargs:
        recording_kwargs = json.loads(os.environ.get("RECORDING_KWARGS", "{}"))
    if not sorters_names_list:
        sorters_names_list = os.environ.get("SORTERS_NAMES_LIST", "kilosort3").split(",")
    if not sorters_kwargs:
        sorters_kwargs = eval(os.environ.get("SORTERS_KWARGS", "{}"))
    if not test_with_toy_recording:
        test_with_toy_recording = os.environ.get("TEST_WITH_TOY_RECORDING", False).lower() in ('true', '1', 't')
    if not test_with_subrecording:
        test_with_subrecording = os.environ.get("TEST_WITH_SUB_RECORDING", False).lower() in ('true', '1', 't')
    if not test_subrecording_n_frames:
        test_subrecording_n_frames = int(os.environ.get("TEST_SUBRECORDING_N_FRAMES", 300000))
    if not log_to_file:
        log_to_file = bool(os.environ.get("LOG_TO_FILE", False))

    # Set up logging
    # logger = make_logger(run_identifier)
    logger = logging.getLogger("sorting_worker")

    # Data source
    if (source_aws_s3_bucket is None or source_aws_s3_bucket_folder is None) and (dandiset_s3_file_url is None) and (not test_with_toy_recording):
        raise Exception("Missing either: \n- SOURCE_AWS_S3_BUCKET and SOURCE_AWS_S3_BUCKET_FOLDER, or \n- DANDISET_S3_FILE_URL")

    s3_client = boto3.client('s3')

    if test_with_toy_recording:
        logger.info("Generating toy recording...")
        recording, _ = se.toy_example(
            duration=10,
            seed=0,
            num_channels=64,
            num_segments=1
        )
    
    elif source_aws_s3_bucket and source_aws_s3_bucket_folder:
        logger.info(f"Downloading dataset: {source_aws_s3_bucket}/{source_aws_s3_bucket_folder}")
        download_all_files_from_bucket_folder(
            client=s3_client,
            bucket_name=source_aws_s3_bucket, 
            bucket_folder=source_aws_s3_bucket_folder
        )

        logger.info("Reading recording...")
        # E.g.: se.read_spikeglx(folder_path="/data", stream_id="imec.ap")
        recording = DATA_TYPE_TO_READER.get(data_type)(
            folder_path="/data",
            **recording_kwargs
        )

    elif dandiset_s3_file_url:
        if not dandiset_s3_file_url.startswith("https://dandiarchive.s3.amazonaws.com"):
            raise Exception(f"DANDISET_S3_FILE_URL should be a valid Dandiset S3 url. Value received was: {dandiset_s3_file_url}")

        if not test_with_subrecording:            
            logger.info(f"Downloading dataset: {dandiset_s3_file_url}")
            download_file_from_url(dandiset_s3_file_url)
            
            logger.info("Reading recording from NWB...")
            recording = se.read_nwb_recording(
                file_path="/data/filename.nwb",
                electrical_series_name=dandiset_file_es_name,
                **recording_kwargs
            )
        else:
            logger.info("Reading recording from NWB...")
            recording = se.read_nwb_recording(
                file_path=dandiset_s3_file_url,
                electrical_series_name=dandiset_file_es_name,
                stream_mode="fsspec",
                **recording_kwargs
            )

    if test_with_subrecording:
        n_frames = int(min(test_subrecording_n_frames, recording.get_num_frames()))
        recording = recording.frame_slice(start_frame=0, end_frame=n_frames)
    
    # Preprocessing ----------------------------------------------------------------------
    #  TODO
    # ------------------------------------------------------------------------------------

    # Run sorters
    if test_with_toy_recording:
        n_jobs = 1
    else:
        n_jobs = int(os.cpu_count())
    sorting_list = list()
    sorters_names_list = [s.lower().strip() for s in sorters_names_list]
    for sorter_name in sorters_names_list:
        try:
            logger.info(f"Running {sorter_name}...")
            sorter_job_kwargs = sorters_kwargs.get(sorter_name, {})
            sorter_job_kwargs["n_jobs"] = min(n_jobs, sorter_job_kwargs.get("n_jobs", n_jobs))
            output_folder = f"/results/sorting/{run_identifier}_{sorter_name}"
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
            sorting.save_to_folder(folder=f'/results/sorting/{run_identifier}_{sorter_name}/sorter_exported')

            if target_output_type == "local":
                # Copy sorting results to local - already done by mounted volume
                pass
            elif target_output_type == "s3":
                # Upload sorting results to S3
                upload_all_files_to_bucket_folder(
                    logger=logger,
                    client=s3_client, 
                    bucket_name=target_aws_s3_bucket, 
                    bucket_folder=target_aws_s3_bucket_folder,
                    local_folder=f'/results/sorting/{run_identifier}_{sorter_name}/sorter_exported'
                )
        except Exception as e:
            logger.info(f"Error running sorter {sorter_name}: {e}")
            print(f"Error running sorter {sorter_name}: {e}")
            if target_output_type == "local":
                # Copy error logs to local - already done by mounted volume
                pass
            elif target_output_type == "s3":
                # upload error logs to S3
                upload_all_files_to_bucket_folder(
                    logger=logger,
                    client=s3_client,
                    bucket_name=target_aws_s3_bucket,
                    bucket_folder=target_aws_s3_bucket_folder,
                    local_folder=output_folder
                )


    # Post sorting operations
    if len(sorters_names_list) > 1:
        logger.info("Running sorters comparison...")
        mcmp = sc.compare_multiple_sorters(
            sorting_list=sorting_list,
            name_list=sorters_names_list,
            verbose=True,
        )
        logger.info("Matching results:")
        logger.info(mcmp.comparisons[tuple(sorters_names_list)].get_matching())


    logger.info("Sorting job completed successfully!")


if __name__ == '__main__':
    main()

# Known issues:
#
# Kilosort3:
# Error using accumarray - First input SUBS must contain positive integer subscripts.
# https://github.com/MouseLand/Kilosort/issues/463