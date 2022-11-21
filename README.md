# Build and deploy the Docker images

Build docker image:
```bash
$ DOCKER_BUILDKIT=1 docker build -t <image-name:version> -f <Dockerfile_name> .
```

Run locally:
```bash
# With mounted volume
$ docker run \
    -v <host_path>:/results \
    --gpus all \
    --env AWS_S3_BUCKET=${AWS_S3_BUCKET} \
    --env AWS_S3_BUCKET_FOLDER=${AWS_S3_BUCKET_FOLDER}  \
    --env AWS_REGION_NAME=${AWS_REGION_NAME}  \
    --env AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}  \
    --env AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}  \
    <image-name:version>

# Run with access to a bash terminal inside the running container
$ docker run -it --gpus all --entrypoint /bin/bash <image-name:version>
```

Push image to ECR:
```bash
# Login to ECR - one of the two options should work
$ aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin <aws_id>.dkr.ecr.us-east-2.amazonaws.com
$ docker login -u AWS -p $(aws ecr get-login-password --region us-east-2) <aws_id>.dkr.ecr.the-region-you-are-in.amazonaws.com

# Tag image to comply with ECR
$ docker tag <image-name:version> <aws_id>.dkr.ecr.us-east-2.amazonaws.com/<image-name:version>

# Push image
$ docker push <aws_id>.dkr.ecr.us-east-2.amazonaws.com/<image-name:version>
```

# AWS Batch configuration

1. Create a Compute environment (EC2)
    - Use the standard IAMs: Service Role = AWSServiceRoleForBatch ([ref](https://docs.aws.amazon.com/batch/latest/userguide/service_IAM_role.html)) and Instance Role = ecsInstanceRole ([ref](https://docs.aws.amazon.com/batch/latest/userguide/instance_IAM_role.html))
    - Configure the instances available to be used by the environment. Instances with access to GPU instances (e.g. g3s.xlarge) might require you to request AWS to increase the quota limit for such machines, which by default is 0.
    - If you choose Spot instances, choose a value between 30~50% for the `Maximum % on-demand price`
2. Create a Job Queue (EC2) associated with the compute environment
3. Create a Job Definition (EC2)
    - choose suitable Execution Timeout, Job Attempts and Retry Strategies, if suitable
    - Select the base image
    - Command = `python run_script.py`
    - For the Job role configuration, choose an IAM role with permissions to read and write to S3 buckets and with Trusted entities configured like this:
    ```
    {
    "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ecs-tasks.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    ```
    - Configure the hardware specs
    - Add any fixed ENV variables that should be used by any Jobs using this definition


# Submiting jobs

The job submission must include the function arguments, which are passed and ENV vars to the running container.


# Useful refs:
- https://medium.com/@michael.smith.qs2/how-to-use-gpus-quickly-and-cheaply-with-aws-batch-and-pytorch-1209320c4e6b
- https://github.com/michael-smith-qs2/aws_gpu_batch_setup_2021
- https://github.com/NVIDIA/nvidia-container-runtime#environment-variables-oci-spec
