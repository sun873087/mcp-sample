# 配置參考

本文件提供 MCP Weather Sample 的完整配置參考，涵蓋所有配置選項、最佳實務和進階設定。

## 目錄

- [servers-config.json 完整參數說明](#servers-configjson-完整參數說明)
- [環境變數配置](#環境變數配置)
- [傳輸模式對比](#傳輸模式對比)
- [安全性配置建議](#安全性配置建議)
- [效能調優參數](#效能調優參數)
- [配置範例](#配置範例)
- [故障排除](#故障排除)

## servers-config.json 完整參數說明

`servers-config.json` 是 MCP Weather Sample 的核心配置文件，定義了所有 MCP 伺服器的連接和行為設定。

### 基本結構

```json
{
  "mcpServers": {
    "server_identifier": {
      // 伺服器配置參數
    }
  }
}
```

### 通用參數

所有伺服器類型都支援的基本參數：

| 參數 | 類型 | 必需 | 預設值 | 說明 |
|------|------|------|--------|------|
| `type` | `string` | 是 | - | 傳輸類型：`"stdio"` 或 `"sse"` |
| `disabled` | `boolean` | 否 | `false` | 是否停用此伺服器 |
| `timeout` | `number` | 否 | `30` | 連接超時時間（秒） |
| `allowedTools` | `array` | 否 | `[]` | 允許使用的工具清單 |
| `notAllowedTools` | `array` | 否 | `[]` | 禁用的工具清單 |
| `retryAttempts` | `number` | 否 | `3` | 重試次數 |
| `retryDelay` | `number` | 否 | `1000` | 重試延遲（毫秒） |
| `keepAlive` | `boolean` | 否 | `true` | 是否保持連線 |

### STDIO 特定參數

用於本地標準輸入輸出模式的參數：

| 參數 | 類型 | 必需 | 預設值 | 說明 |
|------|------|------|--------|------|
| `command` | `string` | 是 | - | 執行命令（如 `"uv"`, `"python"`, `"node"`) |
| `args` | `array` | 是 | - | 命令行參數 |
| `cwd` | `string` | 否 | `"."` | 工作目錄 |
| `env` | `object` | 否 | `{}` | 環境變數 |
| `encoding` | `string` | 否 | `"utf-8"` | 字元編碼 |
| `encoding_error_handler` | `string` | 否 | `"strict"` | 編碼錯誤處理方式 |

**STDIO 配置範例**：

```json
{
  "mcpServers": {
    "stdio_weather": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "weather.py"],
      "cwd": "src/servers/weather/stdio",
      "disabled": false,
      "timeout": 30,
      "env": {
        "DEBUG": "false",
        "LOG_LEVEL": "INFO"
      },
      "encoding": "utf-8",
      "allowedTools": ["get_alerts", "get_forecast"],
      "notAllowedTools": []
    }
  }
}
```

### SSE 特定參數

用於 Server-Sent Events HTTP 模式的參數：

| 參數 | 類型 | 必需 | 預設值 | 說明 |
|------|------|------|--------|------|
| `url` | `string` | 是 | - | 伺服器 URL（含協定和埠號） |
| `accessToken` | `string` | 否 | - | API 存取權杖 |
| `headers` | `object` | 否 | `{}` | 額外 HTTP 標頭 |
| `sslVerify` | `boolean` | 否 | `true` | 是否驗證 SSL 憑證 |
| `maxRetries` | `number` | 否 | `3` | HTTP 請求最大重試次數 |
| `backoffFactor` | `number` | 否 | `1.5` | 重試退避係數 |

**SSE 配置範例**：

```json
{
  "mcpServers": {
    "sse_weather": {
      "type": "sse",
      "url": "http://localhost:8080/sse",
      "accessToken": "password123",
      "disabled": false,
      "timeout": 45,
      "headers": {
        "User-Agent": "MCP-Weather-Client/1.0",
        "X-Client-Version": "1.0.0",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8"
      },
      "sslVerify": true,
      "maxRetries": 5,
      "backoffFactor": 2.0,
      "allowedTools": ["get_alerts", "get_forecast"],
      "notAllowedTools": []
    }
  }
}
```

### 工具權限控制

工具權限透過 `allowedTools` 和 `notAllowedTools` 進行精細控制：

#### 權限規則

1. **預設行為**: 如果 `allowedTools` 為空陣列，允許所有工具
2. **明確允許**: `allowedTools` 中列出的工具被允許使用
3. **明確禁用**: `notAllowedTools` 優先級最高，會覆蓋 `allowedTools`
4. **安全原則**: 當有疑問時，選擇更嚴格的限制

#### 權限配置範例

```json
{
  "mcpServers": {
    "readonly_weather": {
      "type": "sse",
      "url": "http://localhost:8080/sse",
      "allowedTools": ["get_alerts"],           // 只允許查看警報
      "notAllowedTools": ["get_forecast"]       // 明確禁用預報功能
    },
    "full_access_weather": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "weather.py"],
      "allowedTools": [],                       // 空陣列 = 允許所有工具
      "notAllowedTools": []                     // 不禁用任何工具
    },
    "forecast_only": {
      "type": "sse", 
      "url": "http://localhost:8080/sse",
      "allowedTools": ["get_forecast"],         // 只允許預報功能
      "notAllowedTools": ["get_alerts"]         // 禁用警報功能
    }
  }
}
```

## 環境變數配置

環境變數透過 `.env` 檔案或系統環境變數設定，提供敏感資訊和執行時配置。

### AI 模型 API 金鑰

```env
# Anthropic Claude API 金鑰
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# OpenAI GPT API 金鑰  
OPENAI_API_KEY=sk-your-openai-key-here

# Google Gemini API 金鑰
GOOGLE_API_KEY=your-google-ai-key-here
```

### 應用程式設定

```env
# 應用程式模式
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production

# MCP 伺服器設定
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8080
MCP_DEFAULT_TIMEOUT=30

# 天氣服務設定
WEATHER_API_TIMEOUT=30
WEATHER_CACHE_TTL=300
WEATHER_MAX_RETRIES=3

# 資料庫設定（如適用）
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379/0
```

### SSL/TLS 配置

```env
# SSL 憑證路徑（用於 HTTPS）
SSL_CERT_PATH=/path/to/certificate.pem
SSL_KEY_PATH=/path/to/private.key
SSL_CA_PATH=/path/to/ca-bundle.pem

# SSL 選項
SSL_VERIFY=true
SSL_MIN_VERSION=TLSv1.2
```

### 開發環境變數

```env
# 開發模式設定
DEBUG=true
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# 測試資料
TEST_STATE=CA
TEST_LATITUDE=37.7749
TEST_LONGITUDE=-122.4194

# 開發伺服器設定
DEV_SERVER_HOST=localhost
DEV_SERVER_PORT=8080
HOT_RELOAD=true
```

### 生產環境變數

```env
# 生產模式設定
DEBUG=false
LOG_LEVEL=WARNING
ENVIRONMENT=production

# 安全性設定
SECRET_KEY=your-very-secure-secret-key
JWT_SECRET=your-jwt-secret
SESSION_TIMEOUT=3600

# 效能設定
WORKERS=4
MAX_CONNECTIONS=1000
KEEP_ALIVE_TIMEOUT=65
```

## 傳輸模式對比

### STDIO vs SSE 詳細比較

| 特性 | STDIO 模式 | SSE 模式 |
|------|------------|----------|
| **設定複雜度** | 簡單 | 中等 |
| **網路需求** | 無（本地程序） | HTTP 連接 |
| **認證機制** | 無需認證 | API 金鑰認證 |
| **防火牆友善** | 是 | 需要開放埠號 |
| **遠端存取** | 不支援 | 完全支援 |
| **並發連接** | 單一連接 | 多用戶並發 |
| **資源使用** | 低 | 中等 |
| **延遲** | 極低 | 低到中等 |
| **可擴展性** | 低 | 高 |
| **故障排除** | 簡單 | 需要網路知識 |
| **部署複雜度** | 簡單 | 中等到高 |
| **監控能力** | 基本 | 豐富（HTTP 日誌） |

### 使用場景建議

#### STDIO 模式適用場景

```json
{
  "scenarios": [
    "本地開發和測試",
    "單用戶桌面應用",
    "無網路環境",
    "高度安全要求的環境", 
    "嵌入式系統",
    "批次處理腳本"
  ],
  "benefits": [
    "零網路配置",
    "最低延遲",
    "簡單部署",
    "無安全暴露面"
  ]
}
```

#### SSE 模式適用場景

```json
{
  "scenarios": [
    "多用戶 Web 應用",
    "微服務架構", 
    "雲端部署",
    "API 服務",
    "分散式系統",
    "第三方整合"
  ],
  "benefits": [
    "遠端存取能力",
    "水平擴展",
    "標準 HTTP 協定",
    "豐富的監控選項"
  ]
}
```

## 安全性配置建議

### API 金鑰管理

#### 1. 金鑰存儲最佳實務

```bash
# 使用環境變數（推薦）
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# 使用 .env 檔案（開發環境）
echo "ANTHROPIC_API_KEY=sk-ant-api03-..." >> .env

# 使用安全保險庫（生產環境）
# AWS Secrets Manager, Azure Key Vault, HashiCorp Vault
```

#### 2. 金鑰輪換策略

```json
{
  "key_rotation": {
    "frequency": "90 days",
    "process": [
      "生成新的 API 金鑰",
      "更新環境變數",
      "驗證服務正常運作",
      "撤銷舊金鑰"
    ],
    "automation": {
      "tools": ["GitHub Actions", "AWS Lambda", "Kubernetes CronJob"],
      "notifications": ["Slack", "Email", "PagerDuty"]
    }
  }
}
```

### 網路安全配置

#### 1. HTTPS 配置

```json
{
  "mcpServers": {
    "secure_sse_weather": {
      "type": "sse",
      "url": "https://weather.example.com/sse",
      "accessToken": "secure-token-here",
      "sslVerify": true,
      "headers": {
        "User-Agent": "SecureWeatherClient/1.0"
      }
    }
  }
}
```

#### 2. 防火牆規則

```bash
# 僅允許必要的埠號
sudo ufw allow 8080/tcp comment "MCP Weather SSE"
sudo ufw deny 8080/udp

# 限制來源 IP（如適用）
sudo ufw allow from 192.168.1.0/24 to any port 8080

# 啟用日誌記錄
sudo ufw logging on
```

### 存取控制

#### 1. 基於角色的存取控制

```json
{
  "mcpServers": {
    "admin_weather": {
      "type": "sse",
      "url": "https://weather-admin.example.com/sse",
      "accessToken": "admin-token",
      "allowedTools": ["get_alerts", "get_forecast", "admin_tools"]
    },
    "readonly_weather": {
      "type": "sse", 
      "url": "https://weather-readonly.example.com/sse",
      "accessToken": "readonly-token",
      "allowedTools": ["get_alerts"],
      "notAllowedTools": ["get_forecast", "admin_tools"]
    }
  }
}
```

#### 2. IP 白名單

```python
# 在 SSE 伺服器中實現 IP 白名單
class IPWhitelistMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_ips: list):
        super().__init__(app)
        self.allowed_ips = allowed_ips
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        if client_ip not in self.allowed_ips:
            return JSONResponse(
                status_code=403,
                content={"detail": "IP not allowed"}
            )
        return await call_next(request)

# 使用中介軟體
app.add_middleware(IPWhitelistMiddleware, allowed_ips=["192.168.1.100", "10.0.0.50"])
```

## 效能調優參數

### 連接池配置

```json
{
  "mcpServers": {
    "optimized_sse_weather": {
      "type": "sse",
      "url": "http://localhost:8080/sse",
      "timeout": 30,
      "maxRetries": 5,
      "backoffFactor": 1.5,
      "keepAlive": true,
      "connectionPool": {
        "maxConnections": 100,
        "maxKeepAlive": 20,
        "keepAliveTimeout": 300
      }
    }
  }
}
```

### 快取設定

```env
# Redis 快取配置
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300
CACHE_MAX_SIZE=1000

# 記憶體快取配置  
MEMORY_CACHE_SIZE=100MB
MEMORY_CACHE_TTL=300
```

### 併發控制

```json
{
  "performance": {
    "maxConcurrentRequests": 50,
    "requestQueueSize": 200,
    "workerThreads": 4,
    "asyncPoolSize": 10,
    "timeouts": {
      "connection": 30,
      "read": 60,
      "total": 120
    }
  }
}
```

### 監控和指標

```env
# 監控設定
METRICS_ENABLED=true
METRICS_PORT=9090
PROMETHEUS_ENDPOINT=/metrics

# 日誌設定
LOG_FORMAT=json
LOG_ROTATION=daily
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=7
```

## 配置範例

### 開發環境配置

```json
{
  "mcpServers": {
    "dev_stdio_weather": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "weather.py"],
      "cwd": "src/servers/weather/stdio",
      "disabled": false,
      "timeout": 60,
      "env": {
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG"
      },
      "allowedTools": [],
      "notAllowedTools": []
    },
    "dev_sse_weather": {
      "type": "sse",
      "url": "http://localhost:8080/sse",
      "accessToken": "dev-password123",
      "timeout": 30,
      "sslVerify": false,
      "headers": {
        "X-Environment": "development"
      },
      "allowedTools": [],
      "notAllowedTools": []
    }
  }
}
```

### 測試環境配置

```json
{
  "mcpServers": {
    "test_weather": {
      "type": "sse",
      "url": "https://test-weather.example.com/sse",
      "accessToken": "test-secure-token",
      "timeout": 45,
      "maxRetries": 3,
      "headers": {
        "X-Environment": "testing",
        "X-Test-Run-ID": "${TEST_RUN_ID}"
      },
      "allowedTools": ["get_alerts", "get_forecast"],
      "notAllowedTools": []
    }
  }
}
```

### 生產環境配置

```json
{
  "mcpServers": {
    "prod_weather_primary": {
      "type": "sse",
      "url": "https://weather-api.example.com/sse",
      "accessToken": "${WEATHER_API_TOKEN}",
      "timeout": 30,
      "maxRetries": 5,
      "backoffFactor": 2.0,
      "sslVerify": true,
      "headers": {
        "User-Agent": "ProductionWeatherClient/1.0",
        "X-Environment": "production",
        "X-Region": "us-west-2"
      },
      "allowedTools": ["get_alerts", "get_forecast"],
      "notAllowedTools": []
    },
    "prod_weather_fallback": {
      "type": "sse",
      "url": "https://weather-api-backup.example.com/sse", 
      "accessToken": "${WEATHER_BACKUP_TOKEN}",
      "timeout": 45,
      "disabled": false,
      "allowedTools": ["get_alerts"],
      "notAllowedTools": ["get_forecast"]
    }
  }
}
```

### 高可用性配置

```json
{
  "mcpServers": {
    "ha_weather_cluster": {
      "type": "sse",
      "url": "https://weather-lb.example.com/sse",
      "accessToken": "${HA_WEATHER_TOKEN}",
      "timeout": 20,
      "maxRetries": 3,
      "backoffFactor": 1.5,
      "keepAlive": true,
      "healthCheck": {
        "enabled": true,
        "interval": 30,
        "timeout": 10,
        "endpoint": "/health"
      },
      "circuitBreaker": {
        "enabled": true,
        "failureThreshold": 5,
        "recoveryTimeout": 60
      }
    }
  }
}
```

## 故障排除

### 常見配置錯誤

#### 1. JSON 格式錯誤

```bash
# 驗證 JSON 格式
cat servers-config.json | python -m json.tool

# 常見錯誤
# - 遺漏逗號
# - 重複金鑰  
# - 不當的引號
# - 註解（JSON 不支援註解）
```

#### 2. 路徑問題

```json
{
  "錯誤": {
    "cwd": "weather/stdio"  // 相對路徑可能有問題
  },
  "正確": {
    "cwd": "src/servers/weather/stdio"  // 從專案根目錄的相對路徑
  }
}
```

#### 3. 權限設定衝突

```json
{
  "問題範例": {
    "allowedTools": ["get_forecast"],
    "notAllowedTools": ["get_forecast"]  // 衝突！notAllowedTools 優先
  },
  "解決方案": {
    "allowedTools": ["get_forecast"],
    "notAllowedTools": []
  }
}
```

### 配置驗證腳本

```python
import json
import jsonschema
from pathlib import Path

def validate_config(config_path: str):
    """驗證 servers-config.json 配置"""
    
    # 配置 schema
    schema = {
        "type": "object",
        "properties": {
            "mcpServers": {
                "type": "object",
                "patternProperties": {
                    ".*": {
                        "type": "object",
                        "properties": {
                            "type": {"enum": ["stdio", "sse"]},
                            "disabled": {"type": "boolean"},
                            "timeout": {"type": "number", "minimum": 1},
                            "allowedTools": {"type": "array", "items": {"type": "string"}},
                            "notAllowedTools": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["type"]
                    }
                }
            }
        },
        "required": ["mcpServers"]
    }
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        jsonschema.validate(config, schema)
        print("✅ 配置檔案格式正確")
        
        # 額外驗證
        for server_name, server_config in config["mcpServers"].items():
            # 檢查工具權限衝突
            allowed = set(server_config.get("allowedTools", []))
            not_allowed = set(server_config.get("notAllowedTools", []))
            conflicts = allowed & not_allowed
            
            if conflicts:
                print(f"⚠️ {server_name}: 工具權限衝突 {conflicts}")
            
            # 檢查 STDIO 必要參數
            if server_config["type"] == "stdio":
                required = ["command", "args"]
                missing = [param for param in required if param not in server_config]
                if missing:
                    print(f"❌ {server_name}: 缺少必要參數 {missing}")
            
            # 檢查 SSE 必要參數
            if server_config["type"] == "sse":
                if "url" not in server_config:
                    print(f"❌ {server_name}: SSE 模式需要 url 參數")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON 格式錯誤: {e}")
        return False
    except jsonschema.ValidationError as e:
        print(f"❌ 配置驗證失敗: {e.message}")
        return False
    except FileNotFoundError:
        print(f"❌ 找不到配置檔案: {config_path}")
        return False

# 使用範例
if __name__ == "__main__":
    validate_config("servers-config.json")
```

### 效能分析工具

```python
import time
import asyncio
from src.client.client import MCPHost

async def benchmark_config():
    """測試不同配置的效能"""
    
    configs = [
        "servers-config.json",
        "servers-config-optimized.json",
        "servers-config-high-timeout.json"
    ]
    
    for config_path in configs:
        print(f"\n測試配置: {config_path}")
        host = MCPHost(config_path)
        
        try:
            # 測試連接時間
            start = time.time()
            await host.connect()
            connect_time = time.time() - start
            print(f"連接時間: {connect_time:.2f} 秒")
            
            # 測試工具呼叫時間
            start = time.time()
            result = await host.call_tool("get_alerts", {"state": "CA"})
            call_time = time.time() - start
            print(f"工具呼叫時間: {call_time:.2f} 秒")
            
            await host.disconnect()
            
        except Exception as e:
            print(f"配置測試失敗: {e}")

# 執行效能測試
asyncio.run(benchmark_config())
```

這個配置參考文件提供了完整的配置選項說明、最佳實務建議和故障排除指南，幫助使用者根據不同需求進行最佳化配置。