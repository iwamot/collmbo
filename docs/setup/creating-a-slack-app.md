# Creating a Slack App

To get started with Collmbo, create a Slack app and configure it with the necessary tokens and scopes.

## Steps

### 1. Create a Slack App

- Go to <https://api.slack.com/apps>.
- Create a new Slack app using [`manifest.yml`](../../manifest.yml).

*Note: You can customize the manifest whenever needed.*

### 2. Generate an App-Level Token

- In your app settings, go to **Basic Information > App-Level Tokens**.
- Generate a new token with `connections:write` scope.
- Copy the generated token (`xapp-1-...`) and keep it for later.

### 3. Install the App to Your Workspace

- In your app settings, go to **Install App**.
- Install the app to your workspace.
- After installation, copy the **Bot User OAuth Token** (`xoxb-...`) and keep it for later.

### 4. Invite the App to Slack Channel(s)

- In Slack, go to the channel where you want to use Collmbo.
- Run `/invite @Collmbo`.
