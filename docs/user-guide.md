# 使用者指南

本指南詳細說明如何使用 MCP Weather Sample 的各項功能，從基本天氣查詢到進階配置選項。

## 目錄

- [MCP 客戶端使用說明](#mcp-客戶端使用說明)
- [配置文件詳細說明](#配置文件詳細說明)
- [支援的 AI 模型和設定](#支援的-ai-模型和設定)
- [工具使用範例](#工具使用範例)
- [高級配置選項](#高級配置選項)

## MCP 客戶端使用說明

### 基本客戶端操作

MCP Weather Sample 提供兩個主要的客戶端類別：

#### MCPClient - 單一伺服器管理

`MCPClient` 用於管理與單一 MCP 伺服器的連接：

```python
from src.client.client import MCPClient
import asyncio

async def use_single_server():
    # STDIO 模式配置
    stdio_config = {
        "type": "stdio",
        "command": "uv",
        "args": ["run", "python", "weather.py"],
        "cwd": "src/servers/weather/stdio"
    }
    
    # 建立客戶端
    client = MCPClient("weather_stdio", stdio_config)
    
    # 連接到伺服器
    await client.connect_to_local_server(stdio_config)
    
    # 列出可用工具
    tools_response = await client.list_tools()
    tools = [tool.name for tool in tools_response.tools]
    print(f"可用工具: {tools}")
    
    # 呼叫工具
    result = await client.call_tool(
        "get_alerts",
        arguments={"state": "NY"}
    )
    print(f"紐約州天氣警報: {result.content}")
    
    # 關閉連接
    await client.cleanup()

# 執行
asyncio.run(use_single_server())
```

### 連接模式比較

| 特性 | STDIO 模式 | SSE 模式 |
|------|------------|----------|
| 設定複雜度 | 簡單 | 中等 |
| 網路需求 | 無 | HTTP |
| 認證機制 | 無 | API 金鑰 |
| 遠端存取 | 不支援 | 支援 |
| 效能 | 高（本地） | 中等（網路） |
| 擴展性 | 低 | 高 |
| 適用場景 | 開發測試 | 生產環境 |

## 配置文件詳細說明

### servers-config.json 完整參數

```json
{
  "mcpServers": {
    "server_name": {
      // 基本設定
      "type": "stdio|sse",           // 傳輸類型
      "disabled": false,             // 是否停用此伺服器
      "timeout": 30,                 // 建立連線連接超時（秒），SSE讀取超時時間，默認為建立連線超時的10倍
      
      // STDIO 特定設定
      "command": "uv",               // 執行命令
      "args": ["run", "python", "weather.py"],  // 命令參數
      "cwd": "src/servers/weather/stdio",       // 工作目錄
      "env": {},                     // 環境變數
      "encoding": "utf-8",           // 字元編碼
      
      // SSE 特定設定
      "url": "http://localhost:8080/sse",       // 伺服器 URL
      "accessToken": "your_token",              // 存取權杖
      
      // 工具權限控制
      "allowedTools": ["get_alerts", "get_forecast"],    // 允許的工具
      "notAllowedTools": ["get_forecast"],               // 禁用的工具
    }
  }
}
```

### 環境變數配置

在 `.env` 檔案中設定：

```env
# AI 模型 API 金鑰
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-openai-key-here
GOOGLE_API_KEY=your-google-ai-key-here
```

### 工具權限配置

工具權限透過 `allowedTools` 和 `notAllowedTools` 控制：

```json
{
  "mcpServers": {
    "restricted_weather": {
      "type": "sse",
      "url": "http://localhost:8080/sse",
      
      // 情境 1: 僅允許特定工具（ 只包含 allowed tools ）
      "allowedTools": ["get_alerts"],        // 僅允許查詢警報
      
      // 情境 2: 允許所有工具並排除特定工具（ allowed tools - not allowed tools 互斥）
      "allowedTools": ["get_alerts", "get_forecast"],
      "notAllowedTools": ["get_forecast"],   // 禁用預報功能

      // 情境 3: 排除特定工具（all tools - not allowed tools）
      "notAllowedTools": ["get_forecast"]

      // 情境 4: 允許所有工具（預設行為），allowedTools 和 notAllowedTools 都不設定 或為空
      "allowedTools": [],
      "notAllowedTools": []
    }
  }
}
```

**優先級規則**:
1. `notAllowedTools` 優先級最高
2. 如果工具在 `notAllowedTools` 中，即使在 `allowedTools` 中也會被禁用
3. 空的 `allowedTools` 表示允許所有工具


## 高級配置選項

### 自訂日誌配置

```python
import logging
from src.client.client import MCPClient

# 設定自訂日誌回調
def custom_logging_callback(params):
    logger = logging.getLogger("mcp_client")
    logger.info(f"MCP 日誌: {params.level} - {params.message}")

# 使用自訂日誌的客戶端
client = MCPClient(
    "weather_server",
    server_config,
    logging_callback=custom_logging_callback
)
```

這個使用者指南涵蓋了 MCP Weather Sample 的主要使用方式，從基本操作到進階配置。透過這些範例和說明，使用者可以充分利用專案的所有功能。