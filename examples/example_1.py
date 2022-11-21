from spikeinterface_cloud import AWSBatch

# Instantiate client
batch = AWSBatch()

# Get existing job queues and job definitions
my_job_queues = batch.list_job_queues()
my_job_definitions = batch.list_job_definitions()

# Define job arguments
job_kwargs = {
    "SOURCE_AWS_S3_BUCKET": "my-bucket",
    "SOURCE_AWS_S3_BUCKET_FOLDER": "dataset-spikeglx",
    "TARGET_AWS_S3_BUCKET": "my-bucket",
    "TARGET_AWS_S3_BUCKET_FOLDER": "dataset-spikeglx/results",
    "DATA_TYPE": "spikeglx",
    "READ_RECORDING_KWARGS": {"stream_id": "imec.ap"},
    "SORTERS": ["kilosort2_5", "kilosort3"]
}

# Submit job
response_job = batch.submit_job(
    job_name="my-job-123", 
    job_queue=my_job_queues[0]["jobQueueName"],
    job_definition=my_job_definitions[0]["jobDefinitionName"],
    job_kwargs=job_kwargs, 
)

# Check job status every 60 seconds, until succeeded
out = False
while not out:
    r = batch.describe_job(job_id=response_job["jobId"])
    status = r["status"]
    print(f"Job status: {status}")
    if status == "SUCCEEDED":
        out = True