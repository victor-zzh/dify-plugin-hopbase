import logging
from collections.abc import Mapping

import requests
from dify_plugin import ModelProvider
from dify_plugin.errors.model import CredentialsValidateFailedError

from models._common import REQUEST_TIMEOUT, normalize_endpoint_url

logger = logging.getLogger(__name__)


class HopbaseModelProvider(ModelProvider):
    def validate_provider_credentials(self, credentials: Mapping) -> None:
        """Check the API key against GET /models.

        A HopBase key only reaches the models of the groups it includes, so a
        chat request to a fixed model could fail for a valid key. Listing the
        key's models checks authentication without spending any quota.
        """
        api_key = (credentials.get("api_key") or "").strip()
        if not api_key:
            raise CredentialsValidateFailedError("API key is required.")
        url = normalize_endpoint_url(dict(credentials)) + "/models"
        try:
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as ex:
            raise CredentialsValidateFailedError(
                f"Could not reach the HopBase API at {url}: {type(ex).__name__}"
            ) from ex

        if response.status_code in (401, 403):
            raise CredentialsValidateFailedError(
                "The API key was rejected (HTTP %d). Check the key in the HopBase console."
                % response.status_code
            )
        if response.status_code != 200:
            raise CredentialsValidateFailedError(
                f"Unexpected response from {url}: HTTP {response.status_code}"
            )
        try:
            models = response.json().get("data")
        except ValueError:
            models = None
        if not isinstance(models, list):
            raise CredentialsValidateFailedError(
                f"{url} did not return a model list. Check the API Base URL."
            )
        if not models:
            raise CredentialsValidateFailedError(
                "The API key is valid but includes no models. Add a group to the key in the HopBase console."
            )
