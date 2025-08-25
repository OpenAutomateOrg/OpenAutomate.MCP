from mcp.server.fastmcp import FastMCP
import requests
import json
import os
from typing import Optional
from fastapi.responses import JSONResponse

# Configuration - Environment variables with fallback defaults
# Normalize to avoid stray whitespace causing malformed URLs (e.g., host%20)
_RAW_BASE_URL = os.getenv("OPENAUTOMATE_API_BASE_URL", "http://localhost:5252") or ""
OPENAUTOMATE_API_BASE_URL = _RAW_BASE_URL.strip().rstrip("/")
print(f"API Base URL: {OPENAUTOMATE_API_BASE_URL}")

mcp = FastMCP(
    name="mcp-server"
)


# URL helpers
def _sanitize_tenant_slug(tenant_slug: str) -> str:
    return (tenant_slug or "").strip().strip("/")


def _build_api_url(tenant_slug: str, *path_segments: str) -> str:
    tenant = _sanitize_tenant_slug(tenant_slug)
    # Strip slashes/spaces from segments and join
    cleaned_segments = [seg.strip(" /") for seg in path_segments if seg is not None and seg != ""]
    if cleaned_segments:
        return f"{OPENAUTOMATE_API_BASE_URL}/{tenant}/" + "/".join(cleaned_segments)
    return f"{OPENAUTOMATE_API_BASE_URL}/{tenant}"


# Simple HTTP logging utilities
def _sanitize_headers(headers):
    sanitized = {}
    if headers:
        for key, value in headers.items():
            if isinstance(key, str) and key.lower() == "authorization":
                sanitized[key] = "Bearer ***" if isinstance(value, str) and value.startswith("Bearer ") else "***"
            else:
                sanitized[key] = value
    return sanitized


def _perform_request(method: str, url: str, headers=None, params=None, json_body=None):
    try:
        print("[HTTP] ----------------------------------------")
        print(f"[HTTP] {method.upper()} {url}")
        if params:
            try:
                print(f"[HTTP] Query: {json.dumps(params, separators=(',', ':'))}")
            except Exception:
                print(f"[HTTP] Query: {params}")
        if json_body is not None:
            try:
                print(f"[HTTP] Body: {json.dumps(json_body, indent=2)}")
            except Exception:
                print(f"[HTTP] Body: {json_body}")
        print(f"[HTTP] Headers: {json.dumps(_sanitize_headers(headers))}")

        response = requests.request(method=method, url=url, headers=headers, params=params, json=json_body)

        print(f"[HTTP] Status: {response.status_code}")
        try:
            print(f"[HTTP] Response: {response.text}")
        except Exception as e:
            print(f"[HTTP] Response could not be printed: {e}")
        print("[HTTP] ----------------------------------------")
        return response
    except Exception as e:
        print(f"[HTTP] Error during request: {e}")
        print("[HTTP] ----------------------------------------")
        raise


@mcp.tool()
def get_current_temperature_by_city(city_name: str) -> str:
    return "20 degrees celcius"


@mcp.tool()
def get_all_packages(jwt_token: str, tenant_slug: str) -> str:
    """Get all automation packages for a tenant
    
    Args:
        jwt_token: JWT authentication token
        tenant_slug: Tenant slug for multi-tenancy
    
    Returns:
        JSON response containing all packages for the tenant
    """
    
    base_url = OPENAUTOMATE_API_BASE_URL
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        packages_url = _build_api_url(tenant_slug, "api/packages")
        packages_response = _perform_request("GET", packages_url, headers=headers)
        
        if packages_response.status_code == 200:
            packages = packages_response.json()
            return json.dumps({
                "success": True,
                "packages": packages,
                "count": len(packages),
                "message": f"Retrieved {len(packages)} packages for tenant '{tenant_slug}'"
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": "Failed to fetch packages",
                "details": f"Status: {packages_response.status_code}, Response: {packages_response.text}"
            }, indent=2)
    
    except requests.exceptions.RequestException as e:
        return json.dumps({
            "success": False,
            "error": "Network error",
            "details": str(e)
        }, indent=2)
    except json.JSONDecodeError as e:
        return json.dumps({
            "success": False,
            "error": "JSON parsing error",
            "details": str(e)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": "Unexpected error",
            "details": str(e)
        }, indent=2)


@mcp.tool()
def get_all_agents(jwt_token: str, tenant_slug: str) -> str:
    """Get all bot agents for a tenant
    
    Args:
        jwt_token: JWT authentication token
        tenant_slug: Tenant slug for multi-tenancy
    
    Returns:
        JSON response containing all bot agents for the tenant
    """
    
    base_url = OPENAUTOMATE_API_BASE_URL
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        agents_url = _build_api_url(tenant_slug, "api/agents")
        agents_response = _perform_request("GET", agents_url, headers=headers)
        
        if agents_response.status_code == 200:
            agents = agents_response.json()
            
            # Add summary information about agent statuses
            agent_summary = {}
            for agent in agents:
                status = agent.get("status", "Unknown")
                is_active = agent.get("isActive", False)
                key = f"{status} ({'Active' if is_active else 'Inactive'})"
                agent_summary[key] = agent_summary.get(key, 0) + 1
            
            return json.dumps({
                "success": True,
                "agents": agents,
                "count": len(agents),
                "summary": agent_summary,
                "message": f"Retrieved {len(agents)} bot agents for tenant '{tenant_slug}'"
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": "Failed to fetch bot agents",
                "details": f"Status: {agents_response.status_code}, Response: {agents_response.text}"
            }, indent=2)
    
    except requests.exceptions.RequestException as e:
        return json.dumps({
            "success": False,
            "error": "Network error",
            "details": str(e)
        }, indent=2)
    except json.JSONDecodeError as e:
        return json.dumps({
            "success": False,
            "error": "JSON parsing error",
            "details": str(e)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": "Unexpected error",
            "details": str(e)
        }, indent=2)



@mcp.tool()
def start_an_execution(package_name: str, jwt_token: str,
                        tenant_slug: str, version: str = "latest", agent_name: Optional[str] = None) -> str:
    """Start an execution by auto-selecting an available bot agent or by agent name
    
    Args:
        package_name: Name of the automation package to execute
        jwt_token: JWT authentication token
        tenant_slug: Tenant slug for multi-tenancy
        version: Package version to execute (defaults to 'latest')
        agent_name: Optional agent name to use for execution. If not provided, auto-selects any non-Disconnected agent.
    
    Returns:
        JSON response from the execution trigger API
    """
    
    base_url = OPENAUTOMATE_API_BASE_URL
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        # Step 1: Get all bot agents
        bot_agents_url = _build_api_url(tenant_slug, "api/agents")
        bot_agents_response = _perform_request("GET", bot_agents_url, headers=headers)
        
        if bot_agents_response.status_code != 200:
            return json.dumps({
                "success": False,
                "error": "Failed to fetch bot agents",
                "details": f"Status: {bot_agents_response.status_code}, Response: {bot_agents_response.text}"
            }, indent=2)
        
        bot_agents = bot_agents_response.json()
        
        # Find suitable bot agent
        selected_bot_agent = None
        
        if agent_name:
            # Look for agent by name (must be non-Disconnected and active)
            for agent in bot_agents:
                if (agent.get("name") == agent_name and 
                    agent.get("status") != "Disconnected" and 
                    agent.get("isActive")):
                    selected_bot_agent = agent
                    break
            
            if not selected_bot_agent:
                # Show available agents for debugging
                available_agents = [
                    {
                        "name": agent.get("name"), 
                        "status": agent.get("status"), 
                        "isActive": agent.get("isActive")
                    } 
                    for agent in bot_agents 
                    if agent.get("status") != "Disconnected" and agent.get("isActive")
                ]
                return json.dumps({
                    "success": False,
                    "error": f"Agent '{agent_name}' not found or not available",
                    "details": f"Agent must be active and not Disconnected (Available or Busy status is okay)",
                    "available_agents": available_agents
                }, indent=2)
        else:
            # Auto-select any non-Disconnected active agent (Available or Busy is okay)
            for agent in bot_agents:
                if (agent.get("status") != "Disconnected" and 
                    agent.get("isActive")):
                    selected_bot_agent = agent
                    break
        
        if not selected_bot_agent:
            # Show all agents for debugging
            agent_statuses = [
                {
                    "name": agent.get("name"), 
                    "status": agent.get("status"), 
                    "isActive": agent.get("isActive")
                } 
                for agent in bot_agents
            ]
            return json.dumps({
                "success": False,
                "error": "No suitable bot agents found",
                "details": "Need at least one active agent that is not Disconnected (Available or Busy status is okay)",
                "all_agents": agent_statuses
            }, indent=2)
        
        # Step 2: Get package by name
        packages_url = _build_api_url(tenant_slug, "api/packages")
        packages_response = _perform_request("GET", packages_url, headers=headers)
        
        if packages_response.status_code != 200:
            return json.dumps({
                "success": False,
                "error": "Failed to fetch packages",
                "details": f"Status: {packages_response.status_code}, Response: {packages_response.text}"
            }, indent=2)
        
        packages = packages_response.json()
        
        # Find package by name
        target_package = None
        for package in packages:
            if package.get("name") == package_name:
                target_package = package
                break
        
        if not target_package:
            # Show available packages for debugging
            package_names = [pkg.get("name") for pkg in packages]
            return json.dumps({
                "success": False,
                "error": f"Package '{package_name}' not found",
                "available_packages": package_names
            }, indent=2)
        
        # Determine version to use
        package_version = version
        if version == "latest" or not version:
            # Get the latest version from the package versions
            versions = target_package.get("versions", [])
            if versions:
                # Sort versions and get the latest (assuming semantic versioning)
                latest_version = sorted(versions, key=lambda v: v.get("createdAt", ""), reverse=True)[0]
                package_version = latest_version.get("versionNumber", "1.0.0")
            else:
                package_version = "1.0.0"
        
        # Step 3: Trigger execution
        execution_data = {
            "botAgentId": selected_bot_agent["id"],
            "packageId": target_package["id"],
            "packageName": package_name,
            "version": package_version
        }
        
        trigger_url = _build_api_url(tenant_slug, "api/executions/trigger")
        execution_response = _perform_request("POST", trigger_url, headers=headers, json_body=execution_data)
        
        if execution_response.status_code == 200:
            result = execution_response.json()
            return json.dumps({
                "success": True,
                "execution": result,
                "bot_agent": {
                    "id": selected_bot_agent["id"],
                    "name": selected_bot_agent["name"],
                    "status": selected_bot_agent["status"],
                    "selection_method": "by_name" if agent_name else "auto_selected"
                },
                "package": {
                    "id": target_package["id"],
                    "name": package_name,
                    "version": package_version
                },
                "message": f"Execution started successfully for package '{package_name}' version '{package_version}' on bot agent '{selected_bot_agent['name']}' (Status: {selected_bot_agent['status']})"
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": "Failed to trigger execution",
                "details": f"Status: {execution_response.status_code}, Response: {execution_response.text}",
                "request_data": execution_data
            }, indent=2)
    
    except requests.exceptions.RequestException as e:
        return json.dumps({
            "success": False,
            "error": "Network error",
            "details": str(e)
        }, indent=2)
    except json.JSONDecodeError as e:
        return json.dumps({
            "success": False,
            "error": "JSON parsing error",
            "details": str(e)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": "Unexpected error",
            "details": str(e)
        }, indent=2)


# Add health check endpoint for AWS App Runner
@mcp.app.get("/health")
async def health_check():
    """Health check endpoint for AWS App Runner"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "OpenAutomate MCP Server",
            "api_url": OPENAUTOMATE_API_BASE_URL,
            "transport": "sse"
        }
    )

if __name__ == "__main__":
    mcp.run(transport='sse')
