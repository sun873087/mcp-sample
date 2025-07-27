# 技術堆疊分析

## 主要程式語言和版本
- **Python 3.12+**: 專案主要開發語言，使用現代Python功能
- **支援版本**: >=3.12（基於 pyproject.toml 的 requires-python 設定）

## 核心框架和函式庫

### MCP（Model Context Protocol）相關
- **mcp >=1.12.2**: 核心MCP框架，用於實現客戶端與伺服器通訊
- **FastMCP**: 基於FastAPI的MCP伺服器實現框架

### Web框架
- **FastAPI >=0.116.1**: 現代Python web框架，用於SSE伺服器實現
- **Uvicorn**: ASGI伺服器，用於運行FastAPI應用
- **Starlette**: FastAPI的底層框架，提供中介軟體支援

### AI模型整合
- **Anthropic >=0.59.0**: Claude AI模型整合
- **OpenAI >=1.97.1**: GPT模型整合
- **Google GenAI >=1.27.0**: Google Gemini模型整合

### HTTP客戶端和網路
- **httpx >=0.28.1**: 現代異步HTTP客戶端
- **支援異步操作**: 所有網路請求都使用異步模式

### 資料處理和驗證
- **jsonschema >=4.25.0**: JSON Schema驗證
- **Pydantic**: 資料驗證和序列化（FastAPI依賴）

### 環境和配置
- **python-dotenv >=1.1.1**: 環境變數管理
- **JSON配置**: 使用servers-config.json進行伺服器配置

### 圖像處理
- **Pillow >=11.3.0**: Python圖像處理函式庫

## 開發工具和建置系統

### 套件管理
- **UV**: 現代Python套件管理器，用於依賴管理和虛擬環境
- **pyproject.toml**: 現代Python專案配置格式

### 版本控制
- **Git**: 版本控制系統
- **MIT License**: 開源授權

## 資料庫和儲存解決方案
- **記憶體儲存**: 使用Python字典進行用戶和API金鑰管理
- **無外部資料庫依賴**: 當前實現不依賴外部資料庫

## 部署和基礎設施工具

### 傳輸協定
- **STDIO**: 標準輸入輸出傳輸，用於本地MCP伺服器
- **SSE (Server-Sent Events)**: 伺服器推送事件，用於遠端MCP伺服器

### API整合
- **NOAA Weather API**: 美國國家氣象局API整合
- **RESTful API設計**: 遵循REST原則的API設計

## 版本相容性資訊

### Python版本需求
- **最低版本**: Python 3.12
- **建議版本**: Python 3.12或更高版本

### 主要依賴版本約束
- MCP框架: >=1.12.2
- FastAPI: >=0.116.1
- Anthropic: >=0.59.0
- OpenAI: >=1.97.1
- Google GenAI: >=1.27.0
- httpx: >=0.28.1

### 架構特點
- **異步程式設計**: 全面使用Python asyncio
- **多模型支援**: 支援Anthropic、OpenAI和Google AI模型
- **雙傳輸模式**: 支援STDIO和SSE兩種傳輸方式
- **中介軟體架構**: 使用Starlette中介軟體進行API金鑰驗證
- **工具導向設計**: 基於工具呼叫的AI互動模式