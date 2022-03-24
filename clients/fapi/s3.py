import aiohttp
import sys

from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from clients.fapi.uploader import MultipartUploader


class S3Client:
    def __init__(
        self, endpoint_url: str, aws_access_key_id: str, aws_secret_access_key: str
    ):
        self.session = get_session()
        self.endpoint_url = endpoint_url
        self.key_id = aws_access_key_id
        self.access_key = aws_secret_access_key

    async def get_file(self, bucket: str, key):
        async with self.session.create_client(
            "s3",
            region_name="",
            endpoint_url=self.endpoint_url,
            aws_secret_access_key=self.access_key,
            aws_access_key_id=self.key_id,
        ) as client:
            resp = await client.get_object(Bucket=bucket, Key=key)
            return await resp["Body"].read()

    async def bucket_list(self, bucket: str):
        async with self.session.create_client(
            "s3",
            region_name="",
            endpoint_url=self.endpoint_url,
            aws_secret_access_key=self.access_key,
            aws_access_key_id=self.key_id,
        ) as client:
            file_list = await client.list_objects(Bucket=bucket)
            return "\n".join(file["Key"] for file in file_list["Contents"])

    async def bucket_exists(self, bucket: str):
        async with self.session.create_client(
            "s3",
            region_name="",
            endpoint_url=self.endpoint_url,
            aws_secret_access_key=self.access_key,
            aws_access_key_id=self.key_id,
        ) as client:
            try:
                await client.head_bucket(Bucket=bucket)
            except ClientError as e:
                raise e

    async def upload_file(self, bucket: str, path: str, buffer):
        async with self.session.create_client(
            "s3",
            region_name="",
            endpoint_url=self.endpoint_url,
            aws_secret_access_key=self.access_key,
            aws_access_key_id=self.key_id,
        ) as client:
            await client.put_object(Bucket=bucket, Key=path, Body=buffer)

    async def fetch_and_upload(self, bucket: str, path: str, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                await self.upload_file(bucket, path, (await resp.read()))

    async def stream_upload(self, bucket: str, path: str, url: str):
        buf = b""
        size = b""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                async with self.session.create_client(
                    "s3",
                    region_name="us-west-2",
                    endpoint_url=self.endpoint_url,
                    aws_secret_access_key=self.access_key,
                    aws_access_key_id=self.key_id,
                ) as client:
                    async with MultipartUploader(
                        client=client, bucket=bucket, key=path
                    ) as uploader:
                        async for data in resp.content.iter_chunked(10 * 1024 * 1024):
                            buf += data
                            size += data
                            yield len(size)
                            if sys.getsizeof(buf) > 5 * 1024 * 1024:
                                await uploader.upload_part(buf)
                                buf = b""
                        await uploader.upload_part(buf)

    async def stream_file(self, bucket: str, path: str, file: str):
        async with self.session.create_client(
            "s3",
            region_name="us-west-2",
            endpoint_url=self.endpoint_url,
            aws_secret_access_key=self.access_key,
            aws_access_key_id=self.key_id,
        ) as client:
            async with MultipartUploader(
                client=client, bucket=bucket, key=path
            ) as uploader:
                with open(file, "rb") as fd:
                    buf = fd.read(10 * 1024 * 1024)
                    while buf:
                        await uploader.upload_part(buf)
                        buf = fd.read(10 * 1024 * 1024)
