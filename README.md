# Collmbo

Collmbo, pronounced the same as "Colombo", is a Slack app that lets end-users chat with AI. Powered by LiteLLM for flexible model selection. Forked from [seratch/ChatGPT-in-Slack](https://github.com/seratch/ChatGPT-in-Slack).

![](https://github.com/user-attachments/assets/fc078de0-406e-4d4d-abb1-f6e30a0dbeab)

## Quick Start: OpenAI (gpt-4o)

```sh
$ cat env
# Create a new Slack app using manifest.yml and grab the app-level token
SLACK_APP_TOKEN=xapp-1-...

# Install the app into your workspace to grab this token
SLACK_BOT_TOKEN=xoxb-...

# Visit https://platform.openai.com/api-keys for this token
OPENAI_API_KEY=sk-...

# Specify a model name supported by LiteLLM
LITELLM_MODEL=gpt-4o

$ docker run -it --env-file ./env ghcr.io/iwamot/collmbo:latest-slim
```

## Advanced Usage

### Azure OpenAI (gpt-4-0613)

```sh
$ cat env
SLACK_APP_TOKEN=...
SLACK_BOT_TOKEN=...
AZURE_API_KEY=...
AZURE_API_BASE=...
AZURE_API_VERSION=...
LITELLM_MODEL=azure/<your_deployment_name>
LITELLM_MODEL_TYPE=azure/gpt-4-0613

$ docker run -it --env-file ./env ghcr.io/iwamot/collmbo:latest-slim
```

### Amazon Bedrock (Claude 3.5 Sonnet v2)

```sh
$ cat env
SLACK_APP_TOKEN=...
SLACK_BOT_TOKEN=...
LITELLM_MODEL=bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0
# Recommend using IAM roles for authentication

$ docker run -it --env-file ./env ghcr.io/iwamot/collmbo:latest-full
```

*Note: `full` flavor images include boto3.*

## Supported Features

- Flexible model selection
- Redaction (`REDACTION_ENABLED=true`)
- Image reading (`IMAGE_FILE_ACCESS_ENABLED=true`, for supported models only)
- Tools / Function calling (`LITELLM_TOOLS_MODULE_NAME=tests.tools_example`, for supported models only)
- Custom callbacks (`LITELLM_CALLBACK_MODULE_NAME=tests.callback_example`)

## Contributing

We welcome contributions to Collmbo! If you have any feature requests, bug reports, or other issues, please feel free to open an issue on this repository. Your feedback and contributions help make Collmbo better for everyone.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
