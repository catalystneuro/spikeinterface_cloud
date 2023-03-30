from flask import Flask, request
from run_script import main


app = Flask(__name__)

@app.route('/run')
def run():
    main(
        source_aws_s3_bucket=request.args.get('source_aws_s3_bucket'),
        source_aws_s3_bucket_folder=request.args.get('source_aws_s3_bucket_folder'),
        dandiset_s3_file_url=request.args.get('dandiset_s3_file_url'),
        target_aws_s3_bucket=request.args.get('target_aws_s3_bucket'),
        target_aws_s3_bucket_folder=request.args.get('target_aws_s3_bucket_folder'),
        data_type=request.args.get('data_type'),
        recording_kwargs=request.args.get('recording_kwargs'),
        sorters_names_list=request.args.get('sorters_names_list'),
        sorters_kwargs=request.args.get('sorters_kwargs'),
        test_with_toy_recording=request.args.get('test_with_toy_recording'),
        test_with_subrecording=request.args.get('test_with_subrecording'),
        test_subrecording_n_frames=request.args.get('test_subrecording_n_frames'),
    )
    return 'Command executed'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
