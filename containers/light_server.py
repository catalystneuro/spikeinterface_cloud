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


@app.route('/worker/run', methods=['POST'])
async def run():
    data = request.get_json()
    kwargs = dict(
        run_identifier=data.get('run_identifier'),
        source=data.get('source'),
        source_data_type=data.get('source_data_type'),
        source_data_paths=data.get('source_data_paths'),
        recording_kwargs=data.get('recording_kwargs'),
        output_destination=data.get('output_destination'),
        output_path=data.get('output_path'),
        sorters_names_list=data.get('sorters_names_list'),
        sorters_kwargs=data.get('sorters_kwargs'),
        test_with_toy_recording=data.get('test_with_toy_recording'),
        test_with_subrecording=data.get('test_with_subrecording'),
        test_subrecording_n_frames=data.get('test_subrecording_n_frames'),
        log_to_file=data.get('log_to_file'),
    )
    loop = asyncio.get_event_loop()
    task = loop.create_task(run_async(**kwargs))
    return "success"


@app.route('/worker/logs', methods=['GET'])
def get_logs():
    run_identifier = request.args.get('run_identifier')
    log_filename = f"/logs/sorting_worker_{run_identifier}.log"
    with open(log_filename, 'r') as f:
        logs = str(f.read())
    return logs


@app.route('/worker/ping')
def ping():
    return 'Pong!'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)