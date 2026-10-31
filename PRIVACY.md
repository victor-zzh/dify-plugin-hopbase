# Privacy

## What this plugin sends

When you use a HopBase model in Dify, this plugin sends the request that Dify builds (messages, system prompt, images, tool definitions, tool results and model parameters) to the HopBase API over HTTPS, authenticated with your HopBase API key. The default endpoint is `https://api.hop-base.com/v1`; if you change **API Base URL** in the credentials, requests go to that URL instead.

When you save the provider credentials, the plugin calls `GET /v1/models` once with your key to check it. Saving a custom model sends one short test request (`ping`) to that model.

The plugin does not forward the Dify end-user ID, and it contacts no other service.

## What this plugin stores

Nothing. The plugin keeps no data and writes no logs of its own. Your API key is stored by Dify in its credential store.

## What HopBase does with requests

HopBase is an API gateway: it forwards each request to the provider of the model you selected and returns the response. HopBase's [Privacy Policy](https://api.hop-base.com/legal/privacy) governs that processing. In summary, it states that:

- Prompts, context, uploaded content and model responses are used to complete the current request and are not retained long-term as platform business data.
- Request content is not used to train models. Necessary excerpts or logs may be processed for troubleshooting, security, abuse investigation, compliance, or when you open a support ticket.
- Request metadata such as time, model name, token usage, cost, status code, IP address, API key identifier and latency is recorded for billing and auditing.
- Requests are processed by the upstream AI provider of the selected model, under that provider's own terms.

The Privacy Policy is authoritative; read it in full at https://api.hop-base.com/legal/privacy. Do not send sensitive personal data you are not permitted to share.
