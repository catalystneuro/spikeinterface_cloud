# SI cloud app

Set ENV variables:
```shell
export AWS_ACCESS_KEY_ID=XXXXXXXXXXXXXXXXXXX
export AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXX
export AWS_REGION_NAME=us-east-1
```

Running with docker compose (also works for dev, with hot reaload):
```shell
docker compose up
``` 

If you did any changes in `requirements.txt`, `package.json` or `Dockerfile`, you should stop the containers and run again with an extra `--build` flag:
```shell
docker compose down
docker compose up --build
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

