import os


class Settings:
    DANDI_VAR = os.environ.get("DANDI_VAR")

class DevSettings(Settings):
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 8050

class ProdSettings(Settings):
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 8050

def get_settings():
    settings_map = {
        "dev": DevSettings,
        "prod": ProdSettings
    }
    stage = os.environ.get('REST_API_MODE', 'dev')
    return settings_map[stage]()

settings: Settings = get_settings()
