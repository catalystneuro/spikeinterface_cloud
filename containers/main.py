import boto3
import os
import ast
import subprocess
from warnings import filterwarnings
from datetime import datetime
from pathlib import Path
import spikeinterface.extractors as se
from spikeinterface.sorters import run_sorter_local
import spikeinterface.comparison as sc
from neuroconv.tools.spikeinterface import write_sorting, write_recording
from nwbinspector import inspect_nwbfile_object
from pynwb import NWBHDF5IO, NWBFile
from dandi.validate import validate
from dandi.organize import organize
from dandi.upload import upload
from dandi.download import download

from utils import (
    make_logger,
    download_file_from_s3,
    upload_file_to_bucket,
    upload_all_files_to_bucket_folder,
    download_file_from_url,
)


def main(
    run_identifier:str = None,
    source:str = None,
    source_data_type:str = None,
    source_data_paths:dict = None,
    recording_kwargs:dict = None,
    output_destination:str = None,
    output_path:str = None,
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

    The arguments for this script can be passsed as ENV variables:
    - RUN_IDENTIFIER : Unique identifier for this run.
    - SOURCE : Source of input data. Choose from: local, s3, dandi.
    - SOURCE_DATA_PATHS : Dictionary with paths to source data. Keys are names of data files, values are urls.
    - SOURCE_DATA_TYPE : Data type to be read. Choose from: nwb, spikeglx.
    - RECORDING_KWARGS : SpikeInterface extractor keyword arguments, specific to chosen dataset type.
    - OUTPUT_DESTINATION : Destination for saving results. Choose from: local, s3, dandi.
    - OUTPUT_PATH : Path for saving results. 
        If S3, should be a valid S3 path, E.g. s3://...
        If local, should be a valid local path, E.g. /data/results
        If dandi, should be a valid Dandiset uri, E.g. https://dandiarchive.org/dandiset/000001
    - SORTERS_NAMES_LIST : List of sorters to run on source data, stored as comma-separated values.
    - SORTERS_KWARGS : Parameters for each sorter, stored as a dictionary.
    - TEST_WITH_TOY_RECORDING : Runs script with a toy dataset.
    - TEST_WITH_SUB_RECORDING : Runs script with the first 4 seconds of target dataset.
    - TEST_SUB_RECORDING_N_FRAMES : Number of frames to use for sub-recording.
    - LOG_TO_FILE : If True, logs will be saved to a file in /logs folder.

    If running this in any AWS service (e.g. Batch, ECS, EC2...) the access to other AWS services 
    such as S3 storage can be given to the container by an IAM role.
    Otherwise, if running this outside of AWS, these ENV variables should be present in the running container:
    - AWS_DEFAULT_REGION
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY

    If saving results to DANDI archive, or reading from embargoed dandisets, the following ENV variables should be present in the running container:
    - DANDI_API_KEY
    - DANDI_API_KEY_STAGING
    """

    # Order of priority for definition of running arguments:
    # 1. passed by function
    # 2. retrieved from ENV vars
    # 3. default value
    if not run_identifier:
        run_identifier = os.environ.get("RUN_IDENTIFIER", datetime.now().strftime("%Y%m%d%H%M%S"))
    if not source:
        source = os.environ.get("SOURCE", None)
        if source == "None":
            source = None
    if not source_data_paths:
        source_data_paths = eval(os.environ.get("SOURCE_DATA_PATHS", "{}"))
    if not source_data_type:
        source_data_type = os.environ.get("SOURCE_DATA_TYPE", "nwb")
    if not recording_kwargs:
        recording_kwargs = ast.literal_eval(os.environ.get("RECORDING_KWARGS", "{}"))
    if not output_destination:
        output_destination = os.environ.get("OUTPUT_DESTINATION", "s3")
    if not output_path:
        output_path = os.environ.get("OUTPUT_PATH", None)
        if output_path == "None":
            output_path = None
    if not sorters_names_list:
        sorters_names_list = os.environ.get("SORTERS_NAMES_LIST", '["kilosort3"]')
        sorters_names_list = [s.strip().replace("\"", "").replace("\'", "") for s in sorters_names_list.strip('][').split(',')]
    if not sorters_kwargs:
        sorters_kwargs = eval(os.environ.get("SORTERS_KWARGS", "{}"))
    if test_with_toy_recording is None:
        test_with_toy_recording = os.environ.get("TEST_WITH_TOY_RECORDING", "False").lower() in ('true', '1', 't')
    if test_with_subrecording is None:
        test_with_subrecording = os.environ.get("TEST_WITH_SUB_RECORDING", "False").lower() in ('true', '1', 't')
    if not test_subrecording_n_frames:
        test_subrecording_n_frames = int(os.environ.get("TEST_SUBRECORDING_N_FRAMES", 300000))
    if log_to_file is None:
        log_to_file = os.environ.get("LOG_TO_FILE", "False").lower() in ('true', '1', 't')

    # Set up logging
    logger = make_logger(run_identifier=run_identifier, log_to_file=log_to_file)
    
    filterwarnings(action="ignore", message="No cached namespaces found in .*")
    filterwarnings(action="ignore", message="Ignoring cached namespace .*")

    # Checks
    if source not in ["local", "s3", "dandi"]:
        logger.error(f"Source {source} not supported. Choose from: local, s3, dandi.")
        raise ValueError(f"Source {source} not supported. Choose from: local, s3, dandi.")
    
    if source_data_type not in ["nwb", "spikeglx"]:
        logger.error(f"Data type {source_data_type} not supported. Choose from: nwb, spikeglx.")
        raise ValueError(f"Data type {source_data_type} not supported. Choose from: nwb, spikeglx.")
    
    if len(source_data_paths) == 0:
        logger.error(f"No source data paths provided.")
        raise ValueError(f"No source data paths provided.")
    
    if output_destination not in ["local", "s3", "dandi"]:
        logger.error(f"Output destination {output_destination} not supported. Choose from: local, s3, dandi.")
        raise ValueError(f"Output destination {output_destination} not supported. Choose from: local, s3, dandi.")

    if output_destination == "s3":
        if not output_path.startswith("s3://"):
            logger.error(f"Data url {output_path} is not a valid S3 path. E.g. s3://...")
            raise ValueError(f"Data url {output_path} is not a valid S3 path. E.g. s3://...")
        output_path_parsed = output_path.split("s3://")[-1]
        output_s3_bucket = output_path_parsed.split("/")[0]
        output_s3_bucket_folder = "/".join(output_path_parsed.split("/")[1:])

    s3_client = boto3.client('s3')

    # Test with toy recording
    if test_with_toy_recording:
        logger.info("Generating toy recording...")
        recording, _ = se.toy_example(
            duration=20,
            seed=0,
            num_channels=64,
            num_segments=1
        )
        recording = recording.save()
    
    # Load data from S3
    elif source == "s3":
        for k, data_url in source_data_paths.items():
            if not data_url.startswith("s3://"):
                logger.error(f"Data url {data_url} is not a valid S3 path. E.g. s3://...")
                raise ValueError(f"Data url {data_url} is not a valid S3 path. E.g. s3://...")
            logger.info(f"Downloading data from S3: {data_url}")
            data_path = data_url.split("s3://")[-1]
            bucket_name = data_path.split("/")[0]
            file_path = "/".join(data_path.split("/")[1:])
            file_name = download_file_from_s3(
                client=s3_client,
                bucket_name=bucket_name, 
                file_path=file_path,
            )

        logger.info("Reading recording...")
        # E.g.: se.read_spikeglx(folder_path="/data", stream_id="imec.ap")
        if source_data_type == "spikeglx":
            recording = se.read_spikeglx(
                folder_path="/data",
                **recording_kwargs
            )
        elif source_data_type == "nwb":
            recording = se.read_nwb_recording(
                file_path=f"/data/{file_name}",
                **recording_kwargs
            )

    elif source == "dandi":
        dandiset_s3_file_url = source_data_paths["file"]
        if not dandiset_s3_file_url.startswith("https://dandiarchive"):
            raise Exception(f"DANDISET_S3_FILE_URL should be a valid Dandiset S3 url. Value received was: {dandiset_s3_file_url}")

        if not test_with_subrecording:            
            logger.info(f"Downloading dataset: {dandiset_s3_file_url}")
            download_file_from_url(dandiset_s3_file_url)
            
            logger.info("Reading recording from NWB...")
            recording = se.read_nwb_recording(
                file_path="/data/filename.nwb",
                **recording_kwargs
            )
        else:
            logger.info("Reading recording from NWB...")
            recording = se.read_nwb_recording(
                file_path=dandiset_s3_file_url,
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
            output_results_folder = f"/results/sorting/{run_identifier}_{sorter_name}"
            sorting = run_sorter_local(
                sorter_name, 
                recording, 
                output_folder=output_results_folder,
                remove_existing_folder=True, 
                delete_output_folder=True,
                verbose=True, 
                raise_error=True, 
                with_output=True,
                **sorter_job_kwargs
            )
            sorting_list.append(sorting)
            sorting.save_to_folder(folder=f'/results/sorting/{run_identifier}_{sorter_name}/sorter_exported')

            if output_destination == "local":
                # Copy sorting results to local - already done by mounted volume
                pass
            elif output_destination == "s3":
                # Upload sorting results to S3
                upload_all_files_to_bucket_folder(
                    logger=logger,
                    client=s3_client, 
                    bucket_name=output_s3_bucket, 
                    bucket_folder=output_s3_bucket_folder,
                    local_folder=f'/results/sorting/{run_identifier}_{sorter_name}/sorter_exported'
                )
        except Exception as e:
            logger.info(f"Error running sorter {sorter_name}: {e}")
            print(f"Error running sorter {sorter_name}: {e}")
            if output_destination == "local":
                # Copy error logs to local - already done by mounted volume
                pass
            elif output_destination == "s3":
                # upload error logs to S3
                upload_all_files_to_bucket_folder(
                    logger=logger,
                    client=s3_client,
                    bucket_name=output_s3_bucket,
                    bucket_folder=output_s3_bucket_folder,
                    local_folder=output_results_folder
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


    # Write sorting results to NWB
    logger.info("Writing sorting results to NWB...")
    metadata = {
        "NWBFile": {
            "session_start_time": datetime.now().isoformat(),
        },
        # TODO - use subject metadata from Job request data
        "Subject": {
            "age": "P23W",
            "sex": "M",
            "species": "Mus musculus",
            "subject_id": "test_subject",
            "weight": "20g",
        },
    }
    results_nwb_path = Path(f"/results/nwb/{run_identifier}/")
    if not results_nwb_path.exists():
        results_nwb_path.mkdir(parents=True)
    output_nwbfile_path = f"/results/nwb/{run_identifier}/{run_identifier}.nwb"
    write_sorting(
        sorting=sorting,
        nwbfile_path=output_nwbfile_path,
        metadata=metadata,
        overwrite=True
    )

    # Inspect nwb file for CRITICAL best practices violations
    logger.info("Inspecting NWB file...")
    with NWBHDF5IO(path=output_nwbfile_path, mode="r", load_namespaces=True) as io:
        nwbfile = io.read()
        critical_violations = list(inspect_nwbfile_object(nwbfile_object=nwbfile, importance_threshold="CRITICAL"))
    if len(critical_violations) > 0:
        logger.info(f"Found critical violations in resulting NWB file: {critical_violations}")
        raise Exception(f"Found critical violations in resulting NWB file: {critical_violations}")

    # Upload results
    if output_destination == "s3":
        # Upload results to S3
        upload_file_to_bucket(
            logger=logger,
            client=s3_client,
            bucket_name=output_s3_bucket,
            bucket_folder=output_s3_bucket_folder,
            local_file_path=output_nwbfile_path,
        )

    elif output_destination == "dandi":
        # Check if DANDI_API_KEY is present in ENV variables
        DANDI_API_KEY = os.environ.get("DANDI_API_KEY", None)
        if DANDI_API_KEY is None:
            raise Exception("DANDI_API_KEY not found in ENV variables. Cannot upload results to DANDI.")
        
        # Download DANDI dataset
        logger.info(f"Downloading dandiset: {output_path}")
        dandiset_id_number = output_path.split("/")[-1]
        dandiset_local_base_path = Path("dandiset").resolve()
        dandiset_local_full_path = dandiset_local_base_path / dandiset_id_number
        if not dandiset_local_base_path.exists():
            dandiset_local_base_path.mkdir(parents=True)
        try:
            download(
                urls=[output_path],
                output_dir=str(dandiset_local_base_path),
                get_metadata=True,
                get_assets=False,
                sync=False,
            )
        except subprocess.CalledProcessError as e:
            raise Exception("Error downloading DANDI dataset.\n{e}")
        
        # Organize DANDI dataset
        logger.info(f"Organizing dandiset: {dandiset_id_number}")
        organize(
            paths=output_nwbfile_path,
            dandiset_path=str(dandiset_local_full_path),
        )

        # Validate nwb file for DANDI
        logger.info("Validating NWB file for DANDI...")
        validation_errors = [v for v in validate(str(dandiset_local_full_path))]
        if len(validation_errors) > 0:
            logger.info(f"Found DANDI validation errors in resulting NWB file: {validation_errors}")
            raise Exception(f"Found DANDI validation errors in resulting NWB file: {validation_errors}")

        # Upload results to DANDI
        logger.info(f"Uploading results to DANDI: {output_path}")
        dandi_instance = "dandi-staging" if "staging" in output_path else "dandi"
        if dandi_instance == "dandi-staging":
            DANDI_API_KEY = os.environ.get("DANDI_API_KEY_STAGING", None)
            if DANDI_API_KEY is None:
                raise Exception("DANDI_API_KEY_STAGING not found in ENV variables. Cannot upload results to DANDI staging.")
        # upload(
        #     paths=[str(dandiset_local_full_path)],
        #     existing="refresh",
        #     validation="require",
        #     dandi_instance=dandi_instance,
        #     sync=True,
        # )
    else:
        # Upload results to local - already done by mounted volume
        pass

    logger.info("Sorting job completed successfully!")


if __name__ == '__main__':
    main()

# Known issues:
#
# Kilosort3:
# Error using accumarray - First input SUBS must contain positive integer subscripts.
# https://github.com/MouseLand/Kilosort/issues/463