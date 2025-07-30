# https://github.com/sidharthrajaram/mcp-sse/tree/main
import httpx
import uvicorn
from typing import Any

from mcp.server.fastmcp import FastMCP, Context
from fastapi import FastAPI
from starlette.routing import Mount
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from user_db import validate_api_key, get_user_by_api_key

class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication.
    Accepts API key either via x-api-key header, as a Bearer token, or as a query parameter.
    """
    async def dispatch(self, request: Request, call_next):

        # Skip authentication for docs and schema endpoints
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
            
        # For n8n community node, Cursor MCP or other clients that authorize via query parameter
        if request.url.path.startswith('/messages/') or request.url.path == '/messages':
           return await call_next(request)
            
        # Try to get API key from multiple sources
        
        # 1. HEADER AUTHENTICATION
        api_key = request.headers.get("x-api-key")
         
        # 2. BEARER AUTHENTICATION
        if not api_key:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                api_key = auth_header[7:]  # Remove "Bearer " prefix
        
        # 3. QUERY PARAMETER AUTHENTICATION
        if not api_key:
            api_key = request.query_params.get("api_key")
         
        if not api_key or not validate_api_key(api_key):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"}
            )
            
        # Add user info to request state
        request.state.user = get_user_by_api_key(api_key)
        
        # Continue processing the request
        return await call_next(request)


# Create a FastAPI app
app = FastAPI(
    title="MCP Weather API Server",
    description="MCP Server for Weather Tools",
    version="1.0.0"
)

# 初始化Weather工具的FastMCP伺服器(SSE)
mcp = FastMCP(
    name="weather"
)

# Mount the MCP SSE app to the root path
app.router.routes.append(Mount('/', app=mcp.sse_app()))
# Add authentication middleware
app.add_middleware(APIKeyMiddleware)

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""


@mcp.tool()
async def get_alerts(state: str, ctx: Context) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    await ctx.info(f"Fetching alerts for state: {state}")
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    await ctx.info(f"Received data: {data}")

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)


@mcp.tool()
async def get_forecast(latitude: float, longitude: float, ctx: Context) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    await ctx.info(f"Received data: {points_data}")

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)


@mcp.resource("weather://logs")
async def get_logs() -> str:
    """Get the logs of the weather tool."""
    return "Logs are not available in this version."


if __name__ == "__main__":
    """Run the MCP SSE-based server."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    args = parser.parse_args()

    mcp.settings.host = args.host
    mcp.settings.port = args.port
    mcp.run(
        transport="streamable-http"
    )
    uvicorn.run(app, host=mcp.settings.host, port=mcp.settings.port)