from pydantic import BaseModel
from typing import List


class SortingData(BaseModel):
    run_at: str = "local"
    run_identifier: str = None
    run_description: str = None
    source: str = None
    source_data_type: str = None
    source_data_urls: List[str] = None
    recording_kwargs: dict = None
    target_output_type: str = None
    output_path: str = None
    sorters_names_list: list = None
    sorters_kwargs: dict = None
    test_with_toy_recording: bool = None
    test_with_subrecording: bool = None
    test_subrecording_n_frames: int = None
    log_to_file: bool = None