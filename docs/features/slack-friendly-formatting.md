# Slack-friendly Formatting

## Usage

To format replies for Slack, set the environment variable `SLACK_FORMATTING_ENABLED` to `true`. Collmbo then converts the Markdown the model writes into Slack's mrkdwn before posting.

Messages in the thread are always read as Markdown, whatever this setting is: their blocks, attachments and mrkdwn text are converted before the model sees them.

> [!NOTE]
> `SLACK_FORMATTING_ENABLED` is deprecated. It will be removed when Collmbo posts replies as Markdown, which Slack renders without conversion.

```sh
$ cat env
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-5.5
SLACK_FORMATTING_ENABLED=true

$ docker run -it --env-file ./env ghcr.io/iwamot/collmbo:latest
```

> ![Slack formatting example](https://github.com/user-attachments/assets/6d73ed53-2849-4370-acb3-62694c05f86f)
