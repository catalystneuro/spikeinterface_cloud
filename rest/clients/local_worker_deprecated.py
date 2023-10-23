import requests

from core.logger import logger
from models.sorting import SortingData


class LocalWorkerClient:

    def __init__(self, endpoint: str = "http://worker:5000/worker"):
        self.endpoint = endpoint
        self.logger = logger


    def run_sorting(self, **kwargs) -> None:
        payload = SortingData(**kwargs).dict()
        response = requests.post(self.endpoint + "/run", json=payload)
        if response.status_code == 200:
            self.logger.info("Success!")
        else:
            self.logger.info(f"Error {response.status_code}: {response.content}")
    

    def get_run_logs(self, run_identifier):
        self.logger.info("Getting logs...")
        response = requests.get(self.endpoint + "/logs", params={"run_identifier": run_identifier})
        if response.status_code == 200:
            logs = response.content.decode('utf-8')
            if "Error running sorter" in logs:
                return "fail", logs
            elif "Sorting job completed successfully!" in logs:
                return "success", logs
            return "running", logs
        else:
            self.logger.info(f"Error {response.status_code}: {response.content}")
            return "fail", f"Logs couldn't be retrieved. Error {response.status_code}: {response.content}"