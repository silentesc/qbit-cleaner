import time
import typing
import requests
from enum import Enum

from loguru import logger

from src.data.constants import env


class DiscordWebhookType(Enum):
    INFO = 1
    ERROR = 2


class DiscordWebhookUtils:
    def __init__(self) -> None:
        self.webhook_url: str = env.get_discord_webhook_url()


    def __make_request(self, json: typing.Any) -> None:
        if not self.webhook_url:
            return

        while True:
            response = requests.post(self.webhook_url, json=json)
            if response.status_code == 204:
                logger.trace("Discord webhook sent successfully")
                return
            elif response.status_code == 429:
                data = response.json()
                retry_after = data.get("retry_after", 1000)
                logger.warning(f"Discord webhook rate limited. Retrying after {round(retry_after, 2)}s")
                time.sleep(retry_after)
                continue
            else:
                logger.error(f"Failed to send discord webhook: {response.status_code} - {response.text}")
                return


    def send_webhook_embed(self, webhook_type: DiscordWebhookType, title: str, description: str = "", content: str = "", fields: list[dict[str, str | bool]] = []) -> None:
        if not self.webhook_url:
            return

        embed: dict[str, typing.Any] = {
            "title": title,
            "description": description,
            "fields": fields,
        }

        match webhook_type:
            case DiscordWebhookType.INFO: embed["color"] = 0x69ff81
            case DiscordWebhookType.ERROR: embed["color"] = 0xff8080

        data = {
            "content": content,
            "embeds": [embed],
        }

        self.__make_request(json=data)


    def send_webhook_message(self, content: str = "") -> None:
        if not self.webhook_url:
            return

        data = {
            "content": content,
        }

        self.__make_request(json=data)
