# 專案檔案結構分析

## 檔案結構樹狀圖

```
mcp-sample/
├── LICENSE                              # 開源授權文件 (MIT授權)
├── pyproject.toml                       # Python專案配置文件 (依賴、元數據)
├── servers-config.json                  # MCP伺服器配置文件 (伺服器連接設定)
├── uv.lock                             # UV套件管理器鎖定文件 (確保依賴版本一致性)
├── docs/                               # 文件目錄
│   └── planner/                        # 文件規劃目錄
│       ├── technology-stack.md         # 技術堆疊分析文件
│       ├── file-structure.md           # 檔案結構分析文件 (本文件)
│       └── tasks.md                    # 任務分解規劃文件
└── src/                                # 原始碼目錄
    ├── client/                         # MCP客戶端實現
    │   └── client.py                   # 主要客戶端類別和邏輯
    └── servers/                        # MCP伺服器實現
        └── weather/                    # 天氣服務伺服器
            ├── __init__.py             # Python套件初始化文件
            ├── sse/                    # SSE傳輸模式實現
            │   ├── mcp-weather.py      # SSE天氣伺服器主程式
            │   └── user_db.py          # 用戶驗證和API金鑰管理
            └── stdio/                  # STDIO傳輸模式實現
                └── weather.py          # STDIO天氣伺服器主程式
```

## 檔案和目錄詳細說明

### 根目錄檔案

#### LICENSE
- **類型**: 授權文件
- **功能**: 定義專案的開源授權條款
- **內容**: MIT授權，允許自由使用、修改和分發

#### pyproject.toml
- **類型**: Python專案配置文件
- **功能**: 定義專案元數據、依賴關係和建置配置
- **主要內容**:
  - 專案名稱和版本資訊
  - Python版本需求 (>=3.12)
  - 核心依賴清單（MCP、AI模型、Web框架等）

#### servers-config.json
- **類型**: MCP伺服器配置文件
- **功能**: 配置多個MCP伺服器的連接參數
- **主要內容**:
  - SSE天氣伺服器配置 (HTTP連接、API金鑰)
  - STDIO天氣伺服器配置 (本地執行命令)
  - 工具權限設定 (允許/禁用的工具清單)

#### uv.lock
- **類型**: 依賴鎖定文件
- **功能**: 確保所有環境中使用相同的依賴版本
- **內容**: 詳細的套件版本和雜湊值

### 原始碼目錄 (src/)

#### client/client.py
- **類型**: MCP客戶端實現
- **功能**: MCP客戶端主要邏輯和API整合
- **主要類別**:
  - `MCPClient`: 單一MCP伺服器連接管理
  - `MCPHost`: 多伺服器管理和AI模型整合
  - `ModelVendor`: AI模型供應商枚舉
- **核心功能**:
  - STDIO和SSE傳輸模式支援
  - 多AI模型整合 (Anthropic、OpenAI、Google)
  - 工具呼叫和對話管理
  - 異步操作和錯誤處理

#### servers/weather/
天氣服務伺服器的實現，提供兩種傳輸模式：

##### sse/mcp-weather.py
- **類型**: SSE模式天氣伺服器
- **功能**: 透過HTTP SSE提供天氣服務
- **主要特點**:
  - FastAPI和FastMCP整合
  - API金鑰驗證中介軟體
  - NOAA Weather API整合
- **提供工具**:
  - `get_alerts`: 獲取美國州份天氣警報
  - `get_forecast`: 獲取指定座標的天氣預報

##### sse/user_db.py
- **類型**: 用戶驗證模組
- **功能**: 管理API金鑰和用戶資訊
- **主要功能**:
  - 記憶體用戶資料庫
  - API金鑰驗證
  - 用戶角色管理

##### stdio/weather.py
- **類型**: STDIO模式天氣伺服器
- **功能**: 透過標準輸入輸出提供天氣服務
- **主要特點**:
  - 純MCP STDIO實現
  - 相同的天氣API整合
  - 無需額外認證機制

##### __init__.py
- **類型**: Python套件初始化
- **功能**: 將weather目錄標記為Python套件

### 文件目錄 (docs/)

#### planner/
文件規劃專用目錄，包含：
- **technology-stack.md**: 技術堆疊分析
- **file-structure.md**: 檔案結構分析 (本文件)
- **tasks.md**: 任務分解和文件規劃

## 架構設計原則

### 模組化設計
- **客戶端與伺服器分離**: client/ 和 servers/ 目錄明確分工
- **傳輸模式分離**: stdio/ 和 sse/ 實現不同的傳輸協定
- **功能專業化**: 每個模組專注特定功能

### 配置驅動
- **外部配置**: 使用JSON配置文件管理伺服器設定
- **環境分離**: 透過.env文件管理敏感資訊
- **彈性部署**: 支援多種部署模式

### 異步架構
- **全異步設計**: 所有I/O操作使用asyncio
- **高效能**: 支援並發處理多個請求
- **現代Python**: 充分利用Python 3.12+的異步特性