# Gmail MCP Server

This MCP (Model Context Protocol) server provides tools for common operations with gmail.


## Features

- `send_mail`: Send new emails


## Prerequisites

1. **Python 3.12+**
2. [**uv**](https://github.com/astral-sh/uv) - Fast Python package installer and resolver
3. **Google Cloud Console Setup**
  - Go to: [Google Cloud Console](https://console.cloud.google.com/)
  - Create a new project for this MCP Server
  - Enable Gmail API
    - Go to: **APIs and services > Library**
    - Search: **Gmail API**
    - Click on: **Gmail API** tile in the results
    - Click on: **Enable**
  - Setup OAuth
    - Go to: **APIs and services > Credentials**
    - Click on": **Create Credentials > OAuth client ID**
    - Choose Application Type: **Web application**
    - Add: **Authorised redirect URIs**: **http://localhost:4321/**
    - Create client
    - Download the JSON and save it to `credentials.json` in this project root. This has the **Client ID**, **Client Secret**, etc. 



## Installation

1. From this repo root:

  ```bash
  cd mcp-serveur-gmail
  ```

2. Create a virtual environment and install the package in development mode:

    ```bash
    # Create a virtual environment
    uv venv
    
    # Activate the virtual environment
    # On macOS/Linux:
    source .venv/bin/activate
    # On Windows:
    .venv\Scripts\activate
    
    # Install dependencies
    uv sync
    ```

**Get Refresh Token**  

```python
python get_refresh_token.py
```

This will:
1. Start a server on `port`: `4321` to receive `tokens` post Google OAuth
2. Open your browser for Google OAuth
3. On succeeful authentication it will save `token.json` with `refresh_token` along with `client_id`, and `client_secret`.
4. It will also display the `refresh_token` on console.
 

**Create .env**  
```bash
cp example.env .env
```

Setup the corresponding value using what you received in the previous step.



## Inspect

Use MCP Inspector to test it in the development mode.

```bash
mcp dev server.py
```


## Claude Desktop Integration

Once your server is ready, install it in Claude Desktop

```bash
mcp install server.py --with google-auth --with google-auth-oauthlib --with google-auth-httplib2 --with google-api-python-client -f .env
```



MCP server configuration:

```json
{
  "mcpServers": {
    "gmail-mcp-server": {
      "command": "uv",
      "args": [
          "--directory",
          "/:your.path.to/mcp-serveur-gmail",
          "run",
          "server.py"
      ],
      "env": {
        "CLIENT_ID": "google.auth.app.client.id",
        "CLIENT_SECRET": "google.auth.app.client.secret",
        "REFRESH_TOKEN": "google.auth.app.refresh.token"
      }   
    }   
  }
}
```