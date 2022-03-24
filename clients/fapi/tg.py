import aiohttp

from marshmallow import ValidationError

from clients.tg.api import TgClient, TgClientError
from clients.tg.dcs import File, Message, SendMessageResponse


class TgClientWithFile(TgClient):
    async def get_file(self, file_id: str) -> File:
        resp = await self._perform_request(
            "get", self.get_path("getFile"), params={"file_id": file_id}
        )
        try:
            v_file: File = File.Schema().load(resp["result"])
        except ValidationError:
            raise TgClientError(resp)
        return v_file

    async def download_file(self, file_path: str, destination_path: str):
        url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
        async with self.session.get(url) as resp:
            if resp.status != 200:
                raise TgClientError(resp, await resp.text())
            with open(destination_path, "wb") as fd:
                async for data in resp.content.iter_chunked(1024):
                    fd.write(data)

    async def send_document(self, chat_id: int, document_path) -> Message:
        data = aiohttp.FormData()
        data.add_field("chat_id", chat_id)
        data.add_field("document", open(document_path, "rb"))
        async with self.session.post(self.get_path("sendDocument"), data=data) as msg:
            resp = await self._handle_response(msg)
            try:
                v_message: SendMessageResponse = SendMessageResponse.Schema().load(resp)
            except ValidationError:
                raise TgClientError(resp)
            return v_message.result
