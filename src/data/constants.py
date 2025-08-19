import os

from src.data.env import ENV


os.makedirs(ENV.get_config_path(), exist_ok=True)
data_file_path = f"{ENV.get_config_path()}/data.db"
config_file_path = f"{ENV.get_config_path()}/config.yaml"
