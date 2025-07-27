# 快速開始指南

本指南將協助您快速設定並運行 MCP Weather Sample 專案，從零開始體驗 Model Context Protocol 的強大功能。

## 環境需求和先決條件

### 系統需求

- **作業系統**: Windows 10+、macOS 10.15+、或 Linux (Ubuntu 18.04+)
- **Python 版本**: Python 3.12 或更高版本
- **記憶體**: 建議 4GB+ RAM
- **磁碟空間**: 至少 500MB 可用空間

### 必要軟體

1. **Python 3.12+**
   ```bash
   # 檢查 Python 版本
   python --version
   # 或
   python3 --version
   ```

2. **UV 套件管理器**（強烈建議）
   ```bash
   # 安裝 UV
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # 或使用 pip
   pip install uv
   
   # 驗證安裝
   uv --version
   ```

3. **Git**（用於複製專案）
   ```bash
   git --version
   ```

### API 金鑰需求

您需要至少一個 AI 模型的 API 金鑰：

- **Anthropic Claude**: [取得 API 金鑰](https://console.anthropic.com/settings/keys)
- **OpenAI GPT**: [取得 API 金鑰](https://platform.openai.com/api-keys)
- **Google Gemini**: [取得 API 金鑰](https://aistudio.google.com/app/apikey)

## 詳細安裝步驟

### 步驟 1: 複製專案

```bash
# 複製專案倉庫
git clone <repository-url>
cd mcp-sample

# 檢查專案結構
ls -la
```

### 步驟 2: 建立虛擬環境並安裝依賴

#### 使用 UV

```bash
# UV 會自動建立虛擬環境並安裝依賴
uv sync

# 驗證安裝
uv run python --version
```

### 步驟 3: 環境變數配置

1. **建立 .env 檔案**
   ```bash
   # 在專案根目錄中建立 .env 檔案
   touch .env
   ```

2. **添加 API 金鑰**
   
   編輯 `.env` 檔案，添加您的 API 金鑰：
   ```env
   # AI 模型 API 金鑰（至少需要一個）
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here
   ```

### 步驟 4: 伺服器配置

1. **檢查伺服器配置檔案**
   
   檢查 `servers-config.json` 的內容：
   ```bash
   cat servers-config.json
   ```

2. **自訂配置**（可選）
   
   您可以修改配置以符合您的需求：
   ```json
   {
     "mcpServers": {
       "sse_weather": {
         "type": "sse",
         "url": "http://localhost:8080/sse",
         "disabled": false,
         "accessToken": "password123",
         "allowedTools": ["get_alerts", "get_forecast"],
         "notAllowedTools": []
       },
       "stdio_weather": {
         "type": "stdio",
         "command": "uv",
         "cwd": "src/servers/weather/stdio",
         "args": ["run", "python", "weather.py"],
         "disabled": false,
         "allowedTools": ["get_alerts", "get_forecast"],
         "notAllowedTools": []
       }
     }
   }
   ```

## 基本配置說明

### 傳輸模式選擇

專案支援兩種傳輸模式：

#### STDIO 模式（本地）
- **優點**: 設定簡單、無需網路配置、低延遲
- **缺點**: 僅限本地使用、無法遠端存取
- **適用場景**: 開發測試、單機應用

#### SSE 模式（遠端）
- **優點**: 支援遠端存取、可擴展性好、支援認證
- **缺點**: 需要網路配置、稍高延遲
- **適用場景**: 生產環境、多用戶應用

### 工具權限配置

透過 `allowedTools` 和 `notAllowedTools` 控制工具存取權限：

```json
{
  "allowedTools": ["get_alerts", "get_forecast"],    // 明確允許的工具
  "notAllowedTools": ["get_forecast"]               // 明確禁用的工具
}
```

**注意**: `notAllowedTools` 的優先級高於 `allowedTools`。

## 啟動和使用

### 啟動 SSE 伺服器

1. **開啟新終端機並啟動 SSE 伺服器**
   ```bash
   uv run src/servers/weather/sse/mcp-weather.py
   ```
   
   您應該看到類似的輸出：
   ```
   INFO:     Started server process [12345]
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:8080
   ```

### 執行基本天氣查詢

2. **開啟另一個終端機並執行客戶端**
   ```bash
   uv run src/client/client.py
   ```

   您應該看到類似的輸出：
   ```
   Server Name: sse_weather
   Config: {'type': 'sse', 'url': 'http://localhost:8080/sse', 'disabled': False, 'accessToken': 'password123', 'allowedTools': ['get_alerts', 'get_forecast'], 'notAllowedTools': ['get_forecast']}
   ------
   Initialized SSE client...
   Listing tools...

   Connected to server with tools: ['get_alerts', 'get_forecast']
   Server Name: stdio_weather
   Config: {'type': 'stdio', 'command': 'uv', 'cwd': 'src/servers/weather/stdio', 'args': ['run', 'python', 'weather.py'], 'disabled': False, 'allowedTools': ['get_alerts', 'get_forecast'], 'notAllowedTools': ['get_alerts']}
   ------
   [07/27/25 08:22:06] INFO     Processing request of type ListToolsRequest                                                                                                                                                                                      server.py:625

   Connected to server with tools: ['get_alerts', 'get_forecast']

   MCP Client Started!
   Type your queries or 'quit' to exit.

   Query: 
   ```

## 驗證安裝

### 1. 檢查依賴安裝

```bash
# 使用 UV
uv run python -c "import mcp, fastapi, anthropic; print('所有依賴安裝成功')"
```

### 2. 測試 API 連接

```bash
# 測試天氣 API
uv run python -c "
import asyncio
import httpx

async def test_weather_api():
    async with httpx.AsyncClient() as client:
        response = await client.get('https://api.weather.gov/alerts/active?area=NY')
        print(f'天氣 API 狀態: {response.status_code}')
        if response.status_code == 200:
            print('天氣 API 連接成功')

asyncio.run(test_weather_api())
"
```

### 3. 測試 AI 模型連接

```bash
# 測試 Anthropic
uv run python -c "
import os
from anthropic import Anthropic
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
print('Anthropic 客戶端初始化成功')
"
```

## 常見問題排除

### 問題 1: Python 版本不相容

**症狀**: `requires-python = ">=3.12"` 錯誤

**解決方案**:
```bash
# 檢查 Python 版本
python --version

# 如果版本低於 3.12，請升級 Python
# 或使用 pyenv 安裝特定版本
pyenv install 3.12.0
pyenv local 3.12.0
```

### 問題 2: UV 安裝失敗

**症狀**: `uv: command not found`

**解決方案**:
```bash
# 重新安裝 UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv

# 重新載入 shell
source ~/.bashrc  # 或 ~/.zshrc
```

### 問題 3: 依賴安裝錯誤

**症狀**: 套件安裝失敗或版本衝突

**解決方案**:
```bash
# 清除快取並重新安裝
uv cache clean
uv sync --reinstall

# 或使用 pip
pip cache purge
pip install --force-reinstall -r requirements.txt
```

### 問題 4: API 金鑰無效

**症狀**: `401 Unauthorized` 或 API 金鑰錯誤

**解決方案**:
1. 檢查 `.env` 檔案是否正確設定
2. 驗證 API 金鑰是否有效
3. 確認 API 金鑰有適當的權限

```bash
# 檢查環境變數是否載入
uv run python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('ANTHROPIC_API_KEY:', 'HIDDEN' if os.getenv('ANTHROPIC_API_KEY') else 'NOT SET')
"
```

### 問題 5: 連接埠衝突

**症狀**: `Address already in use` 錯誤

**解決方案**:
```bash
# 查找使用 8080 連接埠的程序
lsof -i :8080

# 終止程序或使用不同連接埠
# 修改 mcp-weather.py 中的 port 參數
```


## 下一步

現在您已經成功安裝並運行了 MCP Weather Sample！接下來您可以：

1. **探索更多功能**: 閱讀 [使用者指南](user-guide.md) 了解進階用法
2. **學習開發**: 查看 [開發者指南](developer-guide.md) 學習如何擴展專案
3. **瞭解架構**: 閱讀 [架構文件](architecture.md) 深入理解系統設計

**恭喜！** 🎉 您已經成功設定了您的 MCP 開發環境，準備好探索 Model Context Protocol 的無限可能了！