import shutil
import requests
import logging
import sys
import botocore
from pathlib import Path


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


def make_logger(run_identifier: str, log_to_file: bool):
    logging.basicConfig()
    logger = logging.getLogger("sorting_worker")
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s -- %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if log_to_file:
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
    else:
        # Handler to print to console as well
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(log_formatter)
        logger.addHandler(handler)
    return logger


def download_file_from_url(url):
    # ref: https://stackoverflow.com/a/39217788/11483674
    local_filename = "/data/filename.nwb"
    with requests.get(url, stream=True) as r:
        with open(local_filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)


def download_file_from_s3(
    client:botocore.client.BaseClient, 
    bucket_name:str, 
    file_path:str
):    
    file_name = file_path.split("/")[-1]
    client.download_file(
        Bucket=bucket_name, 
        Key=file_path, 
        Filename=f"/data/{file_name}"
    )
    return file_name       


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


def upload_file_to_bucket(
    logger:logging.Logger,
    client:botocore.client.BaseClient, 
    bucket_name:str, 
    bucket_folder:str,
    local_file_path:str
):
    # Upload file to S3
    logger.info(f"Uploading {local_file_path}...")
    client.upload_file(
        Filename=local_file_path,
        Bucket=bucket_name,
        Key=f"{bucket_folder}/{local_file_path}",
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
