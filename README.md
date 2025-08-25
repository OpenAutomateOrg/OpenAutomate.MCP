# OpenAutomate MCP Server

This MCP (Model Context Protocol) server provides integration between AI assistants and the OpenAutomate platform.

## Features

- Get all automation packages for a tenant
- Get all bot agents for a tenant  
- Start executions by auto-selecting available agents or specifying agent name
- Supports multi-tenant architecture

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

Or install from setup.txt:
```bash
pip install mcp[cli] openai-agents requests
```

## Configuration

The server uses environment variables for configuration:

### Environment Variables

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `OPENAUTOMATE_API_BASE_URL` | Base URL for OpenAutomate API | `http://localhost:5252` |

### Development Setup

For local development, the server will use the default localhost URL:
```bash
python mcp_server.py
```

### Production Deployment

Set the environment variable to point to your production API:

**Linux/macOS:**
```bash
export OPENAUTOMATE_API_BASE_URL=https://api.openautomate.io
python mcp_server.py
```

**Windows:**
```cmd
set OPENAUTOMATE_API_BASE_URL=https://api.openautomate.io
python mcp_server.py
```

**Docker:**
```bash
docker run -e OPENAUTOMATE_API_BASE_URL=https://api.openautomate.io your-mcp-server
```

**Docker Compose:**
```yaml
services:
  mcp-server:
    build: .
    environment:
      - OPENAUTOMATE_API_BASE_URL=https://api.openautomate.io
    ports:
      - "8000:8000"
```

## Usage

The MCP server provides the following tools:

### get_all_packages
Get all automation packages for a tenant.

**Parameters:**
- `jwt_token`: JWT authentication token
- `tenant_slug`: Tenant slug for multi-tenancy

### get_all_agents  
Get all bot agents for a tenant.

**Parameters:**
- `jwt_token`: JWT authentication token
- `tenant_slug`: Tenant slug for multi-tenancy

### start_an_execution
Start an execution by auto-selecting an available bot agent or by agent name.

**Parameters:**
- `package_name`: Name of the automation package to execute
- `jwt_token`: JWT authentication token
- `tenant_slug`: Tenant slug for multi-tenancy
- `version`: Package version to execute (defaults to 'latest')
- `agent_name`: Optional agent name to use for execution

## Running the Server

```bash
python mcp_server.py
```

The server will start and listen for MCP connections using Server-Sent Events (SSE) transport..