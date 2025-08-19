import os

from src.data.env import ENV


os.makedirs("/config", exist_ok=True)
data_file_path = "/config/data.db"
config_file_path = "/config/config.yaml"
