import os

from src.data.env import Env


env = Env()
os.makedirs(env.get_config_path(), exist_ok=True)
data_file_path = f"{env.get_config_path()}/data.db"
