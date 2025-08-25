#!/usr/bin/env python3
"""
Startup script for OpenAutomate MCP Server
This script ensures the server binds to 0.0.0.0 for App Runner compatibility
"""

import os
import uvicorn

# Import the MCP server to initialize it
from mcp_server import mcp

def main():
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    print("=" * 50)
    print("OpenAutomate MCP Server Startup")
    print("=" * 50)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"API URL: {os.getenv('OPENAUTOMATE_API_BASE_URL', 'http://localhost:5252')}")
    print("=" * 50)
    
    # FastMCP has specific app methods for different transports
    try:
        print("🔍 Using FastMCP's sse_app() method...")
        app = mcp.sse_app()
        print("✅ Successfully got SSE app from FastMCP")

        print(f"🚀 Starting SSE server with uvicorn on {host}:{port}")
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        print(f"❌ Failed to get SSE app: {e}")
        print("🔄 Trying streamable_http_app() method...")

        try:
            app = mcp.streamable_http_app()
            print("✅ Successfully got HTTP app from FastMCP")

            print(f"🚀 Starting HTTP server with uvicorn on {host}:{port}")
            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level="info",
                access_log=True
            )
        except Exception as e2:
            print(f"❌ Failed to get HTTP app: {e2}")
            print("⚠️  Falling back to FastMCP run (will bind to 127.0.0.1)")
            mcp.run(transport='sse')

if __name__ == "__main__":
    main()
