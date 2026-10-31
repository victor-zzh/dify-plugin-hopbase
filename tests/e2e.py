"""Live end-to-end check of the HopBase plugin classes (not shipped in the package).

Run from the repo root:

    HOPBASE_API_KEY=... python tests/e2e.py [model-id ...]

With no model IDs it tests every predefined model the key can reach (per
GET /v1/models). Spends a few thousand tokens per model.
"""

import os
import sys
from pathlib import Path

import dify_plugin  # noqa: F401  (import first: it patches the network stack)
import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dify_plugin.entities.model import AIModelEntity  # noqa: E402
from dify_plugin.entities.model.message import (  # noqa: E402
    AssistantPromptMessage,
    PromptMessageTool,
    SystemPromptMessage,
    ToolPromptMessage,
    UserPromptMessage,
)
from dify_plugin.errors.model import CredentialsValidateFailedError  # noqa: E402

from models._common import normalize_endpoint_url  # noqa: E402
from models.llm.llm import HopbaseLargeLanguageModel  # noqa: E402
from provider.hopbase import HopbaseModelProvider  # noqa: E402

WEATHER = PromptMessageTool(
    name="get_weather",
    description="Get the current weather for a city",
    parameters={
        "type": "object",
        "properties": {"city": {"type": "string", "description": "City name"}},
        "required": ["city"],
    },
)


def load_schemas() -> list[AIModelEntity]:
    schemas = []
    for path in sorted((ROOT / "models" / "llm").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        data = yaml.safe_load(path.read_text())
        data.setdefault("fetch_from", "predefined-model")
        schemas.append(AIModelEntity.model_validate(data))
    return schemas


def key_models(creds: dict) -> set[str]:
    url = normalize_endpoint_url(creds) + "/models"
    r = requests.get(url, headers={"Authorization": f"Bearer {creds['api_key']}"}, timeout=30)
    r.raise_for_status()
    return {m["id"] for m in r.json()["data"]}


def check_provider(creds: dict) -> None:
    provider = HopbaseModelProvider.__new__(HopbaseModelProvider)
    provider.validate_provider_credentials(dict(creds))
    print("provider validate (good key): ok")
    for bad in ({"api_key": "sk-invalid-key-for-test"}, {"api_key": creds["api_key"], "endpoint_url": "https://hop-base.com/"}):
        try:
            provider.validate_provider_credentials(bad)
        except CredentialsValidateFailedError as ex:
            print(f"provider validate (bad {'key' if 'endpoint_url' not in bad else 'base URL'}): rejected: {ex}")
        else:
            raise SystemExit("provider validate accepted bad credentials")


def collect(chunks):
    """The SDK yields chunks for blocking calls too; join them."""
    text, calls, usage = "", [], None
    for chunk in chunks:
        content = chunk.delta.message.content
        text += content if isinstance(content, str) else ""
        calls.extend(chunk.delta.message.tool_calls or [])
        usage = chunk.delta.usage or usage
    return text, calls, usage


def tool_round_trip(llm, model: str, creds: dict, stream: bool) -> str:
    msgs = [
        SystemPromptMessage(content="You can call tools. Use get_weather for weather questions."),
        UserPromptMessage(content="What is the weather in Paris right now? Use the tool."),
    ]
    params = {"max_tokens": 2048}
    text, calls, _ = collect(llm.invoke(model, dict(creds), msgs, params, tools=[WEATHER], stream=stream))
    assert calls, f"{model}: no tool call (stream={stream}); text={text!r:.200}"
    call = calls[0]
    assert call.function.name == "get_weather", call
    assert "paris" in call.function.arguments.lower(), call.function.arguments
    # Second turn: feed the tool result back and expect a text answer.
    msgs += [
        AssistantPromptMessage(content="", tool_calls=[call]),
        ToolPromptMessage(content='{"city":"Paris","condition":"sunny","temp_c":21}', tool_call_id=call.id, name="get_weather"),
    ]
    answer, _, _ = collect(llm.invoke(model, dict(creds), msgs, params, tools=[WEATHER], stream=stream))
    assert "21" in answer or "sunny" in answer.lower(), f"{model}: tool result not used: {answer!r:.200}"
    return f"{call.function.name}({call.function.arguments}) -> {answer.strip()[:60]!r}"


def main() -> None:
    creds = {"api_key": os.environ["HOPBASE_API_KEY"]}
    if os.environ.get("HOPBASE_BASE_URL"):
        creds["endpoint_url"] = os.environ["HOPBASE_BASE_URL"]
    llm = HopbaseLargeLanguageModel(model_schemas=load_schemas())
    check_provider(creds)

    reachable = key_models(creds)
    wanted = sys.argv[1:] or [s.model for s in llm.predefined_models() if s.model in reachable]
    failures = 0
    for model in wanted:
        try:
            llm.validate_credentials(model, dict(creds))
            print(f"[{model}] model validate: ok")

            text, _, usage = collect(llm.invoke(model, dict(creds), [UserPromptMessage(content="Reply with the single word: pong")], {"max_tokens": 1024}, stream=False))
            assert "pong" in text.lower(), text
            print(f"[{model}] blocking: {text.strip()[-40:]!r} usage={usage.prompt_tokens}/{usage.completion_tokens}")

            text, _, usage = collect(llm.invoke(model, dict(creds), [UserPromptMessage(content="Count from 1 to 5, separated by spaces.")], {"max_tokens": 1024}, stream=True))
            assert "1 2 3 4 5" in text or "1, 2, 3, 4, 5" in text, text
            print(f"[{model}] stream: {text.strip()[-30:]!r} usage={usage.prompt_tokens if usage else None}/{usage.completion_tokens if usage else None}")

            print(f"[{model}] tool (blocking): {tool_round_trip(llm, model, creds, stream=False)}")
            print(f"[{model}] tool (stream): {tool_round_trip(llm, model, creds, stream=True)}")
        except Exception as ex:  # noqa: BLE001
            failures += 1
            print(f"[{model}] FAILED: {type(ex).__name__}: {str(ex)[:400]}")
    custom = os.environ.get("HOPBASE_CUSTOM_MODEL")
    if custom:
        ccreds = {**creds, "context_size": "128000", "max_tokens_to_sample": "8192", "function_calling_type": "tool_call"}
        schema = llm.get_customizable_model_schema(custom, dict(ccreds))
        llm.validate_credentials(custom, dict(ccreds))
        text, _, _ = collect(llm.invoke(custom, dict(ccreds), [UserPromptMessage(content="Reply with the single word: pong")], {"max_tokens": 512}, stream=True))
        assert "pong" in text.lower(), text
        print(f"[custom {custom}] features={[f.value for f in schema.features]} validate ok, stream: {text.strip()[-30:]!r}")
        print(f"[custom {custom}] tool (stream): {tool_round_trip(llm, custom, ccreds, stream=True)}")
        try:
            llm.validate_credentials("no-such-model-xyz", dict(ccreds))
        except CredentialsValidateFailedError as ex:
            print(f"[custom no-such-model-xyz] validate rejected: {str(ex)[:120]}")
        else:
            failures += 1
            print("[custom no-such-model-xyz] validate wrongly accepted")
    if failures:
        raise SystemExit(f"{failures} model(s) failed")
    print("all ok")


if __name__ == "__main__":
    main()
