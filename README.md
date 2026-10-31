# HopBase for Dify

A model provider plugin for [HopBase](https://hop-base.com), an AI API gateway with an OpenAI-compatible API. One HopBase API key gives Dify access to chat models from DeepSeek, Doubao Seed, Gemini, GPT, Grok, Kimi, GLM and other families.

- Source repository: https://github.com/victor-zzh/dify-plugin-hopbase
- API base URL: `https://api.hop-base.com/v1` (OpenAI Chat Completions, Bearer authentication)
- Public model catalog: https://hop-base.com/models
- Integration docs: https://hop-base.com/en/docs
- Privacy: see [PRIVACY.md](PRIVACY.md) and https://api.hop-base.com/legal/privacy

## Setup

1. Sign in to the HopBase console at https://api.hop-base.com and create an API key.
2. When you create (or edit) the key, add the **group** that contains the models you want. A key can include several groups, and it can call only the models of the groups it includes. See the table below.
3. In Dify, open **Settings > Model Provider**, install **HopBase** and paste the key.
4. Leave **API Base URL** empty to use `https://api.hop-base.com/v1`. Only change it if HopBase gives you a different endpoint.

Saving the provider checks the key with `GET /v1/models`, which spends no quota. A predefined model that is not in one of your key's groups is still listed in Dify, but calling it returns `model_not_found`; add the matching group to the key to use it.

## Predefined models

| Model ID | Group in the HopBase console | Context | Max output | Tool calling | Vision |
| --- | --- | --- | --- | --- | --- |
| `deepseek-v4.1-flash-1017-sg` | DeepSeek Singapore Data Center | 1M | 393,216 | yes | yes |
| `deepseek-v4.1-flash-1017` | DeepSeek | 1M | 393,216 | yes | yes |
| `deepseek-v4-pro-202606` | DeepSeek | 1M | 393,216 | yes | no |
| `doubao-seed-2-1-pro-260915` | Doubao Seed Cloud | 1M | 256K | yes | yes |
| `doubao-seed-2-1-lite-260915` | Doubao Seed Cloud | 1M | 256K | yes | yes |
| `gemini-3.8-flash` | Gemini | 1M | 65,536 | yes | yes |
| `gemini-3.1-pro-preview` | Gemini | 1M | 65,536 | yes | yes |
| `gpt-5.6-sol` | Codex Plus, Codex Pro or GPT Official Direct | 1.05M | 128,000 | yes | yes |
| `grok-4.7` | Grok Suite | 500K | 131,072 | yes | yes |
| `kimi-k3` | Kimi K3 Cloud | 1M | 32,768 | yes | yes (base64 images) |
| `glm-5.3` | GLM Official Direct | 1M | 131,072 | yes | no |

All predefined models stream. Models that think (for example DeepSeek V4.1 Flash, Doubao Seed and GLM-5.3) return their reasoning in `reasoning_content`, which Dify shows as a collapsible thinking block. Group names and model availability can change; your key's `GET /v1/models` response is always authoritative.

## Other models

Any other chat model your key can reach can be added as a custom model:

1. In **Settings > Model Provider > HopBase**, choose **Add Model**.
2. Enter the model ID exactly as `GET https://api.hop-base.com/v1/models` returns it for your key (for example `deepseek-v4.1-flash` or `qwen3.8-max`).
3. Set the context size, the max-tokens upper bound, and whether the model supports tool calling and image input. The catalog at https://hop-base.com/models and the docs list these per model.

Saving a custom model sends one short test request to it.

Only chat models served over `POST /v1/chat/completions` work with this plugin. Image, video and speech models, and models served only over other endpoints, are not exposed in Dify.

## Credentials

| Field | Required | Description |
| --- | --- | --- |
| API Key | yes | Your HopBase API key. |
| API Base URL | no | Defaults to `https://api.hop-base.com/v1`. |

## Connection requirements

The Dify server needs outbound HTTPS access to `api.hop-base.com` (or the API Base URL you configure).

## Notes

The plugin extends the Dify SDK's OpenAI-compatible model class, so request and streaming behavior match the standard OpenAI-compatible provider. The Dify end-user ID is not forwarded to HopBase. Usage is billed by HopBase to your account; see your console for rates.

## Installing a package from GitHub

The Dify Marketplace is the recommended source. To install a `.difypkg` from this repository's [releases](https://github.com/victor-zzh/dify-plugin-hopbase/releases) on a self-hosted Dify instead, use **Plugins > Install plugin > Local package file**. Packages outside the Marketplace are not signed by Dify, so the plugin daemon must allow unsigned plugins (`FORCE_VERIFYING_SIGNATURE=false` in the Dify docker `.env`).

## Support

Open an issue at https://github.com/victor-zzh/dify-plugin-hopbase/issues. For account, billing or key questions, use the contact channels in the HopBase console.

## License

MIT
