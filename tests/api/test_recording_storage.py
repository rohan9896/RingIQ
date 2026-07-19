from apps.api.ringiq_api.config import AppSettings
from apps.api.ringiq_api.services import recording_storage


def recording_settings() -> AppSettings:
    return AppSettings(
        recording_s3_bucket="private-recordings",
        recording_s3_region="ap-south-1",
        recording_s3_access_key="access",
        recording_s3_secret="secret",
        recording_url_expiry_seconds=600,
    )


def test_presigned_recording_url_keeps_private_bucket_private(monkeypatch) -> None:
    observed: dict = {}

    class FakeS3Client:
        def generate_presigned_url(self, operation, *, Params, ExpiresIn):
            observed.update(
                {"operation": operation, "params": Params, "expires_in": ExpiresIn}
            )
            return "https://signed.example.com/call.mp3?signature=test"

    monkeypatch.setattr(recording_storage.boto3, "client", lambda *_, **__: FakeS3Client())

    result = recording_storage.presigned_recording_url(
        "s3://private-recordings/ringiq/recordings/call.mp3",
        "https://public.example.com/call.mp3",
        recording_settings(),
    )

    assert result == "https://signed.example.com/call.mp3?signature=test"
    assert observed == {
        "operation": "get_object",
        "params": {
            "Bucket": "private-recordings",
            "Key": "ringiq/recordings/call.mp3",
        },
        "expires_in": 600,
    }


def test_presigned_recording_url_rejects_unexpected_bucket() -> None:
    assert recording_storage.presigned_recording_url(
        "s3://someone-elses-bucket/call.mp3",
        "https://fallback.example.com/call.mp3",
        recording_settings(),
    ) == "https://fallback.example.com/call.mp3"
