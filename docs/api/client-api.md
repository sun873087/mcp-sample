# 客戶端 API 參考

本文件提供 MCP Weather Sample 客戶端 API 的完整參考，包括所有類別、方法和使用範例。

## 目錄

- [MCPClient 類別](#mcpclient-類別)
- [MCPHost 類別](#mcphost-類別)
- [ModelVendor 枚舉](#modelvendor-枚舉)
- [錯誤處理](#錯誤處理)
- [使用範例](#使用範例)

## MCPClient 類別

`MCPClient` 是用於管理單一 MCP 伺服器連接的核心類別。

### 類別定義

```python
class MCPClient:
    """MCPClient類，用於連接和管理MCP伺服器"""
    
    def __init__(
        self, 
        server_name: str, 
        server_config: dict, 
        logging_callback: Optional[callable] = None
    ):
        """初始化MCPClient"""
```

### 建構函式參數

| 參數 | 類型 | 必需 | 說明 |
|------|------|------|------|
| `server_name` | `str` | 是 | 伺服器識別名稱 |
| `server_config` | `dict` | 是 | 伺服器配置字典 |
| `logging_callback` | `callable` | 否 | 自訂日誌回調函數 |

### 屬性

| 屬性 | 類型 | 說明 |
|------|------|------|
| `server_name` | `str` | 伺服器名稱 |
| `disabled` | `bool` | 是否禁用此伺服器 |
| `allowedTools` | `list` | 允許使用的工具清單 |
| `notAllowedTools` | `list` | 禁用的工具清單 |
| `timeout` | `int` | 連接超時時間（秒） |
| `session` | `ClientSession` | MCP 客戶端會話 |
| `exit_stack` | `AsyncExitStack` | 異步上下文管理器 |

### 方法

#### connect_to_local_server()

連接到本地 STDIO MCP 伺服器。

```python
async def connect_to_local_server(self, server_config: dict) -> None:
    """連接至MCP伺服器
    
    Args:
        server_config: 伺服器配置字典
        
    Raises:
        ConnectionError: 連接失敗時拋出
        TimeoutError: 連接超時時拋出
    """
```

**配置參數**:
```python
server_config = {
    "command": "uv",                          # 執行命令
    "args": ["run", "python", "weather.py"], # 命令參數
    "cwd": "src/servers/weather/stdio",      # 工作目錄
    "env": {},                               # 環境變數
    "encoding": "utf-8",                     # 字元編碼
    "encoding_error_handler": "strict"       # 編碼錯誤處理
}
```

**使用範例**:
```python
client = MCPClient("weather", config)
await client.connect_to_local_server(config)
```

#### connect_to_sse_server()

連接到遠端 SSE MCP 伺服器。

```python
async def connect_to_sse_server(self, server_config: dict) -> None:
    """連接至SSE伺服器
    
    Args:
        server_config: 伺服器配置字典
        
    Raises:
        ConnectionError: 連接失敗時拋出
        AuthenticationError: 認證失敗時拋出
        TimeoutError: 連接超時時拋出
    """
```

**配置參數**:
```python
server_config = {
    "url": "http://localhost:8080/sse",    # 伺服器 URL
    "accessToken": "password123",          # 存取權杖
    "timeout": 30,                         # 超時時間
    "headers": {}                          # 額外 HTTP 標頭
}
```

**使用範例**:
```python
client = MCPClient("sse_weather", config)
await client.connect_to_sse_server(config)
```

#### logging_callback()

處理 MCP 日誌訊息的回調函數。

```python
def logging_callback(self, params: LoggingMessageNotificationParams) -> None:
    """處理日誌訊息
    
    Args:
        params: 日誌訊息參數
    """
```

#### 完整使用範例

```python
import asyncio
from src.client.client import MCPClient

async def example_usage():
    # STDIO 模式範例
    stdio_config = {
        "type": "stdio",
        "command": "uv",
        "args": ["run", "python", "weather.py"],
        "cwd": "src/servers/weather/stdio"
    }
    
    client = MCPClient("weather_stdio", stdio_config)
    
    try:
        # 連接到伺服器
        await client.connect_to_local_server(stdio_config)
        
        # 列出可用工具
        tools_response = await client.session.list_tools()
        print("可用工具:", [tool.name for tool in tools_response.tools])
        
        # 呼叫工具
        result = await client.session.call_tool(
            "get_alerts",
            arguments={"state": "NY"}
        )
        print("結果:", result.content)
        
    finally:
        # 清理資源
        await client.exit_stack.aclose()

asyncio.run(example_usage())
```

## MCPHost 類別

`MCPHost` 提供高層次的介面，管理多個 MCP 伺服器並整合 AI 模型。

### 類別定義

```python
class MCPHost:
    """管理多個MCP伺服器並提供AI模型整合的主機類別"""
    
    def __init__(self, config_path: str):
        """初始化MCPHost
        
        Args:
            config_path: servers-config.json 配置檔案路徑
        """
```

### 屬性

| 屬性 | 類型 | 說明 |
|------|------|------|
| `config_path` | `str` | 配置檔案路徑 |
| `config` | `dict` | 解析後的配置資料 |
| `clients` | `dict` | MCP 客戶端字典 |
| `anthropic_client` | `Anthropic` | Anthropic 客戶端 |
| `openai_client` | `OpenAI` | OpenAI 客戶端 |
| `google_client` | `genai.Client` | Google AI 客戶端 |

### 方法

#### connect()

連接到所有已啟用的 MCP 伺服器。

```python
async def connect(self) -> None:
    """連接到所有伺服器
    
    Raises:
        FileNotFoundError: 配置檔案不存在
        JSONDecodeError: 配置檔案格式錯誤
        ConnectionError: 任一伺服器連接失敗
    """
```

**使用範例**:
```python
host = MCPHost("servers-config.json")
await host.connect()
print(f"已連接伺服器: {list(host.clients.keys())}")
```

#### disconnect()

斷開所有 MCP 伺服器連接。

```python
async def disconnect(self) -> None:
    """斷開所有伺服器連接"""
```

#### call_tool()

呼叫指定的 MCP 工具。

```python
async def call_tool(self, tool_name: str, arguments: dict) -> Any:
    """呼叫MCP工具
    
    Args:
        tool_name: 工具名稱
        arguments: 工具參數
        
    Returns:
        工具執行結果
        
    Raises:
        ToolNotFoundError: 工具不存在
        PermissionError: 工具被禁用
        ValueError: 參數無效
    """
```

**使用範例**:
```python
# 取得天氣警報
result = await host.call_tool(
    "get_alerts", 
    {"state": "CA"}
)

# 取得天氣預報
forecast = await host.call_tool(
    "get_forecast",
    {"latitude": 37.7749, "longitude": -122.4194}
)
```

#### chat_with_model()

與指定的 AI 模型進行對話。

```python
async def chat_with_model(
    self,
    model_vendor: ModelVendor,
    prompt: str,
    **kwargs
) -> str:
    """與AI模型對話
    
    Args:
        model_vendor: AI模型供應商
        prompt: 對話提示
        **kwargs: 模型特定參數
        
    Returns:
        AI模型回應
        
    Raises:
        ModelNotAvailableError: 模型不可用
        AuthenticationError: API金鑰無效
        RateLimitError: 請求限制
    """
```

**模型特定參數**:

**Anthropic Claude**:
```python
response = await host.chat_with_model(
    ModelVendor.ANTHROPIC,
    "分析天氣資料",
    max_tokens=1000,
    temperature=0.7,
    model="claude-3-sonnet-20240229"
)
```

**OpenAI GPT**:
```python
response = await host.chat_with_model(
    ModelVendor.OPENAI,
    "總結天氣趨勢",
    max_tokens=800,
    temperature=0.5,
    model="gpt-4"
)
```

**Google Gemini**:
```python
response = await host.chat_with_model(
    ModelVendor.GOOGLE,
    "預測天氣變化",
    max_output_tokens=600,
    temperature=0.3,
    model="gemini-pro"
)
```

#### 完整使用範例

```python
import asyncio
from src.client.client import MCPHost, ModelVendor

async def comprehensive_example():
    host = MCPHost("servers-config.json")
    
    try:
        # 連接所有伺服器
        await host.connect()
        
        # 取得天氣資料
        alerts = await host.call_tool("get_alerts", {"state": "FL"})
        forecast = await host.call_tool(
            "get_forecast", 
            {"latitude": 25.7617, "longitude": -80.1918}
        )
        
        # 使用不同AI模型分析
        claude_analysis = await host.chat_with_model(
            ModelVendor.ANTHROPIC,
            f"分析佛羅里達州的天氣警報和預報: 警報: {alerts}, 預報: {forecast}",
            max_tokens=1500,
            temperature=0.6
        )
        
        gpt_summary = await host.chat_with_model(
            ModelVendor.OPENAI,
            f"總結這些天氣資料並提供旅遊建議: {alerts}, {forecast}",
            max_tokens=800,
            temperature=0.4
        )
        
        print("Claude 分析:", claude_analysis)
        print("\nGPT 總結:", gpt_summary)
        
    finally:
        await host.disconnect()

asyncio.run(comprehensive_example())
```

## ModelVendor 枚舉

定義支援的 AI 模型供應商。

```python
class ModelVendor(Enum):
    """AI模型供應商枚舉"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
```

### 使用方式

```python
from src.client.client import ModelVendor

# 使用枚舉值
vendor = ModelVendor.ANTHROPIC
print(vendor.value)  # "anthropic"

# 在函數中使用
await host.chat_with_model(ModelVendor.OPENAI, "你好")
```

## 錯誤處理

### 常見異常類型

#### 連接相關錯誤

```python
try:
    await client.connect_to_sse_server(config)
except ConnectionError as e:
    print(f"連接失敗: {e}")
except TimeoutError as e:
    print(f"連接超時: {e}")
except AuthenticationError as e:
    print(f"認證失敗: {e}")
```

#### 工具呼叫錯誤

```python
try:
    result = await host.call_tool("get_alerts", {"state": "INVALID"})
except ToolNotFoundError as e:
    print(f"工具不存在: {e}")
except PermissionError as e:
    print(f"權限不足: {e}")
except ValueError as e:
    print(f"參數錯誤: {e}")
```

#### AI 模型錯誤

```python
try:
    response = await host.chat_with_model(ModelVendor.ANTHROPIC, prompt)
except ModelNotAvailableError as e:
    print(f"模型不可用: {e}")
except RateLimitError as e:
    print(f"請求限制: {e}")
except AuthenticationError as e:
    print(f"API金鑰無效: {e}")
```

### 錯誤處理最佳實務

```python
import asyncio
import logging
from src.client.client import MCPHost, ModelVendor

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def robust_client():
    host = MCPHost("servers-config.json")
    
    try:
        # 連接階段錯誤處理
        await host.connect()
        logger.info("成功連接到所有伺服器")
        
    except FileNotFoundError:
        logger.error("配置檔案不存在")
        return
    except ConnectionError as e:
        logger.error(f"伺服器連接失敗: {e}")
        return
    
    try:
        # 工具呼叫錯誤處理
        async def safe_tool_call(tool_name, args):
            try:
                return await host.call_tool(tool_name, args)
            except Exception as e:
                logger.warning(f"工具 {tool_name} 呼叫失敗: {e}")
                return None
        
        # AI 模型呼叫錯誤處理
        async def safe_ai_call(model, prompt, **kwargs):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    return await host.chat_with_model(model, prompt, **kwargs)
                except RateLimitError:
                    wait_time = 2 ** attempt  # 指數退避
                    logger.warning(f"請求限制，等待 {wait_time} 秒後重試...")
                    await asyncio.sleep(wait_time)
                except Exception as e:
                    logger.error(f"AI 模型呼叫失敗 (嘗試 {attempt + 1}): {e}")
                    if attempt == max_retries - 1:
                        return "抱歉，AI 服務暫時不可用。"
        
        # 使用安全的呼叫包裝器
        alerts = await safe_tool_call("get_alerts", {"state": "NY"})
        if alerts:
            analysis = await safe_ai_call(
                ModelVendor.ANTHROPIC,
                f"分析天氣警報: {alerts}",
                max_tokens=800
            )
            print("分析結果:", analysis)
    
    finally:
        # 確保資源清理
        try:
            await host.disconnect()
            logger.info("已斷開所有連接")
        except Exception as e:
            logger.error(f"斷開連接時發生錯誤: {e}")

# 執行
asyncio.run(robust_client())
```

## 使用範例

### 基本範例：單一伺服器連接

```python
import asyncio
from src.client.client import MCPClient

async def basic_example():
    config = {
        "type": "stdio",
        "command": "uv",
        "args": ["run", "python", "weather.py"],
        "cwd": "src/servers/weather/stdio"
    }
    
    client = MCPClient("weather", config)
    
    try:
        await client.connect_to_local_server(config)
        
        # 呼叫工具
        result = await client.session.call_tool(
            "get_forecast",
            arguments={"latitude": 40.7128, "longitude": -74.0060}
        )
        
        print("紐約天氣預報:", result.content)
        
    finally:
        await client.exit_stack.aclose()

asyncio.run(basic_example())
```

### 進階範例：多伺服器多模型整合

```python
import asyncio
from src.client.client import MCPHost, ModelVendor

async def advanced_example():
    host = MCPHost("servers-config.json")
    
    try:
        await host.connect()
        
        # 並行取得多個地區的天氣資料
        tasks = [
            host.call_tool("get_alerts", {"state": "CA"}),
            host.call_tool("get_alerts", {"state": "TX"}),
            host.call_tool("get_forecast", {"latitude": 34.0522, "longitude": -118.2437})
        ]
        
        ca_alerts, tx_alerts, la_forecast = await asyncio.gather(*tasks)
        
        # 使用不同模型進行分析
        analyses = await asyncio.gather(
            host.chat_with_model(
                ModelVendor.ANTHROPIC,
                f"分析加州天氣警報: {ca_alerts}",
                max_tokens=800
            ),
            host.chat_with_model(
                ModelVendor.OPENAI,
                f"總結德州天氣情況: {tx_alerts}",
                max_tokens=600
            ),
            host.chat_with_model(
                ModelVendor.GOOGLE,
                f"洛杉磯天氣預報解讀: {la_forecast}",
                max_output_tokens=700
            )
        )
        
        claude_analysis, gpt_summary, gemini_forecast = analyses
        
        print("=== 天氣分析報告 ===")
        print("\nClaude - 加州警報分析:")
        print(claude_analysis)
        print("\nGPT - 德州天氣總結:")
        print(gpt_summary)
        print("\nGemini - 洛杉磯預報:")
        print(gemini_forecast)
        
    finally:
        await host.disconnect()

asyncio.run(advanced_example())
```

### 即時監控範例

```python
import asyncio
from src.client.client import MCPHost, ModelVendor

async def monitoring_example():
    host = MCPHost("servers-config.json")
    await host.connect()
    
    states_to_monitor = ["CA", "TX", "FL", "NY"]
    
    try:
        while True:
            print("\n=== 天氣監控報告 ===")
            print(f"時間: {asyncio.get_event_loop().time()}")
            
            for state in states_to_monitor:
                try:
                    alerts = await host.call_tool("get_alerts", {"state": state})
                    
                    if alerts and alerts.get("features"):
                        print(f"\n⚠️ {state} 州有天氣警報:")
                        
                        # 使用 AI 快速摘要警報
                        summary = await host.chat_with_model(
                            ModelVendor.OPENAI,
                            f"用一句話總結這個天氣警報: {alerts}",
                            max_tokens=100,
                            temperature=0.3
                        )
                        print(f"摘要: {summary}")
                    else:
                        print(f"✅ {state} 州目前無天氣警報")
                        
                except Exception as e:
                    print(f"❌ {state} 州查詢失敗: {e}")
            
            # 每10分鐘檢查一次
            await asyncio.sleep(600)
            
    except KeyboardInterrupt:
        print("\n監控已停止")
    finally:
        await host.disconnect()

# 執行監控（使用 Ctrl+C 停止）
asyncio.run(monitoring_example())
```

這個 API 參考文件提供了 MCP Weather Sample 客戶端的完整使用指南，包括所有類別、方法和實際使用範例，幫助開發者快速上手並有效使用這個框架。