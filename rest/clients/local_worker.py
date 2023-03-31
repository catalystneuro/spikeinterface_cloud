import requests
import aiohttp
import asyncio

from core.logger import logger


class LocalWorkerClient:

    def __init__(self, endpoint: str = "http://worker:5000/worker/run"):
        self.endpoint = endpoint
        self.logger = logger


    async def make_request(self, payload: dict) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, json=payload) as response:
                if response.status == 200:
                    self.logger.info("Success!")
                else:
                    self.logger.info(f"Error {response.status}: {await response.text()}")

    async def run_sorting(
        self,
        source_aws_s3_bucket: str,
        source_aws_s3_bucket_folder: str,
        dandiset_s3_file_url: str,
        dandiset_file_es_name: str,
        target_output_type: str,
        target_aws_s3_bucket: str,
        target_aws_s3_bucket_folder: str,
        data_type: str,
        recording_kwargs: str,
        sorters_names_list: str,
        sorters_kwargs: dict,
        test_with_toy_recording: bool,
        test_with_subrecording: bool,
        test_subrecording_n_frames: int,
    ) -> None:
        payload = {
            "source_aws_s3_bucket": source_aws_s3_bucket,
            "source_aws_s3_bucket_folder": source_aws_s3_bucket_folder,
            "dandiset_s3_file_url": dandiset_s3_file_url,
            "dandiset_file_es_name": dandiset_file_es_name,
            "target_output_type": target_output_type,
            "target_aws_s3_bucket": target_aws_s3_bucket,
            "target_aws_s3_bucket_folder": target_aws_s3_bucket_folder,
            "data_type": data_type,
            "recording_kwargs": recording_kwargs,
            "sorters_names_list": sorters_names_list,
            "sorters_kwargs": sorters_kwargs,
            "test_with_toy_recording": test_with_toy_recording,
            "test_with_subrecording": test_with_subrecording,
            "test_subrecording_n_frames": test_subrecording_n_frames,
        }

        # task = asyncio.create_task(self.make_request(payload=payload))

        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(self.make_request(payload=payload))

        response = requests.post(self.endpoint, json=payload)
        if response.status_code == 200:
            self.logger.info("Success!")
        else:
            self.logger.info(f"Error {response.status_code}: {response.content}")