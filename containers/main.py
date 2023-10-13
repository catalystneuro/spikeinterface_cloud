import boto3
import json
import os
import ast
import subprocess
import shutil
import numpy as np
import time
from warnings import filterwarnings
from datetime import datetime
from pathlib import Path


# SPIKEINTERFACE
import spikeinterface as si
import spikeinterface.extractors as se
import spikeinterface.sorters as ss
import spikeinterface.preprocessing as spre
import spikeinterface.postprocessing as spost
import spikeinterface.qualitymetrics as sqm
import spikeinterface.curation as sc
import spikeinterface.widgets as sw

# NWB
from neuroconv.tools.spikeinterface import write_sorting, write_recording
from nwbinspector import inspect_nwbfile_object
from pynwb import NWBHDF5IO, NWBFile

# DANDI
from dandi.validate import validate
from dandi.organize import organize
from dandi.upload import upload
from dandi.download import download

from utils import (
    make_logger,
    validate_not_none,
    download_file_from_s3,
    upload_file_to_bucket,
    upload_all_files_to_bucket_folder,
    download_file_from_url,
)


def main(
    run_at: str,
    run_identifier: str,
    run_description: str,
    test_with_toy_recording: bool = None,
    test_with_subrecording: bool = None,
    test_subrecording_n_frames: int = None,
    log_to_file: bool = None,
    source_name: str = None,
    source_data_type: str = None,
    source_data_paths: dict = None,
    recording_kwargs: dict = None,
    preprocessing_kwargs: dict = None,
    sorter_kwargs: dict = None,
    postprocessing_kwargs: dict = None,
    curation_kwargs: dict = None,
    visualization_kwargs: dict = None,
    output_destination: str = None,
    output_path: str = None
):
    """
    This script should run in an ephemeral Docker container and will:
    1. download a dataset with raw electrophysiology traces from a specfied location
    2. run a SpikeInterface pipeline, including preprocessing, spike sorting, postprocessing and curation
    3. save the results in a target S3 bucket or DANDI archive

    If running this in any AWS service (e.g. Batch, ECS, EC2...) the access to other AWS services
    such as S3 storage can be given to the container by an IAM role.
    Otherwise, if running this outside of AWS, these ENV variables should be present in the running container:
    - AWS_DEFAULT_REGION
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY

    If saving results to DANDI archive, or reading from embargoed dandisets, the following ENV variables should be present in the running container:
    - DANDI_API_KEY
    - DANDI_API_KEY_STAGING

    Parameters
    ----------
    run_at : str
        Where to run the sorting job. Choose from: aws, local.
    run_identifier : str
        Unique identifier for this run.
    run_description : str
        Description for this run.
    test_with_toy_recording : bool
        If True, runs script with a toy dataset.
    test_with_subrecording : bool
        If True, runs script with a subrecording of the source dataset.
    test_subrecording_n_frames : int
        Number of frames to use for sub-recording.
    log_to_file : bool
        If True, logs will be saved to a file in /logs folder.
    source_name : str
        Source of input data. Choose from: local, s3, dandi.
    source_data_type : str
        Data type to be read. Choose from: nwb, spikeglx.
    source_data_paths : dict
        Dictionary with paths to source data. Keys are names of data files, values are urls or paths.
    recording_kwargs : dict
        SpikeInterface recording keyword arguments, specific to chosen dataset type.
    preprocessing_kwargs : dict
        SpikeInterface preprocessing keyword arguments.
    sorter_kwargs : dict
        SpikeInterface sorter keyword arguments.
    postprocessing_kwargs : dict
        SpikeInterface postprocessing keyword arguments.
    curation_kwargs : dict
        SpikeInterface curation keyword arguments.
    visualization_kwargs : dict
        SpikeInterface visualization keyword arguments.
    output_destination : str
        Destination for saving results. Choose from: local, s3, dandi.
    output_path : str
        Path for saving results.
        If S3, should be a valid S3 path, E.g. s3://...
        If local, should be a valid local path, E.g. /data/results
        If dandi, should be a valid Dandiset uri, E.g. https://dandiarchive.org/dandiset/000001
    """
    # Set up logging
    logger = make_logger(run_identifier=run_identifier, log_to_file=log_to_file)

    filterwarnings(action="ignore", message="No cached namespaces found in .*")
    filterwarnings(action="ignore", message="Ignoring cached namespace .*")

    # Checks
    if source_name not in ["local", "s3", "dandi"]:
        logger.error(f"Source {source_name} not supported. Choose from: local, s3, dandi.")
        raise ValueError(f"Source {source_name} not supported. Choose from: local, s3, dandi.")

    # TODO: here we could eventually leverage spikeinterface and add more options
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

    # Set SpikeInterface global job kwargs
    si.set_global_job_kwargs(
        n_jobs=os.cpu_count(), 
        chunk_duration="1s", 
        progress_bar=False
    )

    # Create SpikeInterface folders
    data_folder = Path("data/")
    data_folder.mkdir(exist_ok=True)
    scratch_folder = Path("scratch/")
    scratch_folder.mkdir(exist_ok=True)
    results_folder = Path("results/")
    results_folder.mkdir(exist_ok=True)
    tmp_folder = scratch_folder / "tmp"
    if tmp_folder.is_dir():
        shutil.rmtree(tmp_folder)
    tmp_folder.mkdir()

    # S3 client
    if source_name == "s3" or output_destination == "s3":
        s3_client = boto3.client("s3")

    # Test with toy recording
    if test_with_toy_recording:
        logger.info("Generating toy recording...")
        recording, _ = se.toy_example(duration=20, seed=0, num_channels=64, num_segments=1)
        recording = recording.save()
        recording_name = "toy"

    # Load data from S3
    elif source_name == "s3":
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
            recording = se.read_spikeglx(folder_path="/data", **recording_kwargs)
        elif source_data_type == "nwb":
            recording = se.read_nwb_recording(file_path=f"/data/{file_name}", **recording_kwargs)
        recording_name = "recording_on_s3"

    # Load data from DANDI archive
    elif source_name == "dandi":
        dandiset_s3_file_url = source_data_paths["file"]
        if not dandiset_s3_file_url.startswith("https://dandiarchive"):
            raise Exception(
                f"DANDISET_S3_FILE_URL should be a valid Dandiset S3 url. Value received was: {dandiset_s3_file_url}"
            )
        if not test_with_subrecording:
            logger.info(f"Downloading dataset: {dandiset_s3_file_url}")
            download_file_from_url(dandiset_s3_file_url)
            logger.info("Reading recording from NWB...")
            recording = se.read_nwb_recording(file_path="/data/filename.nwb", **recording_kwargs)
        else:
            logger.info("Reading recording from NWB...")
            recording = se.read_nwb_recording(file_path=dandiset_s3_file_url, stream_mode="fsspec", **recording_kwargs)
        recording_name = "recording_on_dandi"

    # TODO - Load data from local files
    elif source_name == "local":
        pass

    # Run with subrecording
    if test_with_subrecording:
        n_frames = int(min(test_subrecording_n_frames, recording.get_num_frames()))
        recording = recording.frame_slice(start_frame=0, end_frame=n_frames)

    # ------------------------------------------------------------------------------------
    # Preprocessing
    # ------------------------------------------------------------------------------------
    logger.info("Starting preprocessing...")
    preprocessing_notes = ""
    preprocessed_folder = tmp_folder / "preprocessed"
    t_preprocessing_start = time.perf_counter()
    logger.info(f"\tDuration: {np.round(recording.get_total_duration(), 2)} s")

    if "inter_sample_shift" in recording.get_property_keys():
        recording_ps_full = spre.phase_shift(recording, **preprocessing_kwargs["phase_shift"])
    else:
        recording_ps_full = recording

    recording_hp_full = spre.highpass_filter(recording_ps_full, **preprocessing_kwargs["highpass_filter"])
    # IBL bad channel detection
    _, channel_labels = spre.detect_bad_channels(recording_hp_full, **preprocessing_kwargs["detect_bad_channels"])
    dead_channel_mask = channel_labels == "dead"
    noise_channel_mask = channel_labels == "noise"
    out_channel_mask = channel_labels == "out"
    logger.info(f"\tBad channel detection:")
    logger.info(
        f"\t\t- dead channels - {np.sum(dead_channel_mask)}\n\t\t- noise channels - {np.sum(noise_channel_mask)}\n\t\t- out channels - {np.sum(out_channel_mask)}"
    )
    dead_channel_ids = recording_hp_full.channel_ids[dead_channel_mask]
    noise_channel_ids = recording_hp_full.channel_ids[noise_channel_mask]
    out_channel_ids = recording_hp_full.channel_ids[out_channel_mask]

    all_bad_channel_ids = np.concatenate((dead_channel_ids, noise_channel_ids, out_channel_ids))
    max_bad_channel_fraction_to_remove = preprocessing_kwargs["max_bad_channel_fraction_to_remove"]
    if len(all_bad_channel_ids) >= int(max_bad_channel_fraction_to_remove * recording.get_num_channels()):
        logger.info(
            f"\tMore than {max_bad_channel_fraction_to_remove * 100}% bad channels ({len(all_bad_channel_ids)}). "
            f"Skipping further processing for this recording."
        )
        preprocessing_notes += f"\n- Found {len(all_bad_channel_ids)} bad channels. Skipping further processing\n"
        # in this case, we don't bother sorting
        return
    else:
        if preprocessing_kwargs["remove_out_channels"]:
            logger.info(f"\tRemoving {len(out_channel_ids)} out channels")
            recording_rm_out = recording_hp_full.remove_channels(out_channel_ids)
            preprocessing_notes += f"\n- Removed {len(out_channel_ids)} outside of the brain."
        else:
            recording_rm_out = recording_hp_full

        recording_processed_cmr = spre.common_reference(recording_rm_out, **preprocessing_kwargs["common_reference"])

        bad_channel_ids = np.concatenate((dead_channel_ids, noise_channel_ids))
        recording_interp = spre.interpolate_bad_channels(recording_rm_out, bad_channel_ids)
        recording_hp_spatial = spre.highpass_spatial_filter(
            recording_interp, **preprocessing_kwargs["highpass_spatial_filter"]
        )

        preproc_strategy = preprocessing_kwargs["preprocessing_strategy"]
        if preproc_strategy == "cmr":
            recording_processed = recording_processed_cmr
        else:
            recording_processed = recording_hp_spatial

        if preprocessing_kwargs["remove_bad_channels"]:
            logger.info(f"\tRemoving {len(bad_channel_ids)} channels after {preproc_strategy} preprocessing")
            recording_processed = recording_processed.remove_channels(bad_channel_ids)
            preprocessing_notes += f"\n- Removed {len(bad_channel_ids)} bad channels after preprocessing.\n"
        recording_processed = recording_processed.save(folder=preprocessed_folder)

    t_preprocessing_end = time.perf_counter()
    elapsed_time_preprocessing = np.round(t_preprocessing_end - t_preprocessing_start, 2)
    logger.info(f"Preprocessing time: {elapsed_time_preprocessing}s")

    # ------------------------------------------------------------------------------------
    # Spike Sorting
    # ------------------------------------------------------------------------------------
    sorter_name = sorter_kwargs["sorter_name"]
    logger.info(f"\n\nStarting spike sorting with {sorter_name}")
    spikesorting_notes = ""
    sorting_params = None

    t_sorting_start = time.perf_counter()
    # try results here
    spikesorted_raw_output_folder = scratch_folder / "spikesorted_raw"
    sorting_output_folder = results_folder / "spikesorted"

    # we need to concatenate segments for KS
    if recording_processed.get_num_segments() > 1:
        recording_processed = si.concatenate_recordings([recording_processed])

    # Run sorter
    try:
        sorting = ss.run_sorter(
            sorter_name,
            recording_processed,
            output_folder=spikesorted_raw_output_folder,
            verbose=False,
            delete_output_folder=True,
            **sorter_kwargs,
        )
    except Exception as e:
        # save log to results
        sorting_output_folder.mkdir()
        shutil.copy(spikesorted_raw_output_folder / "spikeinterface_log.json", sorting_output_folder)
    logger.info(f"\tRaw sorting output: {sorting}")
    spikesorting_notes += f"\n- KS2.5 found {len(sorting.unit_ids)} units, "
    if sorting_params is None:
        sorting_params = sorting.sorting_info["params"]

    # remove empty units
    sorting = sorting.remove_empty_units()

    # remove spikes beyond num_samples (if any)
    sorting = sc.remove_excess_spikes(sorting=sorting, recording=recording_processed)
    logger.info(f"\tSorting output without empty units: {sorting}")
    spikesorting_notes += f"{len(sorting.unit_ids)} after removing empty templates.\n"

    # split back to get original segments
    if recording_processed.get_num_segments() > 1:
        sorting = si.split_sorting(sorting, recording_processed)

    # save results
    logger.info(f"\tSaving results to {sorting_output_folder}")
    sorting = sorting.save(folder=sorting_output_folder)

    t_sorting_end = time.perf_counter()
    elapsed_time_sorting = np.round(t_sorting_end - t_sorting_start, 2)
    logger.info(f"Spike sorting time: {elapsed_time_sorting}s")

    # ------------------------------------------------------------------------------------
    # Postprocessing
    # ------------------------------------------------------------------------------------
    logger.info("\n\Starting postprocessing...")
    postprocessing_notes = ""
    t_postprocessing_start = time.perf_counter()

    # first extract some raw waveforms in memory to deduplicate based on peak alignment
    wf_dedup_folder = tmp_folder / "postprocessed" / recording_name
    we_raw = si.extract_waveforms(
        recording_processed, sorting, folder=wf_dedup_folder, **postprocessing_kwargs["waveforms_deduplicate"]
    )
    # de-duplication
    sorting_deduplicated = sc.remove_redundant_units(we_raw, duplicate_threshold=curation_kwargs["duplicate_threshold"])
    logger.info(
        f"\tNumber of original units: {len(we_raw.sorting.unit_ids)} -- Number of units after de-duplication: {len(sorting_deduplicated.unit_ids)}"
    )
    postprocessing_notes += (
        f"\n- Removed {len(sorting.unit_ids) - len(sorting_deduplicated.unit_ids)} duplicated units.\n"
    )
    deduplicated_unit_ids = sorting_deduplicated.unit_ids
    # use existing deduplicated waveforms to compute sparsity
    sparsity_raw = si.compute_sparsity(we_raw, **postprocessing_kwargs["sparsity"])
    sparsity_mask = sparsity_raw.mask[sorting.ids_to_indices(deduplicated_unit_ids), :]
    sparsity = si.ChannelSparsity(mask=sparsity_mask, unit_ids=deduplicated_unit_ids, channel_ids=recording.channel_ids)
    shutil.rmtree(wf_dedup_folder)
    del we_raw

    wf_sparse_folder = results_folder / "postprocessed"

    # now extract waveforms on de-duplicated units
    logger.info(f"\tSaving sparse de-duplicated waveform extractor folder")
    we = si.extract_waveforms(
        recording_processed,
        sorting_deduplicated,
        folder=wf_sparse_folder,
        sparsity=sparsity,
        sparse=True,
        overwrite=True,
        **postprocessing_kwargs["waveforms"],
    )
    logger.info("\tComputing spike amplitides")
    spike_amplitudes = spost.compute_spike_amplitudes(we, **postprocessing_kwargs["spike_amplitudes"])
    logger.info("\tComputing unit locations")
    unit_locations = spost.compute_unit_locations(we, **postprocessing_kwargs["locations"])
    logger.info("\tComputing spike locations")
    spike_locations = spost.compute_spike_locations(we, **postprocessing_kwargs["locations"])
    logger.info("\tComputing correlograms")
    ccg, bins = spost.compute_correlograms(we, **postprocessing_kwargs["correlograms"])
    logger.info("\tComputing ISI histograms")
    isi, bins = spost.compute_isi_histograms(we, **postprocessing_kwargs["isis"])
    logger.info("\tComputing template similarity")
    sim = spost.compute_template_similarity(we, **postprocessing_kwargs["similarity"])
    logger.info("\tComputing template metrics")
    tm = spost.compute_template_metrics(we, **postprocessing_kwargs["template_metrics"])
    logger.info("\tComputing PCA")
    pca = spost.compute_principal_components(we, **postprocessing_kwargs["principal_components"])
    logger.info("\tComputing quality metrics")
    qm = sqm.compute_quality_metrics(we, **postprocessing_kwargs["quality_metrics"])

    t_postprocessing_end = time.perf_counter()
    elapsed_time_postprocessing = np.round(t_postprocessing_end - t_postprocessing_start, 2)
    logger.info(f"Postprocessing time: {elapsed_time_postprocessing}s")

    # ------------------------------------------------------------------------------------
    # Curation
    # ------------------------------------------------------------------------------------
    logger.info("\n\Starting curation...")
    curation_notes = ""
    t_curation_start = time.perf_counter()

    # curation query
    isi_violations_ratio_thr = curation_kwargs["isi_violations_ratio_threshold"]
    presence_ratio_thr = curation_kwargs["presence_ratio_threshold"]
    amplitude_cutoff_thr = curation_kwargs["amplitude_cutoff_threshold"]

    curation_query = f"isi_violations_ratio < {isi_violations_ratio_thr} and presence_ratio > {presence_ratio_thr} and amplitude_cutoff < {amplitude_cutoff_thr}"
    logger.info(f"Curation query: {curation_query}")
    curation_notes += f"Curation query: {curation_query}\n"

    postprocessed_folder = results_folder / "postprocessed"

    recording_folder = postprocessed_folder / recording_name

    we = si.load_waveforms(recording_folder)

    # get quality metrics
    qm = we.load_extension("quality_metrics").get_data()
    qm_curated = qm.query(curation_query)
    curated_unit_ids = qm_curated.index.values

    # flag units as good/bad depending on QC selection
    qc_quality = [True if unit in curated_unit_ids else False for unit in we.sorting.unit_ids]
    sorting_precurated = we.sorting
    sorting_precurated.set_property("default_qc", qc_quality)
    sorting_precurated.save(folder=results_folder / "sorting_precurated" / recording_name)
    curation_notes += (
        f"{recording_name}:\n- {np.sum(qc_quality)}/{len(sorting_precurated.unit_ids)} passing default QC.\n"
    )

    t_curation_end = time.perf_counter()
    elapsed_time_curation = np.round(t_curation_end - t_curation_start, 2)
    logger.info(f"Curation time: {elapsed_time_curation}s")

    # ------------------------------------------------------------------------------------
    # TODO: Visualization with FIGURL (needs credentials)
    # ------------------------------------------------------------------------------------



    # ------------------------------------------------------------------------------------
    # Conversion and upload
    # ------------------------------------------------------------------------------------
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
    results_nwb_folder = results_folder / "nwb" / run_identifier
    results_nwb_folder.mkdir(parents=True, exist_ok=True)
    output_nwbfile_path = results_nwb_folder / f"{run_identifier}.nwb"

    # TODO: Consider writing waveforms instead of sorting
    # add sorting properties
    # unit locations
    sorting.set_property("unit_locations", unit_locations)
    # quality metrics
    for metric in qm.columns:
        sorting.set_property(metric, qm[metric])
    # template metrics
    for metric in tm.columns:
        sorting.set_property(metric, tm[metric])
    write_sorting(sorting=sorting, nwbfile_path=output_nwbfile_path, metadata=metadata, overwrite=True)

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
                raise Exception(
                    "DANDI_API_KEY_STAGING not found in ENV variables. Cannot upload results to DANDI staging."
                )
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


if __name__ == "__main__":
    # Get run kwargs from ENV variables
    run_kwargs = json.loads(os.environ.get("SI_RUN_KWARGS", "{}"))
    run_at = validate_not_none(run_kwargs, "run_at")
    run_identifier = run_kwargs.get("run_identifier", datetime.now().strftime("%Y%m%d%H%M%S"))
    run_description = run_kwargs.get("run_description", "")
    test_with_toy_recording = run_kwargs.get("test_with_toy_recording", "False")
    test_with_subrecording = run_kwargs.get("test_with_subrecording", "False")
    test_subrecording_n_frames = int(run_kwargs.get("test_subrecording_n_frames", 30000))
    log_to_file = run_kwargs.get("log_to_file", "False")

    # Get source data kwargs from ENV variables
    source_data_kwargs = json.loads(os.environ.get("SI_SOURCE_DATA_KWARGS", "{}"))
    source_name = validate_not_none(source_data_kwargs, "source_name")
    source_data_type = validate_not_none(source_data_kwargs, "source_data_type")
    source_data_paths = validate_not_none(source_data_kwargs, "source_data_paths")

    # Get recording kwargs from ENV variables
    recording_kwargs = json.loads(os.environ.get("SI_RECORDING_KWARGS", "{}"))
    
    # Get preprocessing kwargs from ENV variables
    preprocessing_kwargs = json.loads(os.environ.get("SI_PREPROCESSING_KWARGS", "{}"))

    # Get sorter kwargs from ENV variables
    sorter_kwargs = json.loads(os.environ.get("SI_SORTER_KWARGS", "{}"))
    
    # Get postprocessing kwargs from ENV variables
    postprocessing_kwargs = json.loads(os.environ.get("SI_POSTPROCESSING_KWARGS", "{}"))

    # Get curation kwargs from ENV variables
    curation_kwargs = json.loads(os.environ.get("SI_CURATION_KWARGS", "{}"))

    # Get visualization kwargs from ENV variables
    visualization_kwargs = json.loads(os.environ.get("SI_VISUALIZATION_KWARGS", "{}"))

    # Get output kwargs from ENV variables
    output_kwargs = json.loads(os.environ.get("SI_OUTPUT_DATA_KWARGS", "{}"))
    output_destination = validate_not_none(output_kwargs, "output_destination")
    output_path = validate_not_none(output_kwargs, "output_path")

    # # Run main function
    # main(
    #     run_at=run_at,
    #     run_identifier=run_identifier,
    #     run_description=run_description,
    #     test_with_toy_recording=test_with_toy_recording,
    #     test_with_subrecording=test_with_subrecording,
    #     test_subrecording_n_frames=test_subrecording_n_frames,
    #     log_to_file=log_to_file,
    #     source_name=source_name,
    #     source_data_type=source_data_type,
    #     source_data_paths=source_data_paths,
    #     recording_kwargs=recording_kwargs,
    #     preprocessing_kwargs=preprocessing_kwargs,
    #     sorter_kwargs=sorter_kwargs,
    #     postprocessing_kwargs=postprocessing_kwargs,
    #     curation_kwargs=curation_kwargs,
    #     visualization_kwargs=visualization_kwargs,
    #     output_destination=output_destination,
    #     output_path=output_path,
    # )

    print("\nRun at: ", run_at)
    print("\nRun identifier: ", run_identifier)
    print("\nRun description: ", run_description)
    print("\nTest with toy recording: ", test_with_toy_recording)
    print("\nTest with subrecording: ", test_with_subrecording)
    print("\nTest subrecording n frames: ", test_subrecording_n_frames)
    print("\nLog to file: ", log_to_file)
    print("\nSource name: ", source_name)
    print("\nSource data type: ", source_data_type)
    print("\nSource data paths: ", source_data_paths)
    print("\nRecording kwargs: ", recording_kwargs)
    print("\nPreprocessing kwargs: ", preprocessing_kwargs)
    print("\nSorter kwargs: ", sorter_kwargs)
    print("\nPostprocessing kwargs: ", postprocessing_kwargs)
    print("\nCuration kwargs: ", curation_kwargs)
    print("\nVisualization kwargs: ", visualization_kwargs)
    print("\nOutput destination: ", output_destination)
    print("\nOutput path: ", output_path)



# Known issues:
#
# Kilosort3:
# Error using accumarray - First input SUBS must contain positive integer subscripts.
# https://github.com/MouseLand/Kilosort/issues/463
