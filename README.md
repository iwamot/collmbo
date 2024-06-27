# Collmbo

Collmbo, pronounced the same as "Colombo", is a Slack app that lets end-users chat with AI. Powered by LiteLLM for flexible model selection. Forked from [seratch/ChatGPT-in-Slack](https://github.com/seratch/ChatGPT-in-Slack).

## Features

### Supported

- Flexible model selection
- Redaction (`REDACTION_ENABLED=true`)
- Image reading (`IMAGE_FILE_ACCESS_ENABLED=true`, for supported models only)
- Tools / Function calling (`LITELLM_TOOLS_MODULE_NAME=tests.tools_example`, for supported models only)
- Custom callbacks (`LITELLM_CALLBACK_MODULE_NAME=tests.callback_example`)

### Will Not Be Supported

- Home tab
- Thread summarization
- Serverless Framework deployment

## How to Run

### Docker Build Examples

#### For Amazon Bedrock

```sh
$ docker build -t <your_repository_name>/collmbo --build-arg USE_BEDROCK=true .
```

*Note: This installs boto3.*

#### For Others

```sh
$ docker build -t <your_repository_name>/collmbo .
```

### Run Examples

#### OpenAI (gpt-4o)

```sh
$ cat env
OPENAI_API_KEY=...
LITELLM_MODEL=gpt-4o
SLACK_APP_TOKEN=...
SLACK_BOT_TOKEN=...

$ docker run -it --env-file ./env <your_repository_name>/collmbo
```

#### Azure OpenAI (gpt-4-0613)

```sh
$ cat env
AZURE_API_KEY=...
AZURE_API_BASE=...
AZURE_API_VERSION=...
LITELLM_MODEL=azure/<your_deployment_name>
LITELLM_MODEL_TYPE=azure/gpt-4-0613
SLACK_APP_TOKEN=...
SLACK_BOT_TOKEN=...

$ docker run -it --env-file ./env <your_repository_name>/collmbo
```

#### Amazon Bedrock (Claude 3.5 Sonnet)


```sh
$ cat env
# Recommend using IAM roles for authentication
AWS_REGION_NAME=...
LITELLM_MODEL=bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0
SLACK_APP_TOKEN=...
SLACK_BOT_TOKEN=...

$ docker run -it --env-file ./env <your_repository_name>/collmbo
```
