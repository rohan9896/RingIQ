from apps.api.ringiq_api.config import Settings
from tests.api.postgres import get_test_database_url


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "database_url": get_test_database_url(),
        "clerk_secret_key": "sk_test_example",
        "clerk_jwt_key": "-----BEGIN PUBLIC KEY-----\\nexample\\n-----END PUBLIC KEY-----",
        "clerk_authorized_parties_raw": "http://localhost:3000",
        "livekit_url": "wss://example.livekit.cloud",
        "livekit_api_key": "api-key",
        "livekit_api_secret": "api-secret",
        "livekit_sip_outbound_trunk_id": "ST_example",
    }
    values.update(overrides)
    return Settings(**values)
