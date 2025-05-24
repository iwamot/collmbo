# Collmbo

[![flake8](https://github.com/iwamot/collmbo/actions/workflows/flake8.yml/badge.svg)](https://github.com/iwamot/collmbo/actions/workflows/flake8.yml)
[![mypy](https://github.com/iwamot/collmbo/actions/workflows/mypy.yml/badge.svg)](https://github.com/iwamot/collmbo/actions/workflows/mypy.yml)
[![pytest](https://github.com/iwamot/collmbo/actions/workflows/tests.yml/badge.svg)](https://github.com/iwamot/collmbo/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/iwamot/collmbo/branch/main/graph/badge.svg)](https://app.codecov.io/gh/iwamot/collmbo)

![Collmbo icon](https://github.com/user-attachments/assets/b13da1c7-5d2f-4ad3-8c5b-9ef4e500deb8)

**A Slack bot that lets you choose your preferred LLM using [LiteLLM](https://github.com/BerriAI/litellm).** Pronounced the same as "Colombo".

> ![](https://github.com/user-attachments/assets/a377b868-3673-4798-b415-44e674cf7ae6)

## Quick Start

Collmbo supports multiple LLMs, but let's begin with OpenAI's gpt-4o model for a quick setup.

### 1. Create a Slack App

[Create a Slack app](https://github.com/iwamot/collmbo/wiki/Creating-a-Slack-App) and obtain the required tokens:

- App-level token (`xapp-1-...`)
- Bot token (`xoxb-...`)

### 2. Create a `.env` File

Save your credentials in a `.env` file:

```sh
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
LITELLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...
```

### 3. Run Collmbo Container

Start the bot using Docker:

```sh
docker run -it --env-file .env ghcr.io/iwamot/collmbo:latest-slim
```

> [!NOTE]
>
> #### Why `latest-slim` Here?
>
> Collmbo provides two official Docker image flavors:
>
> | Flavor | Description |
> |--------|-------------|
> | `slim` | A minimal image with only essential dependencies |
> | `full` | A full-featured image with additional libraries (e.g., `boto3` for Amazon Bedrock) |
>
> You must specify a flavor explicitly. If you want to use the latest image, use `latest-slim` or `latest-full`.
>
> Additionally, you can specify a versioned tag like `x.x.x-slim`. For more details, please check the [list of available tags](https://github.com/iwamot/collmbo/pkgs/container/collmbo/versions?filters%5Bversion_type%5D=tagged).

### 4. Say Hello!

Mention the bot in Slack and start chatting:

```
@Collmbo hello!
```

Collmbo should respond in channels, threads, and DMs.

## Want to Use a Different LLM?

First, pick your favorite LLM from [LiteLLM supported providers](https://docs.litellm.ai/docs/providers).

To use it, update the relevant environment variables in your `.env` file and restart the container.

Here are some examples:

### Gemini - Google AI Studio (Gemini 2.0 Flash)

```sh
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
LITELLM_MODEL=gemini/gemini-2.0-flash-001
GEMINI_API_KEY=...
```

### Azure OpenAI (gpt-4o)

```sh
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
LITELLM_MODEL=azure/<your_deployment_name>

# Specify the model type to grab details like max input tokens
LITELLM_MODEL_TYPE=azure/gpt-4o

AZURE_API_KEY=...
AZURE_API_BASE=...
AZURE_API_VERSION=...
```

### Amazon Bedrock (Claude Sonnet 4)

```sh
SLACK_APP_TOKEN=...
SLACK_BOT_TOKEN=...
LITELLM_MODEL=bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0

# You can specify a Bedrock region if it's different from your default AWS region
AWS_REGION_NAME=us-west-2

# You can use your access key for authentication, but IAM roles are recommended
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

When using Amazon Bedrock, as mentioned earlier, you need to use the `full` flavor image:

```
docker run -it --env-file .env ghcr.io/iwamot/collmbo:latest-full
```

## Deployment

Collmbo does not serve endpoints and can run in any environment with internet access.

## Features

- **[Tools (Function Calling)](https://github.com/iwamot/collmbo/wiki/Tools-(Function-Calling))** - Extends functionality with function calling.
- **[Custom callbacks](https://github.com/iwamot/collmbo/wiki/Custom-callbacks)** - Hooks into requests and responses for custom processing.
- **[Redaction](https://github.com/iwamot/collmbo/wiki/Redaction)** - Masks sensitive information before sending requests.
- **[Slack-friendly formatting](https://github.com/iwamot/collmbo/wiki/Slack%E2%80%90friendly-formatting)** - Formats messages for better readability in Slack.
- **[Image input](https://github.com/iwamot/collmbo/wiki/Image-input)** - Enables AI models to analyze uploaded images.
- **[PDF input](https://github.com/iwamot/collmbo/wiki/PDF-input)** - Enables AI models to analyze uploaded PDFs.
- **[Prompt caching](https://github.com/iwamot/collmbo/wiki/Prompt-caching)** - May help reduce costs by reusing context (Anthropic Claude, Amazon Bedrock).

## Configuration

Collmbo runs with default settings, but you can customize its behavior by [setting optional environment variables](https://github.com/iwamot/collmbo/wiki/Optional-Settings).

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

Before opening a PR, please run:

```sh
./validate.sh
```

This helps maintain code quality.

## Related Projects

- [seratch/ChatGPT-in-Slack](https://github.com/seratch/ChatGPT-in-Slack) - The original project by @seratch.

## License

**The code** in this repository is licensed under the **MIT License**.

**The Collmbo icon** (`assets/icon.png`) is licensed under **[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)**. For example, you may use it as a Slack profile icon.
