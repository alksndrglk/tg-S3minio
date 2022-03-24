import asyncio
import aiohttp
from dataclasses import dataclass
from typing import List, Dict
from contextlib import suppress
import io

from clients.fapi.s3 import S3Client
from clients.tg.dcs import UpdateObj
from clients.fapi.tg import TgClientWithFile
from bot.utils import log_exceptions


@dataclass
class WorkerConfig:
    endpoint_url: str
    aws_secret_access_key: str
    aws_access_key_id: str
    bucket: str
    concurrent_workers: int = 1


@dataclass
class Renamer:
    id: str
    chat_id: int
    name: str
    size: int
    url: str
    question: bool = False
    ans: bool = False


class Worker:
    def __init__(self, token: str, queue: asyncio.Queue, config: WorkerConfig):
        self._tasks: List[asyncio.Task] = []
        self.s3 = S3Client(
            endpoint_url=config.endpoint_url,
            aws_secret_access_key=config.aws_secret_access_key,
            aws_access_key_id=config.aws_access_key_id,
        )
        self.workers = config.concurrent_workers
        self.bucket = config.bucket
        self.tg_cli = TgClientWithFile(token)
        self._queue = queue
        self._users = []
        self.is_running = False
        self.download_url = "https://api.telegram.org/file/bot{}/{}"
        self.rename: Dict[Renamer] = {}

    async def handle_update(self, upd: UpdateObj):
        response = ""
        name = ""
        chat_id = upd.message.from_.id
        if chat_id not in self._users:
            await self.tg_cli.send_message(chat_id, "[greeting]")
            self._users.append(chat_id)
        else:
            if upd.message.document:
                await self.tg_cli.send_message(
                    chat_id, "[document] \nDo you want to rename the file? [y/n]"
                )
                file = await self.tg_cli.get_file(upd.message.document.file_id)
                url = self.download_url.format(self.tg_cli.token, file.file_path)
                self.rename[chat_id] = Renamer(
                    upd.message.document.file_id,
                    chat_id,
                    upd.message.document.file_name,
                    upd.message.document.file_size,
                    url,
                    True,
                )
            else:
                if upd.message.text:
                    if upd.message.text == "/list":
                        response = await self.s3.bucket_list(self.bucket)
                    elif upd.message.text.lower() == "y" and chat_id in self.rename:
                        if self.rename[chat_id].question:
                            self.rename[chat_id].ans = True
                            response = "Enter new file name"
                    elif chat_id in self.rename:
                        if self.rename[chat_id].ans:
                            self.rename[chat_id].name = upd.message.text
                        await self.loader(self.rename[chat_id])
                        del self.rename[chat_id]
                    else:
                        response = "[document is required]"
                    if response:
                        await self.tg_cli.send_message(chat_id, response)

    async def loader(self, file: Renamer):
        def convert_bytes(size):
            for x in ["bytes", "KB", "MB", "GB", "TB"]:
                if size < 1024.0:
                    return "%3.1f %s" % (size, x)
                size /= 1024.0
            return size

        msg = await self.tg_cli.send_message(file.chat_id, "loading ...")
        async for progres in self.s3.stream_upload(self.bucket, file.name, file.url):
            await self.tg_cli.edit_message(
                file.chat_id,
                msg.message_id,
                f"{convert_bytes(progres)} / {convert_bytes(file.size)}",
            )
        if file.ans:
            response = await self.s3.get_file(self.bucket, file.name)
            data = aiohttp.FormData()
            document = io.BytesIO(response)
            data.add_field("chat_id", str(file.chat_id))
            data.add_field("document", document, filename=file.name)
            await self.tg_cli.session.post(
                self.tg_cli.get_path("sendDocument"), data=data
            )
            document.close()
        await self.tg_cli.edit_message(
            file.chat_id, msg.message_id, "[document has been saved]"
        )

    async def _worker(self):
        while self.is_running:
            obj: UpdateObj = await self._queue.get()
            await self.handle_update(obj)
            self._queue.task_done()

    def start(self):
        self.is_running = True
        for _ in range(self.workers):
            self._tasks.append(asyncio.create_task(self._worker()))

    async def stop(self):
        self.is_running = False
        await self._queue.join()
        for task in self._tasks:
            if task:
                task.cancel()
        await self.tg_cli.session.close()
