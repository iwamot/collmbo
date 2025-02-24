# Collmbo

**A Slack app for AI chat with flexible model selection powered by LiteLLM.** Pronounced the same as "Colombo".

> ![](https://github.com/user-attachments/assets/a377b868-3673-4798-b415-44e674cf7ae6)

## Quick Start

First, create a new Slack app using `manifest.yml` and obtain required tokens:

- App-level token (`xapp-1-...` from Basic Information > App-Level Tokens)
- Bot token (`xoxb-...` from OAuth & Permissions after installing the app)

Then, pick your favorite model from [LiteLLM's supported models](https://docs.litellm.ai/docs/providers) and run Collmbo. Here are some examples:

### OpenAI (gpt-4o)

```sh
$ cat env
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
OPENAI_API_KEY=sk-...
LITELLM_MODEL=gpt-4o

$ docker run -it --env-file ./env ghcr.io/iwamot/collmbo:latest-slim
```

### Azure OpenAI (gpt-4-0613)

```sh
$ cat env
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
AZURE_API_KEY=...
AZURE_API_BASE=...
AZURE_API_VERSION=...
LITELLM_MODEL=azure/<your_deployment_name>
LITELLM_MODEL_TYPE=azure/gpt-4-0613

$ docker run -it --env-file ./env ghcr.io/iwamot/collmbo:latest-slim
```

### Gemini - Google AI Studio (Gemini 1.5 Flash)

```sh
$ cat env
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
GEMINI_API_KEY=...
LITELLM_MODEL=gemini/gemini-1.5-flash

$ docker run -it --env-file ./env ghcr.io/iwamot/collmbo:latest-slim
```

### Amazon Bedrock (Claude 3.5 Sonnet v2)

```sh
$ cat env
SLACK_APP_TOKEN=...
SLACK_BOT_TOKEN=...
LITELLM_MODEL=bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0

# You can specify a Bedrock region if it's different from your default AWS region
AWS_REGION_NAME=us-west-2

# You can use your access key for authentication, but IAM roles are recommended
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

$ docker run -it --env-file ./env ghcr.io/iwamot/collmbo:latest-full
```

*Note: `full` flavor images include boto3.*

## Features

- Flexible model selection
- [Tools (Function Calling)](https://github.com/iwamot/collmbo/wiki/Tools-(Function-Calling)): `LITELLM_TOOLS_MODULE_NAME=tests.tools_example`
- [Custom callbacks](https://github.com/iwamot/collmbo/wiki/Custom-callbacks): `LITELLM_CALLBACK_MODULE_NAME=tests.callback_example`
- [Redaction](https://github.com/iwamot/collmbo/wiki/Redaction): `REDACTION_ENABLED=true`
- [Image input](https://github.com/iwamot/collmbo/wiki/Image-input): `IMAGE_FILE_ACCESS_ENABLED=true`
- PDF input:`IMAGE_PDF_ACCESS_ENABLED=true`

## Contributing

Questions and suggestions welcome! Feel free to open an issue.

## Related Projects

- [seratch/ChatGPT-in-Slack](https://github.com/seratch/ChatGPT-in-Slack) – The original project by @seratch.

## License

MIT
