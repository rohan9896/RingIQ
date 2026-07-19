from urllib.parse import urlparse

import boto3

from apps.api.ringiq_api.config import AppSettings


def presigned_recording_url(
    storage_uri: str | None,
    fallback_url: str | None,
    settings: AppSettings,
) -> str | None:
    if not storage_uri or not storage_uri.startswith("s3://"):
        return fallback_url
    parsed = urlparse(storage_uri)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    if not bucket or not key or bucket != settings.recording_s3_bucket:
        return fallback_url
    if not all(
        (
            settings.recording_s3_region,
            settings.recording_s3_access_key,
            settings.recording_s3_secret,
        )
    ):
        return fallback_url

    client = boto3.client(
        "s3",
        region_name=settings.recording_s3_region,
        aws_access_key_id=settings.recording_s3_access_key,
        aws_secret_access_key=settings.recording_s3_secret,
        endpoint_url=settings.recording_s3_endpoint or None,
    )
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=settings.recording_url_expiry_seconds,
    )
