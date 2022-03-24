import asyncio
from dataclasses import dataclass

from bot.poller import Poller
from bot.worker import Worker, WorkerConfig
from botocore.exceptions import ClientError

from clients.tg.api import TgClientError


@dataclass
class BotConfig:
    token: str
    worker: WorkerConfig


class Bot:
    def __init__(self, config: BotConfig):
        queue = asyncio.Queue()
        self.poller = Poller(config.token, queue)
        self.worker = Worker(config.token, queue, config.worker)
        self.validation = False

    async def start(self):
        try:
            await self.poller.tg_cli.get_me()
            await self.worker.s3.bucket_exists(self.worker.bucket)
            self.poller.start()
            self.worker.start()
        except (TgClientError, ClientError) as e:
            print("Validation Error: ", e)

    async def stop(self):
        await self.poller.stop()
        await self.worker.stop()
