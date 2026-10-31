DEFAULT_ENDPOINT = "https://api.hop-base.com/v1"
REQUEST_TIMEOUT = (10, 30)


def normalize_endpoint_url(credentials: dict) -> str:
    """Return the configured base URL, falling back to the public HopBase API."""
    url = (credentials.get("endpoint_url") or "").strip() or DEFAULT_ENDPOINT
    return url.rstrip("/")
