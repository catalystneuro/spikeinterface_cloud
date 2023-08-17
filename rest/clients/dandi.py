import concurrent.futures
from dandi.dandiapi import DandiAPIClient
from dandischema.models import Dandiset
from pynwb import NWBHDF5IO, NWBFile
import fsspec
import pynwb
import h5py
import json
import requests
from fsspec.implementations.cached import CachingFileSystem
from typing import List


class DandiClient:

    def __init__(self, token: str = None):
        """
        Initialize DandiClient object, to interact with DANDI API.
        """
        self.fs = CachingFileSystem(
            fs=fsspec.filesystem("http"),
            cache_storage="data/nwb-cache",  # Local folder for the cache
        )
        self.token = token


    def get_all_dandisets_labels(self) -> List[str]:
        """
        List all dandisets labels.

        Returns:
            List[str]: List of dandisets labels. Each label is a string in the format: "dandiset_id - dandiset_name"
        """
        all_metadata = self.get_all_dandisets_metadata_from_file()
        return [
            k + " - " + v["name"] 
            for k, v in all_metadata.items()
        ]
    

    def save_dandisets_metadata_to_json(self) -> None:
        """
        Save metadata for all dandisets to a local file.
        """
        all_metadata = self.get_all_dandisets_metadata_from_dandi()
        with open("data/dandisets_metadata.json", "w", encoding="utf-8") as f:
            json.dump(all_metadata, f, ensure_ascii=False, indent=4)


    def get_all_dandisets_metadata_from_file(self) -> List:
        """
        Get metadata for all dandisets, from a local file.

        Returns:
            List: List of dandisets metadata.
        """
        with open("data/dandisets_metadata.json", "r") as f:
            all_metadata = json.load(f)
        return all_metadata

    
    def get_all_dandisets_metadata_from_dandi(self) -> List:
        """
        Get metadata for all dandisets, directly from DANDI.

        Returns:
            List: List of dandisets metadata.
        """
        with DandiAPIClient(token=self.token) as client:
            all_metadata = dict()
            dandisets_list = list(client.get_dandisets())
            total_dandisets = len(dandisets_list)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(self.process_dandiset, dandiset) for dandiset in dandisets_list]
                for future in concurrent.futures.as_completed(futures):
                    metadata = future.result()
                    if metadata:
                        all_metadata[metadata["id"].split(":")[-1].split("/")[0].strip()] = metadata
                    print(f"Processed {len(all_metadata)} of {total_dandisets} dandisets.")
        return all_metadata
    

    def process_dandiset(self, dandiset):
        try:
            metadata = dandiset.get_raw_metadata()
            if self.has_nwb(metadata) and self.has_ecephys(metadata):
                return metadata
        except:
            pass
        return None
    

    def get_dandiset_metadata(self, dandiset_id: str) -> dict:
        """
        Get metadata for a dandiset.

        Args:
            dandiset_id (str): Numerical ID of the dandiset. E.g. 000001

        Returns:
            dict: Metadata for the dandiset.
        """
        with DandiAPIClient(token=self.token) as client:
            dandiset = client.get_dandiset(dandiset_id=dandiset_id, version_id="draft")
            return dandiset.get_raw_metadata()


    def list_dandiset_files(self, dandiset_id: str) -> List[str]:
        """
        List all files in a dandiset.

        Args:
            dandiset_id (str): Numerical ID of the dandiset. E.g. 000001

        Returns:
            List[str]: List of files in the dandiset.
        """
        with DandiAPIClient(token=self.token) as client:
            dandiset = client.get_dandiset(dandiset_id=dandiset_id, version_id="draft")
            return [i.dict().get("path") for i in dandiset.get_assets() if i.dict().get("path").endswith(".nwb")]
        

    def get_nwbfile_info_fsspec(self, dandiset_id: str, file_path: str) -> dict:
        """
        Uses fsspec to read the file from S3.

        Args:
            dandiset_id (str): Numerical ID of the dandiset. E.g. 000001
            file_path (str): File path within Dandiset. E.g. sub-000001/sub-000001.nwb

        Returns:
            dict: Information extracted from the NWBFile object.
        """
        file_s3_url = self.get_file_url(dandiset_id, file_path)
        if "dandiarchive-embargo" in file_s3_url:
            file_s3_url = self.get_file_url_embargo(dandiset_id, file_path)
        with self.fs.open(file_s3_url, "rb") as f:
            with h5py.File(f) as file:
                with pynwb.NWBHDF5IO(file=file, load_namespaces=True) as io:
                    nwbfile = io.read()
                    file_info = self.extract_nwbfile_info(nwbfile=nwbfile)
                    file_info["url"] = file_s3_url
                    return file_info


    def get_nwbfile_info_ros3(self, dandiset_id: str, file_path: str) -> dict:
        """
        Uses ros3 to read the file from S3.

        Args:
            dandiset_id (str): Numerical ID of the dandiset. E.g. 000001
            file_path (str): File path within Dandiset. E.g. sub-000001/sub-000001.nwb

        Returns:
            dict: Information extracted from the NWBFile object.
        """
        file_s3_url = self.get_file_url(dandiset_id, file_path)
        with NWBHDF5IO(file_s3_url, mode='r', load_namespaces=True, driver='ros3') as io:
            nwbfile = io.read()
            return self.extract_nwbfile_info(nwbfile=nwbfile)


    def extract_nwbfile_info(self, nwbfile: NWBFile) -> dict:
        """
        Extracts information from an NWBFile object.

        Args:
            nwbfile (NWBFile): NWBFile object.

        Returns:
            dict: Information extracted from the NWBFile object.
        """
        file_info = dict()
        file_info["acquisition"] = dict()
        for k, v in nwbfile.acquisition.items():
            file_info["acquisition"][k] = {
                "name": k,
                "description": v.description,
                "rate": v.rate,
                "unit": v.unit,
                "duration": v.data.shape[0] / v.rate,
                "n_traces": v.data.shape[1],
            }
        file_info["subject"] = dict()
        for k, v in nwbfile.subject.fields.items():
            file_info["subject"][k] = v
        return file_info


    def get_file_url(self, dandiset_id: str, file_path: str) -> str:
        """
        Get the S3 URL of a file in a dandiset.

        Args:
            dandiset_id (str): Numerical ID of the dandiset. E.g. 000001
            file_path (str): File path within Dandiset. E.g. sub-000001/sub-000001.nwb

        Returns:
            str: S3 URL of the file.
        """
        with DandiAPIClient(token=self.token) as client:
            asset = client.get_dandiset(dandiset_id, "draft").get_asset_by_path(file_path)
            return asset.get_content_url(follow_redirects=1, strip_query=True)
    

    def get_file_url_embargo(self, dandiset_id: str, file_path: str) -> str:
        """
        Get the S3 URL of a file in a dandiset in embargo mode.

        Args:
            dandiset_id (str): Numerical ID of the dandiset. E.g. 000001
            file_path (str): File path within Dandiset. E.g. sub-000001/sub-000001.nwb

        Returns:
            str: S3 URL of the file.
        """
        with DandiAPIClient(token=self.token) as client:
            asset = client.get_dandiset(dandiset_id, "draft").get_asset_by_path(file_path)
            base_download_url = asset.base_download_url
            headers = {
                "Authorization": f'token {self.token}'
            }
            response = requests.get(base_download_url, headers=headers, stream=True)
            authorized_url = response.url
            return authorized_url
    

    def has_nwb(self, metadata: Dandiset) -> bool:
        """
        Tests if a dandiset has any NWB files.

        Args:
            metadata (Dandiset): Dandiset object

        Returns:
            bool: True if the dandiset has any NWB files.
        """
        assets_summary = metadata.get("assetsSummary", None)
        if assets_summary:
            data_standard = assets_summary.get("dataStandard", None)
            if data_standard:
                return any(x.get("identifier", "") == "RRID:SCR_015242" for x in data_standard)
        return False
        

    def has_ecephys(self, metadata: Dandiset) -> bool:
        """
        Test if a dandiset has any ecephys data.

        Args:
            metadata (Dandiset): Daniset object

        Returns:
            bool: True if the dandiset has any ecephys data.
        """
        assets_summary = metadata.get("assetsSummary", None)
        if assets_summary:
            variable_measured = assets_summary.get("variableMeasured", [])
            if variable_measured:
                return any(v == "ElectricalSeries" for v in variable_measured)
        return False