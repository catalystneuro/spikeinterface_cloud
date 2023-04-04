from flask import Flask, request, Response, stream_with_context
import asyncio
import logging
import functools

from run_script import main


app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_async(**kwargs):
    for k,v in kwargs.items():
        logger.info(f"{k}: {v}")
    main(**kwargs)
    # # Use stream_with_context to stream the response
    # async with stream_with_context(main(**kwargs)) as response:
    #     for line in response:
    #         # Yield each line of the response as it is generated
    #         logger.info(line)
    #         yield line

@app.route('/worker/run', methods=['POST'])
# def run():
async def run():
    # data = await request.get_json()
    data = request.get_json()
    kwargs = dict(
        run_identifier=data.get('run_identifier'),
        source_aws_s3_bucket=data.get('source_aws_s3_bucket'),
        source_aws_s3_bucket_folder=data.get('source_aws_s3_bucket_folder'),
        dandiset_s3_file_url=data.get('dandiset_s3_file_url'),
        dandiset_file_es_name=data.get('dandiset_file_es_name'),
        target_output_type=data.get('target_output_type'),
        target_aws_s3_bucket=data.get('target_aws_s3_bucket'),
        target_aws_s3_bucket_folder=data.get('target_aws_s3_bucket_folder'),
        data_type=data.get('data_type'),
        recording_kwargs=data.get('recording_kwargs'),
        sorters_names_list=data.get('sorters_names_list'),
        sorters_kwargs=data.get('sorters_kwargs'),
        test_with_toy_recording=data.get('test_with_toy_recording'),
        test_with_subrecording=data.get('test_with_subrecording'),
        test_subrecording_n_frames=data.get('test_subrecording_n_frames'),
    )
    # Use the Response object to return the async response
    # return Response(run_async(**kwargs), mimetype='text/plain')

    # task = asyncio.create_task(run_async(**kwargs))
    loop = asyncio.get_event_loop()
    task = loop.create_task(run_async(**kwargs))
    # Run the long function asynchronously
    # result = loop.run_in_executor(None, functools.partial(run_async, data=kwargs))
    # Stream the output to the client
    # return Response(stream_with_context(result), mimetype='text/plain')

    return "success"


@app.route('/worker/logs', methods=['GET'])
def get_logs():
    run_identifier = request.args.get('run_identifier')
    log_filename = f"/logs/sorting_worker_{run_identifier}.log"
    with open(log_filename, 'r') as f:
        logs = str(f.read())
    return logs


@app.route('/worker/hello')
def hello_world():
    return 'Hello, World!'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)