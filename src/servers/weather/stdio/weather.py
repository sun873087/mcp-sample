from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# 初始化 FastMCP 伺服器
mcp = FastMCP("Weather")

# 常數
NWS_API_BASE_URL = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """
    發送 HTTP 請求到 NOAA 天氣 API 並返回 JSON 響應
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            return None
        
def format_alert(feature: dict) -> str:
    """
    格式化 NOAA 警報資料
    """
    props = feature["properties"]
    return f"""
Event: {props.get("event", "Unknown")}
Area: {props.get("areaDesc", "Unknown")}
Severity: {props.get("severity", "Unknown")}
Description: {props.get("description", "No description available")}
Instructions: {props.get("instruction", "No specific instructions provided")}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """
    獲取美國特定州份的警報資料.

    Args:
        state (str): 美國州份的縮寫 (e.g., "CA", "TX", "NY")
        
    Returns:
        str: 警報資料的文字描述
    """
    url = f"{NWS_API_BASE_URL}/alerts/active/area/{state}"
    data = await make_nws_request(url)
    
    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."
    
    if not data["features"]:
        return "No active alerts found for the given state."
    
    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """
    獲取特定位置的預報資料

    Args:
        latitude (float): 緯度
        longitude (float): 經度
    """
    # 首先取得預測網格端點
    points_url = f"{NWS_API_BASE_URL}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."
    
    # 從端點取得詳細預報
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."
    
    periods = forecast_data["properties"]["periods"]
    forecasts = []

    for period in periods[:5]:
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n\n".join(forecasts)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')