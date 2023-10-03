# SI cloud app

Easy submission of spike sorting jobs locally or to the Cloud:
![sorting](/media/sorting.gif)

Keep track of your sorting jobs:
![runs](/media/runs.gif)

# Running the app locally
Set ENV variables:
```shell
export AWS_DEFAULT_REGION=
export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=
export AWS_BATCH_JOB_QUEUE=
export AWS_BATCH_JOB_DEFINITION=
export DANDI_API_KEY=
```

Running with docker compose pulling images from github packages:
```shell
docker compose up
``` 

Running with docker compose building images locally (for dev, with hot reaload):
```shell
docker compose -f docker-compose-dev.yml up
```

If you did any changes in `requirements.txt`, `package.json` or `Dockerfile`, you should stop the containers and run again with an extra `--build` flag:
```shell
docker compose down
docker compose -f docker-compose-dev.yml up --build
``` 

Run rest api standalone (dev):
```shell
cd rest
python main.py
```

Run frontend standalone (dev):
```shell
cd frontend
yarn start
```

# App components

The app is composed of four components:
- `rest` - the rest api, which is a FastAPI app
- `frontend` - the frontend, which is a React app
- `db` - the database, which is a Postgres database
- `worker` - the worker, which is a sorter container with a Flask app

![app sketch](/media/app_sketch.jpg)


# Building images separately

```shell
DOCKER_BUILDKIT=1 docker build -t ghcr.io/catalystneuro/si-sorting-worker:latest -f Dockerfile.combined .
docker push ghcr.io/catalystneuro/si-sorting-worker:latest
```
