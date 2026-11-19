from bson import ObjectId
from gridfs import AsyncGridFSBucket
from gridfs.errors import NoFile
from pymongo.asynchronous.database import AsyncDatabase


class PhotoStore:
    """Processed JPEG photos in a GridFS bucket."""

    def __init__(self, db: AsyncDatabase, bucket_name: str) -> None:
        self.bucket = AsyncGridFSBucket(db, bucket_name=bucket_name)

    async def save(self, filename: str, data: bytes) -> ObjectId:
        return await self.bucket.upload_from_stream(
            filename, data, metadata={"content_type": "image/jpeg"}
        )

    async def read(self, file_id: ObjectId) -> bytes | None:
        try:
            stream = await self.bucket.open_download_stream(file_id)
        except NoFile:
            return None
        return await stream.read()

    async def delete(self, file_id: ObjectId) -> None:
        try:
            await self.bucket.delete(file_id)
        except NoFile:
            pass
