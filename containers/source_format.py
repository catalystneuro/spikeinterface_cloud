

source_data = {
    "source": "dandi",  # or "s3"
    "source_data_type": "nwb",  # or "spikeglx"
    "source_data_urls": [
        "https://dandiarchive.org/dandiset/000003/0.210813.1807"
    ],
    "recording_kwargs": {
        "electrical_series_name": "ElectricalSeries",
    }
}


source_data_2 = {
    "source": "s3",
    "source_data_type": "spikeglx",
    "source_data_urls": [
        "s3://bucket/path/to/file",
        "s3://bucket/path/to/file2",
    ],
    "recording_kwargs": {}
}