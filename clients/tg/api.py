from typing import Optional, List
from json import JSONDecodeError

from clients.base import ClientError, Client
from clients.tg.dcs import UpdateObj, Message, GetUpdatesResponse, SendMessageResponse

from marshmallow import ValidationError


class TgClientError(ClientError):
    pass


class TgClient(Client):

    API_PATH = "https://api.telegram.org"

    def __init__(self, token: str = ""):
        self.token = token
        super().__init__()

    async def _handle_response(self, resp):
        if resp.status != 200:
            if resp.status == 401:
                raise TgClientError(resp)
            raise TgClientError(resp, await resp.text())
        try:
            return await resp.json()
        except JSONDecodeError:
            raise TgClientError(resp)

    def get_base_path(self):
        return f"{self.API_PATH}/bot{self.token}"

    def get_path(self, url):
        return f"{self.get_base_path()}/{url}"

    async def get_me(self) -> dict:
        return await self._perform_request("get", self.get_path("getMe"))

    async def get_updates(self, offset: Optional[int] = None, timeout: int = 0) -> dict:
        params = {}
        if offset:
            params["offset"] = offset
        if timeout:
            params["timeout"] = timeout
        return await self._perform_request(
            "get", self.get_path("getUpdates"), params=params
        )

    async def get_updates_in_objects(self, *args, **kwargs) -> List[UpdateObj]:
        res = await self.get_updates(*args, **kwargs)
        try:
            v_response: GetUpdatesResponse = GetUpdatesResponse.Schema().load(res)
        except ValidationError:
            raise TgClientError(res)
        return v_response.result

    async def send_message(self, chat_id: int, text: str) -> Message:
        params = {
            "chat_id": chat_id,
            "text": text,
        }
        msg = await self._perform_request(
            "post", self.get_path("sendMessage"), json=params
        )

        try:
            v_message: SendMessageResponse = SendMessageResponse.Schema().load(msg)
        except ValidationError:
            raise TgClientError(msg)
        return v_message.result

    async def edit_message(self, chat_id, message_id, text):
        params = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        }

        await self._perform_request(
            "post", self.get_path("editMessageText"), json=params
        )
