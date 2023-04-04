import boto3
import json
import enum


class JobStatus(enum.Enum):
    SUBMITTED = 'SUBMITTED'
    PENDING = 'PENDING'
    RUNNABLE = 'RUNNABLE'
    STARTING = 'STARTING'
    RUNNING = 'RUNNING'
    SUCCEEDED = 'SUCCEEDED'
    FAILED = 'FAILED'


class AWSBatch(object):
 
    def __init__(self, profile_name: str="default"):
        """
        References: 
        - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html
        - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs.html
        """
        self.session = boto3.Session(profile_name=profile_name)
        self.client_batch = self.session.client("batch")
        self.client_logs = self.session.client("logs")


    def list_job_queues(self):
        return self.client_batch.describe_job_queues()['jobQueues']


    def list_job_definitions(self):
        return self.client_batch.describe_job_definitions(status='ACTIVE')['jobDefinitions']
    

    def list_jobs(self, job_queue: str, job_status: JobStatus):
        return self.client_batch.list_jobs(jobQueue=job_queue, jobStatus=job_status)['jobSummaryList']


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
            kwargs['containerOverrides'] = dict()
            kwargs['containerOverrides']['environment'] = [{'name': k, 'value': str(v).replace("'", "\"")} for k, v in job_kwargs.items()]

        response = self.client_batch.submit_job(**kwargs)
        return response
    

    def describe_job(self, job_id: str):
        return self.client_batch.describe_jobs(jobs=[job_id])["jobs"][0]

    
    def get_job_logs(self, job_id: str):
        log_stream_name = self.describe_job(job_id=job_id)["container"].get("logStreamName", None)
        try:
            logs = self.client_logs.get_log_events(
                logGroupName="/aws/batch/job",
                logStreamName=log_stream_name,
            )["events"]
            return "\n".join([log["message"] for log in logs])
        except:
            return "Logs not available yet for this job."
    

    def get_job_logs_by_name(self, job_name: str, job_queue: str):
        response = self.client_batch.list_jobs(
            jobQueue=job_queue,
            filters=[{'name': 'JOB_NAME', 'values': [job_name]}]
        )
        job_id = response['jobSummaryList'][0]['jobId']
        return self.get_job_logs(job_id=job_id)
 
