import boto3
import botocore
import os
from pathlib import Path
import spikeinterface.extractors as se
from spikeinterface.sorters import run_sorter_local
import spikeinterface.comparison as sc


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
    # S3 client
    client = boto3.client(
        's3', 
        # region_name=os.environ["AWS_REGION_NAME"], 
        # aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        # aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"]
    )

    # Run-specific arguments are retireved from ENV vars
    bucket_name = os.environ["AWS_S3_BUCKET"]
    bucket_folder = os.environ["AWS_S3_BUCKET_FOLDER"]

    # Download data
    print(f"Downloading dataset: {bucket_name}/{bucket_folder}")
    download_all_files_from_bucket_folder(
        client=client,
        bucket_name=bucket_name, 
        bucket_folder=bucket_folder
    )

    # Read SpikeGLX data into recording
    print("Reading recording...")
    recording = se.read_spikeglx(folder_path="/data", stream_id="imec.ap")


    # recording, _ = se.toy_example(
    #     duration=10,
    #     seed=0,
    #     num_channels=64,
    #     num_segments=1
    # )

    # Run sorter
    print("Running Kilosort 3...")
    output_folder = '/results/sorting'
    sorting_ks3 = run_sorter_local(
        'kilosort3', 
        recording, 
        output_folder=output_folder,
        remove_existing_folder=True, 
        delete_output_folder=True,
        verbose=True, 
        raise_error=True, 
        with_output=True
    )
    sorting_ks3.save_to_folder(folder='/results/sorter_exported_ks3')

    print("Running Kilosort 2.5...")
    output_folder = '/results/sorting'
    sorting_ks25 = run_sorter_local(
        'kilosort2_5', 
        recording, 
        output_folder=output_folder,
        remove_existing_folder=True, 
        delete_output_folder=True,
        verbose=True, 
        raise_error=True, 
        with_output=True
    )
    sorting_ks25.save_to_folder(folder='/results/sorter_exported_ks25')

    print("Running sorters comparison...")
    mcmp = sc.compare_multiple_sorters(
        sorting_list=[sorting_ks3, sorting_ks25],
        name_list=['KS3', 'KS25'],
        verbose=True,
    )
    print("Matching results:")
    print(mcmp.comparisons[('KS3', 'KS25')].get_matching())

    # Upload sorting results to S3
    upload_all_files_to_bucket_folder(
        client=client, 
        bucket_name=bucket_name, 
        bucket_folder=bucket_folder,
        local_folder="results/sorter_exported_ks3"
    )
    upload_all_files_to_bucket_folder(
        client=client, 
        bucket_name=bucket_name, 
        bucket_folder=bucket_folder,
        local_folder="results/sorter_exported_ks25"
    )
