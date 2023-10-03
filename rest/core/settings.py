import os


class Settings:
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", None)
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", None)
    AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION", None)
    DANDI_API_KEY = os.environ.get("DANDI_API_KEY", None)
    DANDI_VAR = os.environ.get("DANDI_VAR")
    
    AWS_BATCH_JOB_QUEUE = os.environ.get("AWS_BATCH_JOB_QUEUE", None)
    AWS_BATCH_JOB_DEFINITION = os.environ.get("AWS_BATCH_JOB_DEFINITION", None)
    SORTING_LOGS_S3_BUCKET = os.environ.get("SORTING_LOGS_S3_BUCKET", None)

    WORKER_DEPLOY_MODE = os.environ.get("WORKER_DEPLOY_MODE", "compose")


class DevSettings(Settings):
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 8000
    DB_CONNECTION_STRING = 'postgresql+psycopg2://postgres:postgres@database/si-sorting-db'


class ProdSettings(Settings):
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 8050
    DB_CONNECTION_STRING = os.environ.get("DB_CONNECTION_STRING", None)


def get_settings():
    settings_map = {
        "compose": DevSettings,
        "dev": DevSettings,
        "prod": ProdSettings
    }
    stage = os.environ.get('REST_DEPLOY_MODE', 'dev')
    return settings_map[stage]()


settings: Settings = get_settings()
