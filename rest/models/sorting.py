from pydantic import BaseModel
from typing import List
from enum import Enum


class OutputDestination(str, Enum):
    s3 = "s3"
    dandi = "dandi"
    local = "local"


class SourceDataType(str, Enum):
    nwb = "nwb"
    spikeglx = "spikeglx"


class Source(str, Enum):
    s3 = "s3"
    dandi = "dandi"


class RunAt(str, Enum):
    aws = "aws"
    local = "local"


class SortingData(BaseModel):
    run_at: RunAt = "local"
    run_identifier: str = None
    run_description: str = None
    source: Source = None
    source_data_type: SourceDataType = None
    source_data_paths: dict = None
    subject_metadata: dict = None
    recording_kwargs: dict = None
    output_destination: OutputDestination = None
    output_path: str = None
    sorters_names_list: List[str] = None
    sorters_kwargs: dict = None
    test_with_toy_recording: bool = None
    test_with_subrecording: bool = None
    test_subrecording_n_frames: int = None
    log_to_file: bool = None