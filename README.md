# SI cloud app

Set ENV variables:
```shell
export AWS_ACCESS_KEY_ID=XXXXXXXXXXXXXXXXXXX
export AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXX
export AWS_REGION_NAME=us-east-1
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
docker compose -f docker-compose-dev.yml
docker compose -f docker-compose-dev.yml --build
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