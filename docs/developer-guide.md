# 開發者指南

歡迎來到 MCP Weather Sample 開發者指南！本指南將幫助您設定開發環境、理解程式碼結構，並參與專案開發。

## 目錄

- [本地開發環境設定](#本地開發環境設定)
- [程式碼結構和架構說明](#程式碼結構和架構說明)

## 本地開發環境設定

### 先決條件

確保您的開發環境滿足以下要求：

- **Python 3.12+**: 使用最新的 Python 功能
- **UV**: 推薦的套件管理工具
- **Git**: 版本控制
- **VS Code** (推薦): 開發編輯器

### 開發環境安裝

#### 1. 複製並設定專案

```bash
# 複製專案
git clone <repository-url>
cd mcp-sample

# 檢查專案結構
tree -I "__pycache__|*.pyc|.git"
```

#### 2. 建立開發環境

```bash
# 使用 UV 建立開發環境
uv sync --dev
```

#### 3. 環境變數設定

建立開發用的 `.env` 檔案：

```env
# API 金鑰（使用測試金鑰）
ANTHROPIC_API_KEY=your_dev_anthropic_key
OPENAI_API_KEY=your_dev_openai_key
GOOGLE_API_KEY=your_dev_google_key
```

#### 5. IDE 設定

**VS Code 推薦設定** (`.vscode/settings.json`):

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

**推薦的 VS Code 擴展**:
- Python
- Pylance
- Black Formatter
- isort
- GitLens
- Thunder Client (API 測試)

## 程式碼結構和架構說明

### 專案結構概覽

```
mcp-sample/
├── src/                           # 原始碼目錄
│   ├── client/                    # MCP 客戶端實現
│   │   └── client.py              # 核心客戶端類別
│   └── servers/                   # MCP 伺服器實現
│       └── weather/               # 天氣服務
│           ├── __init__.py
│           ├── sse/               # SSE 傳輸模式
│           │   ├── mcp-weather.py # SSE 伺服器主程式
│           │   └── user_db.py     # 用戶認證模組
│           └── stdio/             # STDIO 傳輸模式
│               └── weather.py     # STDIO 伺服器主程式
├── docs/                          # 文件目錄
├── pyproject.toml                 # 專案配置
├── servers-config.json            # MCP 伺服器配置
└── README.md                      # 專案說明
```

### 核心模組詳解

#### 1. 客戶端模組 (`src/client/client.py`)

**主要類別**:

```python
class MCPClient:
    """單一 MCP 伺服器連接管理"""
    
    def __init__(self, server_name: str, server_config: dict, logging_callback: Optional[callable] = None)
    async def connect_to_local_server(self, server_config: dict)  # STDIO 連接
    async def connect_to_sse_server(self, server_config: dict)    # SSE 連接
    def logging_callback(self, params: LoggingMessageNotificationParams)

class MCPHost:
    """多伺服器管理和 AI 模型整合"""
    
    def __init__(self, config_path: str)
    async def connect(self)                                      # 連接所有伺服器
    async def disconnect(self)                                   # 斷開所有連接
    async def call_tool(self, tool_name: str, arguments: dict)   # 呼叫 MCP 工具
    async def chat_with_model(self, model_vendor: ModelVendor, prompt: str, **kwargs)  # AI 對話

class ModelVendor(Enum):
    """AI 模型供應商枚舉"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
```

#### 2. 伺服器模組架構

**STDIO 伺服器** (`src/servers/weather/stdio/weather.py`):

```python
from mcp.server.fastmcp import FastMCP

# 初始化 FastMCP 伺服器
mcp = FastMCP("Weather")

@mcp.tool()
async def get_alerts(state: str) -> str:
    """取得天氣警報"""
    
@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """取得天氣預報"""
```

**SSE 伺服器** (`src/servers/weather/sse/mcp-weather.py`):

```python
from mcp.server.fastmcp import FastMCP, Context
from fastapi import FastAPI

# FastAPI 應用
app = FastAPI(title="MCP Weather API Server")

# FastMCP 伺服器
mcp = FastMCP(name="weather")

# 認證中介軟體
class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # API 金鑰驗證邏輯
        
@mcp.tool()
async def get_alerts(state: str, ctx: Context) -> str:
    """取得天氣警報（含上下文）"""

@mcp.tool()
async def get_forecast(latitude: float, longitude: float, ctx: Context) -> str:
    """取得天氣預報（含上下文）"""
```

### 架構設計原則

#### 1. 分離關注點
- **客戶端**: 專注於連接管理和 AI 整合
- **伺服器**: 專注於工具實現和資料處理
- **傳輸層**: STDIO 和 SSE 模式分離

#### 2. 異步優先
```python
# 所有 I/O 操作使用 async/await
async def make_nws_request(url: str) -> dict[str, Any] | None:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=30.0)
        return response.json()
```

#### 3. 錯誤處理
```python
try:
    response = await client.get(url, headers=headers, timeout=30.0)
    response.raise_for_status()
    return response.json()
except httpx.HTTPStatusError as e:
    print(f"HTTP error occurred: {e}")
    return None
```

#### 4. 配置驅動
```json
{
  "mcpServers": {
    "server_name": {
      "type": "stdio|sse",
      "disabled": false,
      "allowedTools": ["tool1", "tool2"],
      "notAllowedTools": []
    }
  }
}
```

這個開發者指南提供了完整的開發環境設定、程式碼結構理解和貢獻流程，幫助新開發者快速上手並有效參與專案開發。