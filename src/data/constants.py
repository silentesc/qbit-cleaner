import os


CONFIG_FOLDER_PATH = "/config"
DATA_FOLDER_PATH = "/data"

os.makedirs(CONFIG_FOLDER_PATH, exist_ok=True)
DATA_FILE_PATH = f"{CONFIG_FOLDER_PATH}/data.db"
CONFIG_FILE_PATH = f"{CONFIG_FOLDER_PATH}/config.yaml"
