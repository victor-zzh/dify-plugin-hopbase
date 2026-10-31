from collections.abc import Generator
from typing import Optional, Union

from dify_plugin import OAICompatLargeLanguageModel
from dify_plugin.entities.model import AIModelEntity, ModelFeature
from dify_plugin.entities.model.llm import LLMResult
from dify_plugin.entities.model.message import PromptMessage, PromptMessageTool

from models._common import normalize_endpoint_url

TOOL_FEATURES = {
    ModelFeature.TOOL_CALL,
    ModelFeature.MULTI_TOOL_CALL,
    ModelFeature.STREAM_TOOL_CALL,
}


class HopbaseLargeLanguageModel(OAICompatLargeLanguageModel):
    """HopBase chat models over the OpenAI-compatible Chat Completions API."""

    def _invoke(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: Optional[list[PromptMessageTool]] = None,
        stop: Optional[list[str]] = None,
        stream: bool = True,
        user: Optional[str] = None,
    ) -> Union[LLMResult, Generator]:
        credentials = self._prepare_credentials(model, credentials)
        # The Dify end-user ID is not forwarded (user=None).
        result = super()._invoke(
            model, credentials, prompt_messages, model_parameters, tools, stop, stream, None
        )
        return result

    def validate_credentials(self, model: str, credentials: dict) -> None:
        credentials = self._prepare_credentials(model, credentials)
        # Reasoning models may spend a few tokens thinking before they answer.
        credentials["validate_credentials_max_tokens"] = 16
        super().validate_credentials(model, credentials)

    def get_num_tokens(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        tools: Optional[list[PromptMessageTool]] = None,
    ) -> int:
        count = super().get_num_tokens(
            model, self._prepare_credentials(model, credentials), prompt_messages, tools
        )
        return count

    def get_customizable_model_schema(
        self, model: str, credentials: dict
    ) -> Optional[AIModelEntity]:
        credentials = dict(credentials)
        credentials["mode"] = "chat"
        credentials.setdefault("function_calling_type", "tool_call")
        entity = super().get_customizable_model_schema(model, credentials)
        if credentials["function_calling_type"] == "tool_call":
            for feature in (ModelFeature.TOOL_CALL, ModelFeature.AGENT_THOUGHT):
                if feature not in entity.features:
                    entity.features.append(feature)
        return entity

    def _prepare_credentials(self, model: str, credentials: dict) -> dict:
        creds = dict(credentials)
        creds["endpoint_url"] = normalize_endpoint_url(creds)
        creds["mode"] = "chat"
        creds.pop("endpoint_model_name", None)
        creds.pop("extra_headers", None)
        if "function_calling_type" not in creds:
            schema = self._predefined_schema(model)
            if schema is None or TOOL_FEATURES.intersection(schema.features or []):
                creds["function_calling_type"] = "tool_call"
        return creds

    def _predefined_schema(self, model: str) -> Optional[AIModelEntity]:
        for schema in self.predefined_models():
            if schema.model == model:
                return schema
        return None
