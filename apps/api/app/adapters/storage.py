"""S3-compatible storage (R2 in prod, MinIO locally)."""

from __future__ import annotations

import uuid

import boto3
from botocore.client import Config

from app.config import get_settings


class StorageClient:
    def __init__(self) -> None:
        s = get_settings()
        self.bucket = s.s3_bucket
        kwargs: dict = {
            "aws_access_key_id": s.s3_access_key,
            "aws_secret_access_key": s.s3_secret_key,
            "region_name": s.s3_region,
            "config": Config(signature_version="s3v4"),
        }
        if s.s3_endpoint_url:
            kwargs["endpoint_url"] = s.s3_endpoint_url
        self.client = boto3.client("s3", **kwargs)

    def presign_put(self, key: str, content_type: str, expires: int = 900) -> str:
        return self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires,
        )

    def presign_get(self, key: str, expires: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires,
        )

    def put_object(self, key: str, body: bytes, content_type: str = "application/octet-stream") -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=body, ContentType=content_type)

    def get_object(self, key: str) -> bytes:
        resp = self.client.get_object(Bucket=self.bucket, Key=key)
        return resp["Body"].read()

    @staticmethod
    def new_key(prefix: str, ext: str) -> str:
        return f"{prefix.rstrip('/')}/{uuid.uuid4().hex}.{ext.lstrip('.')}"


_singleton: StorageClient | None = None


def get_storage() -> StorageClient:
    global _singleton
    if _singleton is None:
        _singleton = StorageClient()
    return _singleton
