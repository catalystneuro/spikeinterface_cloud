import boto3
import json


class AWSBatch(object):
 
    def __init__(self):
        """
        Reference: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html
        """
        self.client = boto3.client("batch")


    def list_job_queues(self):
        return self.client.describe_job_queues()['jobQueues']


    def list_job_definitions(self):
        return self.client.describe_job_definitions(status='ACTIVE')['jobDefinitions']


    def submit_job(
        self, 
        job_name: str, 
        job_queue: str,
        job_definition :str,
        job_kwargs: dict = None, 
        attempt_duration_seconds: int = 1800,
    ):  
        kwargs = dict(
            jobName=job_name,
            jobQueue=job_queue,
            jobDefinition=job_definition,
            timeout={'attemptDurationSeconds': attempt_duration_seconds},
        )

        if job_kwargs:
            kwargs['containerOverrides']['environment'] = [{k:str(v).replace("'", "\"")} for k, v in job_kwargs.items()]

        response = self.client.submit_job(**kwargs)
        return response
    

    def describe_job(self, job_id: str):
        return self.client.describe_jobs(jobs=[job_id])["jobs"][0]
 
