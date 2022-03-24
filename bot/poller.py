import asyncio
from typing import Optional
from contextlib import suppress

from clients.tg.api import TgClient
from bot.utils import log_exceptions


class Poller:
    def __init__(self, token: str, queue: asyncio.Queue):
        self._task: Optional[asyncio.Task] = None
        self.tg_cli = TgClient(token)
        self._queue = queue
        self.is_runnig = False

    async def _worker(self):
        offset = 0
        while self.is_runnig:
            upd = await self.tg_cli.get_updates_in_objects(offset=offset, timeout=60)
            if upd:
                for obj in upd:
                    self._queue.put_nowait(obj)
                    offset = obj.update_id + 1

    def start(self):
        self.is_runnig = True
        self._task = asyncio.create_task(self._worker())

    async def stop(self):
        self.is_runnig = False
        if self._task:
            self._task.cancel()
        await self.tg_cli.session.close()
