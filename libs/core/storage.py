import json
import io
from minio import Minio
from minio.error import S3Error
from libs.core.logger import configure_logger
from libs.core.config import BaseConfig

logger = configure_logger("storage_client")

class StorageClient:
    def __init__(self, config: BaseConfig):
        self.client = Minio(
            config.MINIO_ENDPOINT,
            access_key=config.MINIO_ACCESS_KEY,
            secret_key=config.MINIO_SECRET_KEY,
            secure=config.MINIO_SECURE
        )
        self.bucket_name = "raw-emails"
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"MinIO Error: {e}")

    def upload_json(self, object_name: str, data: dict) -> str:
        """
        Uploads a dictionary as a JSON file to MinIO.
        Returns the object path (bucket/object_name).
        """
        try:
            json_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
            data_stream = io.BytesIO(json_bytes)
            
            self.client.put_object(
                self.bucket_name,
                object_name,
                data_stream,
                length=len(json_bytes),
                content_type="application/json"
            )
            logger.info(f"Uploaded {object_name} to {self.bucket_name}")
            return f"{self.bucket_name}/{object_name}"
        except S3Error as e:
            logger.error(f"Failed to upload JSON to MinIO: {e}")
            raise e

    def upload_file(self, object_name: str, file_data: bytes, content_type: str = "application/octet-stream") -> str:
        """
        Uploads raw bytes to MinIO.
        """
        try:
            data_stream = io.BytesIO(file_data)
            self.client.put_object(
                self.bucket_name,
                object_name,
                data_stream,
                length=len(file_data),
                content_type=content_type
            )
            return f"{self.bucket_name}/{object_name}"
        except S3Error as e:
            logger.error(f"Failed to upload file to MinIO: {e}")
            raise e
