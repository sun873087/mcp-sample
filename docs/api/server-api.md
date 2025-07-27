# 伺服器 API 參考

本文件詳細說明 MCP Weather Sample 伺服器端提供的工具和 API，包括天氣服務的所有功能和使用方式。

## 目錄

- [天氣工具 API 參考](#天氣工具-api-參考)
- [get_alerts 工具詳細說明](#get_alerts-工具詳細說明)
- [get_forecast 工具詳細說明](#get_forecast-工具詳細說明)
- [API 回應格式](#api-回應格式)
- [錯誤代碼和處理](#錯誤代碼和處理)
- [資源端點](#資源端點)
- [使用範例](#使用範例)

## 天氣工具 API 參考

MCP Weather Sample 提供兩個主要的天氣工具，基於 NOAA (美國國家氣象局) API 提供即時天氣資料。

### 工具概覽

| 工具名稱 | 功能 | 參數 | 回傳類型 |
|----------|------|------|----------|
| `get_alerts` | 取得美國州份天氣警報 | `state: str` | `str` |
| `get_forecast` | 取得座標位置天氣預報 | `latitude: float, longitude: float` | `str` |

### 伺服器架構

專案提供兩種伺服器實現：

#### STDIO 伺服器 (`src/servers/weather/stdio/weather.py`)
- **傳輸方式**: 標準輸入輸出
- **適用場景**: 本地開發、單機應用
- **認證方式**: 無需認證
- **設定複雜度**: 簡單

#### SSE 伺服器 (`src/servers/weather/sse/mcp-weather.py`)
- **傳輸方式**: Server-Sent Events over HTTP
- **適用場景**: 遠端存取、多用戶應用
- **認證方式**: API 金鑰認證
- **設定複雜度**: 中等

## get_alerts 工具詳細說明

取得美國特定州份的現行天氣警報資訊。

### 函數簽名

```python
async def get_alerts(state: str) -> str:
    """
    取得美國特定州份的警報資料
    
    Args:
        state (str): 美國州份的縮寫 (e.g., "CA", "TX", "NY")
        
    Returns:
        str: 警報資料的文字描述
    """
```

### 參數詳細說明

#### state (必需)
- **類型**: `str`
- **格式**: 兩字母美國州份縮寫（大寫）
- **範例**: `"CA"`, `"NY"`, `"TX"`, `"FL"`
- **驗證**: 必須是有效的美國州份代碼

### 支援的州份代碼

| 代碼 | 州份 | 代碼 | 州份 |
|------|------|------|------|
| `AL` | 阿拉巴馬州 | `MT` | 蒙大拿州 |
| `AK` | 阿拉斯加州 | `NE` | 內布拉斯加州 |
| `AZ` | 亞利桑那州 | `NV` | 內華達州 |
| `AR` | 阿肯色州 | `NH` | 新罕布夏州 |
| `CA` | 加利福尼亞州 | `NJ` | 紐澤西州 |
| `CO` | 科羅拉多州 | `NM` | 新墨西哥州 |
| `CT` | 康乃狄克州 | `NY` | 紐約州 |
| `DE` | 德拉瓦州 | `NC` | 北卡羅萊納州 |
| `FL` | 佛羅里達州 | `ND` | 北達科他州 |
| `GA` | 喬治亞州 | `OH` | 俄亥俄州 |
| ... | ... | ... | ... |

### 回應格式

成功時返回格式化的警報資訊：

```
Event: Tornado Warning
Area: Broward County
Severity: Extreme
Description: A tornado warning has been issued for Broward County until 3:00 PM EDT.
Instructions: Take shelter immediately in a sturdy building. Stay away from windows.

---

Event: Flash Flood Watch
Area: Miami-Dade County
Severity: Minor
Description: Heavy rainfall may cause flash flooding in urban areas.
Instructions: Avoid driving through flooded roadways.
```

### 使用範例

#### 基本呼叫

```python
# STDIO 模式
result = await client.session.call_tool(
    "get_alerts",
    arguments={"state": "FL"}
)
print(result.content)

# SSE 模式（透過 MCPHost）
alerts = await host.call_tool("get_alerts", {"state": "CA"})
print(alerts)
```

#### 錯誤處理

```python
try:
    alerts = await host.call_tool("get_alerts", {"state": "XX"})  # 無效州份
except ValueError as e:
    print(f"參數錯誤: {e}")
except Exception as e:
    print(f"API 錯誤: {e}")
```

### 回應狀態

| 情況 | 回應 |
|------|------|
| 有警報 | 格式化的警報清單 |
| 無警報 | `"No active alerts for this state."` |
| API 錯誤 | `"Unable to fetch alerts or no alerts found."` |
| 無效州份 | `"Unable to fetch alerts or no alerts found."` |

## get_forecast 工具詳細說明

取得特定地理座標位置的詳細天氣預報。

### 函數簽名

```python
async def get_forecast(latitude: float, longitude: float) -> str:
    """
    取得特定位置的預報資料
    
    Args:
        latitude (float): 緯度 (-90 到 90)
        longitude (float): 經度 (-180 到 180)
        
    Returns:
        str: 格式化的天氣預報
    """
```

### 參數詳細說明

#### latitude (必需)
- **類型**: `float`
- **範圍**: -90.0 到 90.0
- **格式**: 十進位度數
- **說明**: 正值表示北緯，負值表示南緯
- **範例**: `40.7128` (紐約市)

#### longitude (必需)
- **類型**: `float`
- **範圍**: -180.0 到 180.0
- **格式**: 十進位度數
- **說明**: 正值表示東經，負值表示西經
- **範例**: `-74.0060` (紐約市)

### 主要城市座標參考

| 城市 | 緯度 | 經度 |
|------|------|------|
| 紐約市 | `40.7128` | `-74.0060` |
| 洛杉磯 | `34.0522` | `-118.2437` |
| 芝加哥 | `41.8781` | `-87.6298` |
| 邁阿密 | `25.7617` | `-80.1918` |
| 西雅圖 | `47.6062` | `-122.3321` |
| 丹佛 | `39.7392` | `-104.9903` |
| 亞特蘭大 | `33.7490` | `-84.3880` |
| 波士頓 | `42.3601` | `-71.0589` |

### 回應格式

成功時返回未來 5 個時段的預報：

```
Tonight:
Temperature: 45°F
Wind: 10 mph W
Forecast: Partly cloudy with temperatures falling to around 45 degrees.

---

Friday:
Temperature: 62°F
Wind: 5 mph SW
Forecast: Sunny with high temperatures reaching 62 degrees.

---

Friday Night:
Temperature: 48°F
Wind: 5 mph S
Forecast: Clear skies with overnight lows around 48 degrees.

---

Saturday:
Temperature: 68°F
Wind: 10 mph S
Forecast: Mostly sunny with high temperatures near 68 degrees.

---

Saturday Night:
Temperature: 52°F
Wind: 5 mph SE
Forecast: Partly cloudy with overnight lows around 52 degrees.
```

### 使用範例

#### 基本呼叫

```python
# 查詢紐約市天氣
forecast = await host.call_tool(
    "get_forecast",
    {
        "latitude": 40.7128,
        "longitude": -74.0060
    }
)
print(forecast)
```

#### 批次查詢多個城市

```python
cities = [
    ("紐約", 40.7128, -74.0060),
    ("洛杉磯", 34.0522, -118.2437),
    ("芝加哥", 41.8781, -87.6298)
]

forecasts = {}
for city_name, lat, lon in cities:
    forecast = await host.call_tool(
        "get_forecast",
        {"latitude": lat, "longitude": lon}
    )
    forecasts[city_name] = forecast

for city, forecast in forecasts.items():
    print(f"\n=== {city} 天氣預報 ===")
    print(forecast)
```

#### 座標驗證

```python
def validate_coordinates(lat, lon):
    """驗證座標是否有效"""
    if not (-90 <= lat <= 90):
        raise ValueError(f"緯度 {lat} 超出範圍 [-90, 90]")
    if not (-180 <= lon <= 180):
        raise ValueError(f"經度 {lon} 超出範圍 [-180, 180]")
    return True

# 使用驗證
try:
    validate_coordinates(40.7128, -74.0060)
    forecast = await host.call_tool(
        "get_forecast",
        {"latitude": 40.7128, "longitude": -74.0060}
    )
except ValueError as e:
    print(f"座標錯誤: {e}")
```

### 回應狀態

| 情況 | 回應 |
|------|------|
| 成功 | 格式化的 5 時段預報 |
| 座標超出美國範圍 | `"Unable to fetch forecast data for this location."` |
| API 錯誤 | `"Unable to fetch detailed forecast."` |
| 無效座標 | `"Unable to fetch forecast data for this location."` |

## API 回應格式

### 工具呼叫回應結構

```python
# MCP 工具呼叫回應
{
    "content": [
        {
            "type": "text",
            "text": "實際的天氣資料文字"
        }
    ],
    "isError": false
}
```

### 錯誤回應結構

```python
# 錯誤回應
{
    "content": [
        {
            "type": "text", 
            "text": "錯誤訊息"
        }
    ],
    "isError": true
}
```

### 資料來源格式

工具使用 NOAA API 的 GeoJSON 格式：

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "event": "Tornado Warning",
        "severity": "Extreme",
        "areaDesc": "Broward County",
        "description": "警報詳細描述...",
        "instruction": "安全指示..."
      }
    }
  ]
}
```

## 錯誤代碼和處理

### HTTP 狀態碼（SSE 模式）

| 狀態碼 | 說明 | 原因 |
|--------|------|------|
| `200` | 成功 | 請求正常處理 |
| `400` | 錯誤請求 | 參數格式錯誤 |
| `401` | 未授權 | API 金鑰無效或缺失 |
| `404` | 找不到 | 工具不存在 |
| `429` | 請求限制 | 超出 API 呼叫限制 |
| `500` | 伺服器錯誤 | 內部錯誤 |
| `503` | 服務不可用 | NOAA API 暫時不可用 |

### 認證錯誤處理

SSE 模式支援多種認證方式：

```python
# 1. HTTP Header 認證
headers = {"x-api-key": "your_api_key"}

# 2. Bearer Token 認證  
headers = {"Authorization": "Bearer your_api_key"}

# 3. Query Parameter 認證
url = "http://localhost:8080/sse?api_key=your_api_key"
```

### 錯誤處理最佳實務

```python
import asyncio
from src.client.client import MCPHost

async def robust_weather_query():
    host = MCPHost("servers-config.json")
    
    try:
        await host.connect()
        
        # 重試機制的工具呼叫
        async def call_with_retry(tool_name, args, max_retries=3):
            for attempt in range(max_retries):
                try:
                    return await host.call_tool(tool_name, args)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    print(f"嘗試 {attempt + 1} 失敗，重試中...")
                    await asyncio.sleep(2 ** attempt)  # 指數退避
        
        # 安全的座標驗證
        def safe_coordinates(lat, lon):
            lat = max(-90, min(90, float(lat)))    # 限制緯度範圍
            lon = max(-180, min(180, float(lon)))  # 限制經度範圍
            return lat, lon
        
        # 使用重試和驗證
        lat, lon = safe_coordinates(40.7128, -74.0060)
        forecast = await call_with_retry(
            "get_forecast",
            {"latitude": lat, "longitude": lon}
        )
        
        print("預報結果:", forecast)
        
    except Exception as e:
        print(f"查詢失敗: {e}")
    finally:
        await host.disconnect()

asyncio.run(robust_weather_query())
```

## 資源端點

### weather://logs 資源

```python
@mcp.resource("weather://logs")
async def get_logs() -> str:
    """取得天氣工具的日誌"""
    return "Logs are not available in this version."
```

#### 使用方式

```python
# 透過 MCP 客戶端訪問資源
logs = await client.session.read_resource("weather://logs")
print(logs.contents[0].text)
```

## 使用範例

### 完整的天氣監控應用

```python
import asyncio
import json
from datetime import datetime
from src.client.client import MCPHost, ModelVendor

class WeatherMonitor:
    def __init__(self, config_path: str):
        self.host = MCPHost(config_path)
        self.monitoring = False
    
    async def start_monitoring(self, locations: list, interval: int = 300):
        """開始監控指定位置的天氣
        
        Args:
            locations: 包含 (name, lat, lon) 的位置清單
            interval: 監控間隔（秒）
        """
        await self.host.connect()
        self.monitoring = True
        
        print("🌤️ 天氣監控已啟動")
        
        try:
            while self.monitoring:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n📊 天氣監控報告 - {timestamp}")
                print("=" * 50)
                
                for name, lat, lon in locations:
                    try:
                        # 取得預報
                        forecast = await self.host.call_tool(
                            "get_forecast",
                            {"latitude": lat, "longitude": lon}
                        )
                        
                        # 取得所在州份的警報（假設是美國）
                        state = self._get_state_from_coords(lat, lon)
                        if state:
                            alerts = await self.host.call_tool(
                                "get_alerts",
                                {"state": state}
                            )
                        else:
                            alerts = "不適用（非美國地區）"
                        
                        # 使用 AI 生成摘要
                        summary = await self.host.chat_with_model(
                            ModelVendor.ANTHROPIC,
                            f"請用一段話總結這個天氣預報，突出重點: {forecast[:500]}",
                            max_tokens=200
                        )
                        
                        print(f"\n📍 {name}")
                        print(f"摘要: {summary}")
                        
                        if "No active alerts" not in alerts:
                            print(f"⚠️ 警報: {alerts[:200]}...")
                        else:
                            print("✅ 無現行警報")
                            
                    except Exception as e:
                        print(f"❌ {name} 查詢失敗: {e}")
                
                # 等待下次監控
                print(f"\n⏰ 下次更新: {interval} 秒後")
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n👋 監控已停止")
        finally:
            await self.stop_monitoring()
    
    async def stop_monitoring(self):
        """停止監控"""
        self.monitoring = False
        await self.host.disconnect()
    
    def _get_state_from_coords(self, lat: float, lon: float) -> str:
        """根據座標推測美國州份（簡化版）"""
        # 這裡只是示例，實際應用中需要更精確的地理資料庫
        state_coords = {
            "CA": (36.7783, -119.4179),
            "NY": (42.1657, -74.9481),
            "TX": (31.0545, -97.5635),
            "FL": (27.7663, -82.6404),
        }
        
        min_distance = float('inf')
        closest_state = None
        
        for state, (s_lat, s_lon) in state_coords.items():
            distance = ((lat - s_lat) ** 2 + (lon - s_lon) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_state = state
        
        return closest_state if min_distance < 10 else None

# 使用範例
async def main():
    monitor = WeatherMonitor("servers-config.json")
    
    # 定義監控位置
    locations = [
        ("紐約市", 40.7128, -74.0060),
        ("洛杉磯", 34.0522, -118.2437),
        ("邁阿密", 25.7617, -80.1918),
        ("西雅圖", 47.6062, -122.3321)
    ]
    
    # 開始監控（每 5 分鐘更新一次）
    await monitor.start_monitoring(locations, interval=300)

# 執行監控
if __name__ == "__main__":
    asyncio.run(main())
```

### 天氣比較分析工具

```python
async def weather_comparison_tool():
    """比較多個城市的天氣情況"""
    host = MCPHost("servers-config.json")
    await host.connect()
    
    cities = {
        "東岸": [
            ("紐約", 40.7128, -74.0060),
            ("邁阿密", 25.7617, -80.1918),
            ("波士頓", 42.3601, -71.0589)
        ],
        "西岸": [
            ("洛杉磯", 34.0522, -118.2437),
            ("舊金山", 37.7749, -122.4194),
            ("西雅圖", 47.6062, -122.3321)
        ]
    }
    
    try:
        for region, city_list in cities.items():
            print(f"\n🌎 {region}天氣比較")
            print("=" * 30)
            
            forecasts = {}
            
            # 批次獲取預報
            for city, lat, lon in city_list:
                forecast = await host.call_tool(
                    "get_forecast",
                    {"latitude": lat, "longitude": lon}
                )
                forecasts[city] = forecast
            
            # 使用 AI 進行比較分析
            comparison_prompt = f"""
            請比較以下城市的天氣情況並提供分析：
            {json.dumps(forecasts, indent=2)}
            
            請提供：
            1. 溫度比較
            2. 天氣模式分析
            3. 旅遊建議
            4. 服裝建議
            """
            
            analysis = await host.chat_with_model(
                ModelVendor.CLAUDE,
                comparison_prompt,
                max_tokens=1500
            )
            
            print(analysis)
    
    finally:
        await host.disconnect()

# 執行比較分析
asyncio.run(weather_comparison_tool())
```

這個伺服器 API 參考文件提供了完整的天氣工具使用指南，包括詳細的參數說明、錯誤處理和實際應用範例，幫助開發者充分利用 MCP Weather Sample 的所有功能。