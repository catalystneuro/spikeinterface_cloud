import os


class Settings:
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", None)
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", None)
    AWS_REGION = os.environ.get("AWS_REGION", None)
    DANDI_VAR = os.environ.get("DANDI_VAR")

    WORKER_DEPLOY_MODE = os.environ.get("WORKER_DEPLOY_MODE", "compose")
    db_connection_string = 'postgresql+psycopg2://postgres:postgres@database/si-sorting-db'

class DevSettings(Settings):
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 8000

class ProdSettings(Settings):
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 8050

def get_settings():
    settings_map = {
        "compose": DevSettings,
        "dev": DevSettings,
        "prod": ProdSettings
    }
    stage = os.environ.get('DEPLOY_MODE', 'dev')
    return settings_map[stage]()

settings: Settings = get_settings()
