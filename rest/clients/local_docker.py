from pathlib import Path
import docker

from ..core.logger import logger
from ..models.sorting import (
    RunKwargs,
    SourceDataKwargs,
    RecordingKwargs,
    PreprocessingKwargs,
    SorterKwargs,
    PostprocessingKwargs,
    CurationKwargs,
    VisualizationKwargs,
    OutputDataKwargs
)


map_sorter_to_image = {
    "kilosort2": "ghcr.io/catalystneuro/si-sorting-ks2:latest",
    "kilosort25": "ghcr.io/catalystneuro/si-sorting-ks25:latest",
    "kilosort3": "ghcr.io/catalystneuro/si-sorting-ks3:latest",
    "ironclust": "ghcr.io/catalystneuro/si-sorting-ironclust:latest",
    "spykingcircus": "ghcr.io/catalystneuro/si-sorting-spyking-circus:latest",
}


class LocalDockerClient:

    def __init__(self, base_url: str = "tcp://docker-proxy:2375"):
        self.logger = logger
        self.client = docker.DockerClient(base_url=base_url)

    def run_sorting(
        self, 
        run_kwargs: RunKwargs,
        source_data_kwargs: SourceDataKwargs,
        recording_kwargs: RecordingKwargs,
        preprocessing_kwargs: PreprocessingKwargs,
        sorter_kwargs: SorterKwargs,
        postprocessing_kwargs: PostprocessingKwargs,
        curation_kwargs: CurationKwargs,
        visualization_kwargs: VisualizationKwargs,
        output_data_kwargs: OutputDataKwargs,
    ) -> None:
        # Pass kwargs as environment variables to the container
        env_vars = dict(
            SI_RUN_KWARGS=run_kwargs.json(),
            SI_SOURCE_DATA_KWARGS=source_data_kwargs.json(),
            SI_RECORDING_KWARGS=recording_kwargs.json(),
            SI_PREPROCESSING_KWARGS=preprocessing_kwargs.json(),
            SI_SORTER_KWARGS=sorter_kwargs.json(),
            SI_POSTPROCESSING_KWARGS=postprocessing_kwargs.json(),
            SI_CURATION_KWARGS=curation_kwargs.json(),
            SI_VISUALIZATION_KWARGS=visualization_kwargs.json(),
            SI_OUTPUT_DATA_KWARGS=output_data_kwargs.json(),
        )
        
        # Local volumes to mount
        local_directory = Path(".").absolute()
        logs_directory = local_directory / "logs"
        results_directory = local_directory / "results"
        volumes = {
            logs_directory: {'bind': '/logs', 'mode': 'rw'},
            results_directory: {'bind': '/results', 'mode': 'rw'},
        }

        container = self.client.containers.run(
            name=f'si-sorting-run-{run_kwargs.run_identifier}',
            image=map_sorter_to_image[sorter_kwargs.sorter_name],
            command=['python', 'main.py'],
            detach=True,
            environment=env_vars,
            volumes=volumes,
            device_requests=[
                docker.types.DeviceRequest(
                    device_ids=["0"], 
                    capabilities=[['gpu']]
                )
            ]
        )    

    def get_run_logs(self, run_identifier):
        # TODO: Implement this
        self.logger.info("Getting logs...")
        # response = requests.get(self.url + "/logs", params={"run_identifier": run_identifier})
        # if response.status_code == 200:
        #     logs = response.content.decode('utf-8')
        #     if "Error running sorter" in logs:
        #         return "fail", logs
        #     elif "Sorting job completed successfully!" in logs:
        #         return "success", logs
        #     return "running", logs
        # else:
        #     self.logger.info(f"Error {response.status_code}: {response.content}")
        #     return "fail", f"Logs couldn't be retrieved. Error {response.status_code}: {response.content}"