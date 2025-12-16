# Simple MCP Weather Server

A minimal MCP server with real weather data from wttr.in (no API key required).

## Local Run

```bash
pip install -r requirements.txt
python server.py
```

## Docker

### Build Image
```bash
docker build -t mcp-server .
```

### Test Container Locally

**Option 1: Using MCP Inspector with Docker**
```bash
# Run container and test with MCP Inspector
npx @modelcontextprotocol/inspector docker run -i mcp-server
```

**Option 2: Interactive Mode**
```bash
# Run container in interactive mode
docker run -i mcp-server
```

**Option 3: Test with a simple script**
```bash
# Run container and pipe MCP messages
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | docker run -i mcp-server
```

## Deploy to AWS ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t mcp-server .
docker tag mcp-server:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/mcp-server:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/mcp-server:latest
```

## Testing

Use MCP Inspector:
```bash
npx @modelcontextprotocol/inspector python server.py
```

Then test the `get_weather` tool with any city name (e.g., "New York", "London", "Tokyo").

