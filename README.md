# Collmbo

<p align="center">
  <img src="https://github.com/user-attachments/assets/b13da1c7-5d2f-4ad3-8c5b-9ef4e500deb8">
</p>

**A Slack bot that lets you choose your preferred LLM using LiteLLM.** Pronounced the same as "Colombo".

> ![](https://github.com/user-attachments/assets/a377b868-3673-4798-b415-44e674cf7ae6)

## Quick Start

Collmbo supports multiple LLMs, but let's begin with OpenAI for a quick setup.

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

### 4. Say Hello!

Mention the bot in Slack and start chatting:

```
@Collmbo hello!
```

## Want to Use a Different LLM?

First, pick your favorite LLM from [LiteLLM supported providers](https://docs.litellm.ai/docs/providers).

To use it, update the relevant environment variables in your `.env` file and restart the container.

Here are some examples:

### Azure OpenAI (gpt-4-0613)

```sh
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
LITELLM_MODEL=azure/<your_deployment_name>
LITELLM_MODEL_TYPE=azure/gpt-4-0613
AZURE_API_KEY=...
AZURE_API_BASE=...
AZURE_API_VERSION=...
```

### Gemini - Google AI Studio (Gemini 1.5 Flash)

```sh
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
LITELLM_MODEL=gemini/gemini-1.5-flash
GEMINI_API_KEY=...
```

### Amazon Bedrock (Claude 3.5 Sonnet v2)

```sh
SLACK_APP_TOKEN=...
SLACK_BOT_TOKEN=...
LITELLM_MODEL=bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0

# You can specify a Bedrock region if it's different from your default AWS region
AWS_REGION_NAME=us-west-2

# You can use your access key for authentication, but IAM roles are recommended
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

When using Amazon Bedrock, use the `full` flavor image instead of `slim` one, as it includes `boto3`, which is required for Bedrock:

```
docker run -it --env-file .env ghcr.io/iwamot/collmbo:latest-full
```

## Deployment

Collmbo does not serve endpoints and can run in any environment with internet access.

## Features

- **[Tools (Function Calling)](https://github.com/iwamot/collmbo/wiki/Tools-(Function-Calling))** – Extends functionality with function calling.
- **[Custom callbacks](https://github.com/iwamot/collmbo/wiki/Custom-callbacks)** – Hooks into requests and responses for custom processing.
- **[Redaction](https://github.com/iwamot/collmbo/wiki/Redaction)** – Masks sensitive information before sending requests.
- **[Slack-friendly formatting](https://github.com/iwamot/collmbo/wiki/Slack%E2%80%90friendly-formatting)** – Formats messages for better readability in Slack.
- **[Image input](https://github.com/iwamot/collmbo/wiki/Image-input)** – Enables AI models to analyze uploaded images.
- **[PDF input](https://github.com/iwamot/collmbo/wiki/PDF-input)** – Enables AI models to analyze uploaded PDFs.

## Configuration

Collmbo runs with default settings, but you can customize its behavior by [setting optional environment variables](https://github.com/iwamot/collmbo/wiki/Optional-Settings).

## Contributing

Questions and suggestions welcome! Feel free to open an issue.

## Related Projects

- [seratch/ChatGPT-in-Slack](https://github.com/seratch/ChatGPT-in-Slack) – The original project by @seratch.

## License

**The code** in this repository is licensed under the **MIT License**.

**The Collmbo icon** (`assets/icon.png`) is licensed under **[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)**. For example, you may use it as a Slack profile icon.
