# 擴展指南

## 概述

本指南將詳細說明如何擴展 MCP Weather Sample 專案，包括新增 MCP 伺服器、開發自訂工具、整合新的 AI 模型，以及開發外掛程式。透過模組化的設計，您可以輕鬆地擴展系統功能。

## 1. 新增新的 MCP 伺服器

### 1.1 建立伺服器目錄結構

```bash
src/servers/your_service/
├── __init__.py
├── stdio/
│   └── your_service.py      # STDIO 版本
└── sse/
    ├── mcp-your_service.py  # SSE 版本
    └── middleware.py        # 可選的中介軟體
```

### 1.2 實現 STDIO 版本

建立 `src/servers/your_service/stdio/your_service.py`：

```python
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# 初始化 FastMCP 伺服器
mcp = FastMCP("YourService")

@mcp.tool()
async def your_tool(param1: str, param2: int) -> str:
    """
    描述您的工具功能
    
    Args:
        param1: 第一個參數說明
        param2: 第二個參數說明
        
    Returns:
        工具執行結果
    """
    # 實現您的工具邏輯
    result = f"處理 {param1} 和 {param2}"
    return result

@mcp.resource("your_service://logs")
async def get_logs() -> str:
    """獲取服務日誌"""
    return "服務日誌內容"

if __name__ == "__main__":
    # 以 STDIO 模式運行伺服器
    mcp.run(transport='stdio')
```

### 1.3 實現 SSE 版本

建立 `src/servers/your_service/sse/mcp-your_service.py`：

```python
import uvicorn
from mcp.server.fastmcp import FastMCP, Context
from fastapi import FastAPI
from starlette.routing import Mount
from starlette.middleware.base import BaseHTTPMiddleware

# 建立 FastAPI 應用
app = FastAPI(
    title="MCP Your Service API Server",
    description="MCP Server for Your Service Tools",
    version="1.0.0"
)

# 初始化 FastMCP 伺服器
mcp = FastMCP(name="your_service")

# 掛載 MCP SSE 應用
app.router.routes.append(Mount('/', app=mcp.sse_app()))

@mcp.tool()
async def your_tool(param1: str, param2: int, ctx: Context) -> str:
    """
    描述您的工具功能
    
    Args:
        param1: 第一個參數說明
        param2: 第二個參數說明
        ctx: MCP 上下文物件
    """
    await ctx.info(f"執行工具，參數：{param1}, {param2}")
    
    # 實現您的工具邏輯
    result = f"處理 {param1} 和 {param2}"
    return result

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8081, help='Port to listen on')
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)
```

### 1.4 更新配置檔案

在 `servers-config.json` 中新增您的伺服器：

```json
{
  "mcpServers": {
    "your_service_stdio": {
      "type": "stdio",
      "command": "uv",
      "cwd": "src/servers/your_service/stdio",
      "args": ["run", "python", "your_service.py"],
      "disabled": false,
      "allowedTools": ["your_tool"],
      "timeout": 30
    },
    "your_service_sse": {
      "type": "sse",
      "url": "http://localhost:8081/sse",
      "disabled": false,
      "accessToken": "your_access_token",
      "allowedTools": ["your_tool"],
      "timeout": 30
    }
  }
}
```

## 2. 自訂工具開發

### 2.1 工具開發原則

- **單一職責**: 每個工具專注一個特定功能
- **輸入驗證**: 使用類型提示和驗證
- **錯誤處理**: 妥善處理異常情況
- **文件化**: 提供清晰的函數說明

### 2.2 基本工具範例

```python
@mcp.tool()
async def process_data(data: str, format_type: str = "json") -> str:
    """
    處理資料並返回指定格式
    
    Args:
        data: 要處理的資料
        format_type: 輸出格式 (json, xml, csv)
        
    Returns:
        處理後的資料
        
    Raises:
        ValueError: 當格式類型不支援時
    """
    if format_type not in ["json", "xml", "csv"]:
        raise ValueError(f"不支援的格式類型: {format_type}")
    
    # 處理邏輯
    if format_type == "json":
        return f'{{"processed_data": "{data}"}}'
    elif format_type == "xml":
        return f"<data>{data}</data>"
    else:  # csv
        return f"data\n{data}"
```

### 2.3 異步工具範例

```python
@mcp.tool()
async def fetch_external_data(url: str, timeout: int = 30) -> str:
    """
    從外部 API 獲取資料
    
    Args:
        url: API 端點 URL
        timeout: 請求超時時間（秒）
        
    Returns:
        API 回應資料
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except httpx.RequestError as e:
            return f"請求失敗: {str(e)}"
        except httpx.HTTPStatusError as e:
            return f"HTTP 錯誤: {e.response.status_code}"
```

### 2.4 帶上下文的工具（SSE 版本）

```python
@mcp.tool()
async def long_running_task(task_name: str, ctx: Context) -> str:
    """
    執行長時間運行的任務
    
    Args:
        task_name: 任務名稱
        ctx: MCP 上下文，用於日誌記錄
    """
    await ctx.info(f"開始執行任務: {task_name}")
    
    # 模擬長時間運行的任務
    for i in range(5):
        await asyncio.sleep(1)
        await ctx.info(f"任務進度: {(i+1)*20}%")
    
    await ctx.info(f"任務完成: {task_name}")
    return f"任務 {task_name} 執行完成"
```

## 3. 新 AI 模型整合

### 3.1 擴展 ModelVendor 枚舉

在 `src/client/client.py` 中新增新的模型供應商：

```python
class ModelVendor(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    CUSTOM = "custom"  # 新增自訂模型
```

### 3.2 新增模型客戶端初始化

在 `MCPHost.__init__` 方法中新增：

```python
def __init__(self, model_vendor: ModelVendor, config: Optional[dict] = None):
    # 現有程式碼...
    
    # 新增自訂模型客戶端
    if model_vendor == ModelVendor.CUSTOM:
        self.custom_client = CustomModelClient(
            api_key=os.getenv("CUSTOM_API_KEY"),
            base_url=os.getenv("CUSTOM_BASE_URL")
        )
```

### 3.3 實現工具格式轉換

在 `get_available_tools` 方法中新增格式轉換：

```python
elif self.model_vendor == ModelVendor.CUSTOM:
    # 自訂模型的工具格式
    tools = [{
        "name": f"{mcpClient.server_name}#{tool.name}",
        "description": tool.description,
        "parameters": tool.inputSchema,
        "type": "function"
    } for tool in response.tools]
```

### 3.4 實現查詢處理方法

```python
async def process_query_custom(self, query: str) -> str:
    """使用自訂模型處理查詢"""
    messages = [{"role": "user", "content": query}]
    available_tools = await self.get_available_tools()
    
    response = await self.custom_client.generate(
        messages=messages,
        tools=available_tools,
        max_tokens=1000
    )
    
    # 處理工具調用邏輯（類似其他模型的實現）
    # ...
    
    return response.content
```

### 3.5 更新主要處理邏輯

在 `chat_loop` 方法中新增新模型的處理：

```python
match self.model_vendor:
    case ModelVendor.ANTHROPIC:
        response = await self.process_query_anthropic(query)
    case ModelVendor.GOOGLE:
        response = await self.process_query_google(query)
    case ModelVendor.CUSTOM:
        response = await self.process_query_custom(query)
    case _:
        response = await self.process_query_openai(query)
```

## 4. 外掛開發指南

### 4.1 外掛架構設計

```python
# src/plugins/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class MCPPlugin(ABC):
    """MCP 外掛基礎類別"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化外掛"""
        pass
    
    @abstractmethod
    async def get_tools(self) -> List[Dict[str, Any]]:
        """獲取外掛提供的工具"""
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """執行工具調用"""
        pass
    
    async def cleanup(self) -> None:
        """清理資源"""
        pass
```

### 4.2 實現具體外掛

```python
# src/plugins/database_plugin.py
import asyncpg
from .base import MCPPlugin

class DatabasePlugin(MCPPlugin):
    """資料庫操作外掛"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("database", config)
        self.connection = None
    
    async def initialize(self) -> None:
        """建立資料庫連接"""
        self.connection = await asyncpg.connect(
            host=self.config["host"],
            port=self.config["port"],
            user=self.config["user"],
            password=self.config["password"],
            database=self.config["database"]
        )
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """返回資料庫相關工具"""
        return [
            {
                "name": "execute_query",
                "description": "執行 SQL 查詢",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL 查詢語句"},
                        "params": {"type": "array", "description": "查詢參數"}
                    },
                    "required": ["query"]
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """執行工具調用"""
        if tool_name == "execute_query":
            query = args["query"]
            params = args.get("params", [])
            
            try:
                result = await self.connection.fetch(query, *params)
                return [dict(row) for row in result]
            except Exception as e:
                return f"查詢執行失敗: {str(e)}"
        
        raise ValueError(f"未知的工具: {tool_name}")
    
    async def cleanup(self) -> None:
        """關閉資料庫連接"""
        if self.connection:
            await self.connection.close()
```

### 4.3 外掛管理器

```python
# src/plugins/manager.py
from typing import Dict, List
from .base import MCPPlugin

class PluginManager:
    """外掛管理器"""
    
    def __init__(self):
        self.plugins: Dict[str, MCPPlugin] = {}
    
    async def load_plugin(self, plugin: MCPPlugin) -> None:
        """載入外掛"""
        await plugin.initialize()
        self.plugins[plugin.name] = plugin
    
    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """獲取所有外掛的工具"""
        all_tools = []
        for plugin in self.plugins.values():
            tools = await plugin.get_tools()
            for tool in tools:
                tool["plugin"] = plugin.name
                all_tools.append(tool)
        return all_tools
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """調用指定工具"""
        plugin_name = args.pop("plugin", None)
        if plugin_name and plugin_name in self.plugins:
            return await self.plugins[plugin_name].call_tool(tool_name, args)
        
        # 在所有外掛中尋找工具
        for plugin in self.plugins.values():
            tools = await plugin.get_tools()
            if any(tool["name"] == tool_name for tool in tools):
                return await plugin.call_tool(tool_name, args)
        
        raise ValueError(f"未找到工具: {tool_name}")
    
    async def cleanup(self) -> None:
        """清理所有外掛"""
        for plugin in self.plugins.values():
            await plugin.cleanup()
```

## 5. 最佳實務建議

### 5.1 程式碼組織

```
src/
├── servers/           # MCP 伺服器
│   └── service_name/
│       ├── stdio/     # STDIO 實現
│       ├── sse/       # SSE 實現
│       └── common/    # 共用程式碼
├── plugins/           # 外掛系統
│   ├── base.py       # 基礎類別
│   └── specific/     # 具體外掛
└── utils/            # 工具函數
    ├── validation.py # 輸入驗證
    ├── logging.py    # 日誌工具
    └── errors.py     # 自訂例外
```

### 5.2 錯誤處理模式

```python
from typing import Union, Dict, Any

class MCPError(Exception):
    """MCP 相關錯誤的基礎類別"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)

class ToolExecutionError(MCPError):
    """工具執行錯誤"""
    pass

class ValidationError(MCPError):
    """輸入驗證錯誤"""
    pass

def safe_tool_execution(func):
    """工具執行的安全裝飾器"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            return {"error": "validation_error", "message": e.message}
        except ToolExecutionError as e:
            return {"error": "execution_error", "message": e.message}
        except Exception as e:
            return {"error": "unknown_error", "message": str(e)}
    return wrapper
```

### 5.3 輸入驗證

```python
from pydantic import BaseModel, validator
from typing import Optional

class ToolInput(BaseModel):
    """工具輸入的基礎模型"""
    
    @validator('*', pre=True)
    def validate_not_empty(cls, v):
        if isinstance(v, str) and not v.strip():
            raise ValueError('字串不能為空')
        return v

class WeatherToolInput(ToolInput):
    """天氣工具輸入模型"""
    state: str
    include_details: Optional[bool] = False
    
    @validator('state')
    def validate_state_code(cls, v):
        if len(v) != 2 or not v.isalpha():
            raise ValueError('州代碼必須是兩個字母')
        return v.upper()
```

### 5.4 配置管理

```python
# src/config/manager.py
import json
import os
from typing import Dict, Any
from pathlib import Path

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "servers-config.json"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """載入配置檔案"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {"mcpServers": {}}
    
    def save_config(self) -> None:
        """儲存配置檔案"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def add_server(self, name: str, config: Dict[str, Any]) -> None:
        """新增伺服器配置"""
        self.config["mcpServers"][name] = config
        self.save_config()
    
    def remove_server(self, name: str) -> None:
        """移除伺服器配置"""
        if name in self.config["mcpServers"]:
            del self.config["mcpServers"][name]
            self.save_config()
```

### 5.5 測試策略

```python
# tests/test_tools.py
import pytest
from unittest.mock import AsyncMock, patch
from src.servers.weather.stdio.weather import get_forecast

@pytest.mark.asyncio
async def test_get_forecast_success():
    """測試天氣預報工具成功案例"""
    with patch('httpx.AsyncClient.get') as mock_get:
        # 模擬 API 回應
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "properties": {
                "forecast": "http://api.weather.gov/forecast"
            }
        }
        mock_get.return_value = mock_response
        
        result = await get_forecast(40.7128, -74.0060)
        assert "Temperature:" in result

@pytest.mark.asyncio
async def test_get_forecast_api_error():
    """測試 API 錯誤處理"""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.side_effect = httpx.RequestError("Connection failed")
        
        result = await get_forecast(40.7128, -74.0060)
        assert "Unable to fetch" in result
```

### 5.6 文件化標準

```python
def example_tool(param1: str, param2: int, optional_param: bool = False) -> str:
    """
    工具簡短描述（一行）
    
    更詳細的功能說明，包括使用場景和注意事項。
    
    Args:
        param1: 參數1的描述，包括類型和用途
        param2: 參數2的描述，說明取值範圍或限制
        optional_param: 可選參數的描述和預設值說明
        
    Returns:
        返回值的描述，包括格式和可能的內容
        
    Raises:
        ValueError: 當參數無效時拋出
        ConnectionError: 當網路連接失敗時拋出
        
    Examples:
        >>> result = await example_tool("test", 42)
        >>> print(result)
        處理結果: test, 42
        
    Note:
        任何重要的使用注意事項或限制
    """
    pass
```

## 6. 除錯和測試

### 6.1 除錯工具

```python
# src/utils/debug.py
import logging
import json
from typing import Any

def setup_debug_logging():
    """設定除錯日誌"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def log_tool_call(tool_name: str, args: Any, result: Any):
    """記錄工具調用"""
    logger = logging.getLogger("mcp.tools")
    logger.debug(f"Tool: {tool_name}")
    logger.debug(f"Args: {json.dumps(args, indent=2)}")
    logger.debug(f"Result: {json.dumps(result, indent=2)}")

async def debug_mcp_session(session):
    """除錯 MCP 會話"""
    try:
        tools = await session.list_tools()
        print(f"Available tools: {[t.name for t in tools.tools]}")
        
        resources = await session.list_resources()
        print(f"Available resources: {[r.uri for r in resources.resources]}")
        
    except Exception as e:
        print(f"Debug session failed: {e}")
```

### 6.2 整合測試

```python
# tests/integration/test_mcp_integration.py
import pytest
import asyncio
from src.client.client import MCPHost, ModelVendor

@pytest.mark.asyncio
async def test_full_workflow():
    """測試完整的 MCP 工作流程"""
    config = {
        "mcpServers": {
            "test_server": {
                "type": "stdio",
                "command": "python",
                "args": ["test_server.py"],
                "disabled": False
            }
        }
    }
    
    host = MCPHost(ModelVendor.ANTHROPIC, config)
    await host.create_mcp_clients()
    
    try:
        tools = await host.get_available_tools()
        assert len(tools) > 0
        
        # 測試工具調用
        client = await host.get_mcp_client("test_server")
        result = await client.call_tool("test_tool", {"param": "value"})
        assert result is not None
        
    finally:
        await host.cleanup()
```

透過遵循這些指南和最佳實務，您可以有效地擴展 MCP Weather Sample 專案，新增新功能並保持程式碼的品質和可維護性。