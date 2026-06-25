# MCP Tools

Collmbo can integrate with MCP servers using streamable HTTP transport.

Each server in [`config/mcp.yml`](../../config/mcp.yml) declares an `auth_type`:

- `none`: No authentication. Available to all users.
- `bearer`: A static token that Collmbo sends as an `Authorization: Bearer`
  header. Shared by all users. See [Bearer Token MCP Servers](#bearer-token-mcp-servers).
- `user_federation`: Per-user OAuth via AgentCore Identity. Each user signs in
  from the Home tab. See [OAuth MCP Servers](#oauth-mcp-servers).

## Usage

1. Edit [`config/mcp.yml`](../../config/mcp.yml).
2. Run Collmbo.
3. Check the Home tab in Slack to view available MCP servers.
4. Send a message in Slack that triggers tool execution.

## Bearer Token MCP Servers

For an MCP server that authenticates with a static bearer token, set
`auth_type: bearer` and name the environment variable that holds the token via
`token_env`. The token itself is never stored in `config/mcp.yml`.

```yaml
servers:
  - name: Context7
    url: https://mcp.context7.com/mcp
    auth_type: bearer
    token_env: CONTEXT7_TOKEN
```

```sh
CONTEXT7_TOKEN=...
```

Collmbo sends the token as `Authorization: Bearer <token>` on every request to
that server.

If the named environment variable is unset, the server is skipped with a
warning. Because the token belongs to Collmbo rather than an individual user,
these servers are available to all users.

## OAuth MCP Servers

If you will use MCP Servers with OAuth authentication, you need:

### AWS Credentials

AWS credentials are required for AgentCore Identity integration. You can authenticate using:

```sh
# Option 1: Access keys (for testing)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Option 2: IAM roles (recommended for production)
# Use IAM roles (e.g., attached to EC2 instance, ECS task, etc.)
```

### OAuth Callback App

Deploy the [oauth-callback-app](../../oauth-callback-app/) to handle OAuth callbacks with user verification. See [oauth-callback-app/README.md](../../oauth-callback-app/README.md) for setup instructions.

### AgentCore Identity Configuration

[Configure credential provider(s) in Amazon Bedrock AgentCore Identity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/resource-providers.html).

> [!CAUTION]
> **Security Note:** Access tokens are temporarily stored in memory during use. Do not share your Collmbo instance with untrusted parties, as they may be able to access authenticated resources on behalf of users.

## Try this Feature

```sh
$ cat config/mcp.yml
workload_name: Collmbo
auth_session_duration_minutes: 30
agentcore_region: us-west-2
oauth_callback_url: https://abc123.lambda-url.us-west-2.on.aws/callback
servers:
  - name: AWS Knowledge
    url: https://knowledge-mcp.global.api.aws
    auth_type: none
  - name: GitHub
    url: https://api.githubcopilot.com/mcp/
    auth_type: user_federation
    scopes:
      - repo
      - read:packages
      - read:org
    agentcore_provider: github

$ cat env
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-5.2

# AWS credentials for OAuth MCP servers (GitHub example above)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

$ docker run -it --env-file ./env -v ./config:/app/config ghcr.io/iwamot/collmbo:latest
```

`workload_name` will be used as a name for [AgentCore Identity workload](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/creating-agent-identities.html).
