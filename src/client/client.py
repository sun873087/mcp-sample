import os
import asyncio
from typing import Optional
from contextlib import AsyncExitStack
from enum import Enum

from mcp import ClientSession, StdioServerParameters
from mcp.types import (
    LoggingMessageNotificationParams,
    ListToolsResult, 
    CallToolResult,     
    ListResourcesResult, 
    ReadResourceResult,
    ListPromptsResult,
    GetPromptResult
)
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client

from anthropic import Anthropic
from openai import OpenAI
from google import genai
from google.genai import types

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

class ModelVendor(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"

class MCPClient:
    """MCPClient類，用於連接和管理MCP伺服器"""
    def __init__(self, server_name: str, server_config: dict, logging_callback: Optional[callable] = None):
        """初始化MCPClient

        Args:
            server_name: 伺服器名稱
            server_config: 伺服器配置字典
            logging_callback: 自訂日誌回調函數，若為None則使用預設
        """
        self.server_name = server_name
        self.disabled = server_config.get("disabled", False)  # 是否禁用
        self.allowedTools = server_config.get("allowedTools", [])  # 允許的工具列表
        self.notAllowedTools = server_config.get("notAllowedTools", [])  # 禁用的工具列表
        self.timeout = server_config.get("timeout", 30)  # 超時時間，默認為30秒
        self.session: Optional[ClientSession] = None # 用於管理MCP伺服器連接
        self.exit_stack = AsyncExitStack() # 管理異步上下文
        self._logging_callback = logging_callback

    async def connect_to_local_server(self, server_config: dict):
        """連接至MCP伺服器

        Args:
            server_config: 伺服器配置字典
        """
        server_params = StdioServerParameters(
            command=server_config["command"], # 指定命令 (python 或 node)
            args=server_config["args"], # 指定命令行參數
            env=server_config.get("env", None), # 指定環境變量
            cwd=server_config.get("cwd", None), # 指定工作目錄
            encoding=server_config.get("encoding", "utf-8"), # 指定編碼
            encoding_error_handler=server_config.get("encoding_error_handler", "strict"), # 指定編碼錯誤處理器
        )

        # 使用stdio_client建立stdio連接
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params)) # 建立stdio連接
        self.stdio, self.write = stdio_transport # 解包stdio連接
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(
                read_stream=self.stdio, # 讀取流
                write_stream=self.write, # 寫入流
                logging_callback=self.logging_callback, # 日誌回調函數
            )
        ) # 建立ClientSession

        await self.session.initialize() # 初始化ClientSession

        # List available tools
        response = await self.session.list_tools() # 列出可用工具
        tools = response.tools # 解包工具
        print("\nConnected to server with tools:", [tool.name for tool in tools]) # 打印連接成功訊息

    async def connect_to_sse_server(self, server_config: dict):
        """連接至SSE伺服器

        Args:
            server_url: 伺服器URL
        """
        # Store the context managers so they stay alive
        sse_params = {
            "url": server_config["url"], # 伺服器URL
            "timeout": self.timeout, # 建立連線超時時間
            "sse_read_timeout": self.timeout * 10 # SSE讀取超時時間，默認為建立連線超時的10倍
        }
        # 如果有accessToken，則添加到sse_params
        if "accessToken" in server_config:
            sse_params["headers"] = {
                "Authorization": f"Bearer {server_config['accessToken']}" # 添加授權標頭
            }
        self._streams_context = sse_client(**sse_params)
        read_stream, write_stream = await self._streams_context.__aenter__()
        self._session_context = ClientSession(
            read_stream=read_stream, # 讀取流
            write_stream=write_stream, # 寫入流
            logging_callback=self.logging_callback, # 日誌回調函數
        )        
        self.session: ClientSession = await self._session_context.__aenter__()

        # Initialize
        await self.session.initialize()

        # List available tools to verify connection
        print("Initialized SSE client...")
        print("Listing tools...")
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def connect_to_http_server(self, server_config: dict):
        """連接至HTTP伺服器

        Args:
            server_config: 伺服器配置字典
        """
        # Store the context managers so they stay alive
        http_params = {
            "url": server_config["url"], # 伺服器URL
            "timeout": self.timeout, # 建立連線超時時間
            "sse_read_timeout": self.timeout * 10 # SSE讀取超時時間，默認為建立連線超時的10倍
        }
        if "accessToken" in server_config:
            http_params["headers"] = {
                "Authorization": f"Bearer {server_config['accessToken']}" # 添加授權標頭
            }
        self._streams_context = streamablehttp_client(**http_params)
        result = await self._streams_context.__aenter__()
        print(f"返回值類型: {type(result)}")
        print(f"返回值內容: {result}")
        print(f"返回值長度: {len(result) if hasattr(result, '__len__') else 'N/A'}")        
        receive_stream = result[0]
        send_stream = result[1]
        self._session_context = ClientSession(
            read_stream=receive_stream, # 讀取流
            write_stream=send_stream, # 寫入流
            logging_callback=self.logging_callback, # 日誌回調函數
        )
        self.session: ClientSession = await self._session_context.__aenter__()
        # Initialize
        await self.session.initialize()

        # List available tools to verify connection
        print("Initialized HTTP client...")
        print("Listing tools...")
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])
        



    async def list_tools(self) -> ListToolsResult:
        """列出所有可用的工具"""
        if not self.session:
            raise RuntimeError("Session is not initialized. Please connect to a server first.")
        response = await self.session.list_tools() # 列出工具
        return response

    async def call_tool(self, tool_name: str, tool_args: dict) -> CallToolResult:
        if not self.session:
            raise RuntimeError("Session is not initialized. Please connect to a server first.")
        response = await self.session.call_tool(tool_name, tool_args)
        return response

    async def list_resources(self) -> ListResourcesResult:
        """列出所有可用的資源"""
        if not self.session:
            raise RuntimeError("Session is not initialized. Please connect to a server first.")
        response = await self.session.list_resources() # 列出資源
        return response
    
    async def read_resource(self, resource_uri: str) -> ReadResourceResult:
        """讀取指定資源的內容

        Args:
            resource_uri: 資源URI

        Returns:
            Resource content
        """
        if not self.session:
            raise RuntimeError("Session is not initialized. Please connect to a server first.")
        response = await self.session.read_resource(resource_uri) # 讀取資源
        return response

    async def list_prompts(self) -> ListPromptsResult:
        """列出所有可用的提示"""
        if not self.session:
            raise RuntimeError("Session is not initialized. Please connect to a server first.")
        response = await self.session.list_prompts() # 列出提示
        return response
    
    async def get_prompt(
        self, name: str, arguments: dict[str, str] | None = None
    ) -> GetPromptResult:
        """獲取指定提示的內容

        Args:
            name: 提示名稱
            arguments: 提示參數

        Returns:
            Prompt content
        """
        if not self.session:
            raise RuntimeError("Session is not initialized. Please connect to a server first.")
        response = await self.session.get_prompt(name, arguments) # 獲取提示
        return response
    
    async def logging_callback(self, params: LoggingMessageNotificationParams):
        """日誌回調函數，用於處理MCP伺服器的日誌消息

        Args:
            message: 日誌消息
        """
        if self._logging_callback:            
            await self._logging_callback(self.server_name, params)

    async def cleanup(self):
        """清理資源"""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None) # 關閉異步上下文
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None) # 關閉異步上下文
        await self.exit_stack.aclose() # 關閉異步上下文


class MCPHost:
    """MCPHost類，用於管理多個MCPClient實例"""
    def __init__(self, model_vendor: ModelVendor, config: Optional[dict] = None):
        """初始化MCPHost

        Args:
            model_vendor: 模型供應商 (Anthropic, OpenAI, Google)
            config: MCP伺服器配置字典
        """
        self.mcp_clients = []  # 用於存儲MCP客戶端列表
        self.anthropic = Anthropic(
            api_key=anthropic_api_key, # 使用Anthropic API密鑰
        ) # 初始化Anthropic API
        self.openai = OpenAI(
            api_key=openai_api_key,
        ) # 初始化OpenAI API
        self.client = genai.Client(
            api_key=google_api_key, # 使用Google API密鑰
        )
        self.model_vendor = model_vendor
        self.config = config or {}  # 使用提供的配置或默認空字典
        # 格式必須為 {"mcpServers": {"<server_name>": {"command": "python", "args": ["<path_to_server_script>"]}}}
        # 定義 json schema
        json_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "mcpServers": {
                    "type": "object",
                    "patternProperties": {                        
                        "^[a-zA-Z0-9_]{1,128}$": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["http","sse", "stdio"]
                                },
                                "url": {
                                    "type": "string",
                                    "format": "uri"
                                },
                                "command": {
                                    "type": "string"
                                },
                                "args": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                },
                                "disabled": {
                                    "type": "boolean"
                                },
                                "allowedTools": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                },
                                "notAllowedTools": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                },
                                "timeout": {
                                    "type": "number"
                                }
                            },
                            "required": ["type"],
                            "allOf": [
                                {
                                "if": {
                                    "properties": { "type": { "const": "stdio" } }
                                },
                                "then": {
                                    "required": ["command", "args"]
                                }
                                },
                                {
                                "if": {
                                    "properties": { "type": { "const": "sse" } }
                                },
                                "then": {
                                    "required": ["url"]
                                }
                                },
                                {
                                "if": {
                                    "properties": { "type": { "const": "http" } }
                                },
                                "then": {
                                    "required": ["url"]
                                }
                                },
                            ],
                            "additionalProperties": True
                        }
                    },
                    "additionalProperties": False
                }
            },
            "required": ["mcpServers"],
            "additionalProperties": False
        }

        # 驗證config格式
        try:
            jsonschema.validate(config, json_schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Invalid config format: {e}")

    async def create_mcp_clients(self):
        """根據配置創建MCP客戶端"""
        if not self.config or "mcpServers" not in self.config:
            raise ValueError("No MCP servers configured")

        mcp_clients: list[MCPClient] = []
        mcp_servers = self.config.get("mcpServers", {})
        for server_name, server_config in mcp_servers.items():
            print(f"Server Name: {server_name}")
            print(f"Config: {server_config}")
            print("------")
            if server_config.get("disabled", False):
                print(f"Skipping disabled server: {server_name}")
                continue
            client = MCPClient(server_name, server_config, self.logging_callback)  # 初始化MCPClient
            if "sse" in server_config["type"]:
                await client.connect_to_sse_server(server_config)
            elif "http" in server_config["type"]:
                await client.connect_to_http_server(server_config)
            else:
                await client.connect_to_local_server(server_config)
            mcp_clients.append(client)  # 添加到MCP客戶端列表

        self.mcp_clients = mcp_clients  # 保存MCP客戶端列表
    
    async def get_mcp_client(self, server_name: str) -> MCPClient:
        """獲取指定名稱的MCP客戶端

        Args:
            server_name: 伺服器名稱

        Returns:
            MCPClient: 指定名稱的MCP客戶端
        """
        for client in self.mcp_clients:
            if client.server_name == server_name:
                return client
        raise ValueError(f"No MCP client found for server name: {server_name}")
    
    async def get_available_tools(self) -> list:
        """獲取所有可用的工具

        Returns:
            list: 可用工具列表
        """
        available_tools = []  # 用於存儲可用工具
        for mcpClient in self.mcp_clients:
            response = await mcpClient.list_tools()
            # 過濾掉禁用的工具
            if mcpClient.disabled or not response.tools: # 如果MCP客戶端被禁用或沒有工具，則跳過
                continue # 如果MCP客戶端被禁用，則跳過 我住在台灣新竹縣竹北市，請問這裡的天氣如何?
            
            if self.model_vendor == ModelVendor.GOOGLE:
                # 將工具轉換為適合Google GenAI的格式
                tools = [
                    types.Tool(function_declarations=[types.FunctionDeclaration(
                        name=f"{mcpClient.server_name}-{tool.name}",
                        description=tool.description,
                        parameters=tool.inputSchema
                    )]) for tool in response.tools
                ]                
                # 先加入允許的工具
                if mcpClient.allowedTools:
                    # 過濾掉不在允許列表中的工具
                    tools = [tool for tool in tools if tool.function_declarations[0].name.split("-")[1] in mcpClient.allowedTools]
                # 如果有禁用的工具，則過濾掉禁用的工具
                if mcpClient.notAllowedTools:
                    # 過濾掉在禁用列表中的工具
                    tools = [tool for tool in tools if tool.function_declarations[0].name.split("-")[1] not in mcpClient.notAllowedTools]

            elif self.model_vendor == ModelVendor.ANTHROPIC:
                # 將工具轉換為適合Anthropic的格式
                tools = [{
                    "name": f"{mcpClient.server_name}-{tool.name}",  # 工具名稱
                    "description": tool.description,  # 工具描述
                    "input_schema": tool.inputSchema  # 工具輸入模式
                } for tool in response.tools]
                # 先加入允許的工具
                if mcpClient.allowedTools:
                    # 過濾掉不在允許列表中的工具
                    tools = [tool for tool in tools if tool["name"].split("-")[1] in mcpClient.allowedTools]
                # 如果有禁用的工具，則過濾掉禁用的工具
                if mcpClient.notAllowedTools:
                    # 過濾掉在禁用列表中的工具
                    tools = [tool for tool in tools if tool["name"].split("-")[1] not in mcpClient.notAllowedTools]
            else:
                # 將工具轉換為適合OpenAI的格式
                tools = [{
                    "type": "function",
                    "function": {
                        "name": f"{mcpClient.server_name}-{tool.name}",
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                } for tool in response.tools]
                # 先加入允許的工具
                if mcpClient.allowedTools and mcpClient.allowedTools != []:
                    # 過濾掉不在允許列表中的工具
                    tools = [tool for tool in tools if tool["function"]["name"].split("-")[1] in mcpClient.allowedTools]
                # 如果有禁用的工具，則過濾掉禁用的工具
                if mcpClient.notAllowedTools and mcpClient.notAllowedTools != []:
                    # 過濾掉在禁用列表中的工具
                    tools = [tool for tool in tools if tool["function"]["name"].split("-")[1] not in mcpClient.notAllowedTools]
            # 將工具添加到可用工具列表
            available_tools.extend(tools)
            
        return available_tools

    async def process_query_anthropic(self, query: str) -> str:
        """使用Claude和可用工具處理查詢

        Args:
            query: 用戶查詢

        Returns:
            str: 處理後的回應
        """
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        available_tools = await self.get_available_tools() # 獲取可用工具

        # 初始Claude API調用
        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022", # 使用Claude 3.5 Sonnet模型
            max_tokens=1000, # 最大令牌數
            messages=messages, # 用戶查詢
            tools=available_tools # 可用工具
        )       

        # 處理回應並處理工具調用
        tool_results = []
        final_text = []

        assistant_message_content = []
        for content in response.content:
            if content.type == 'text': # 如果內容是文本
                final_text.append(content.text) # 添加到最終文本
                assistant_message_content.append(content) # 添加到助手消息內容
            elif content.type == 'tool_use': # 如果內容是工具調用
                tool_name = content.name
                server_name = tool_name.split("-")[0] # 獲取伺服器名稱
                tool_name = tool_name.split("-")[1]
                tool_args = content.input
                
                # 執行工具調用
                mcpClient = await self.get_mcp_client(server_name) # 獲取MCP客戶端
                result = await mcpClient.call_tool(tool_name, tool_args) # 調用工具
                tool_results.append({"call": tool_name, "result": result}) # 添加到工具結果
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]") # 添加到最終文本

                assistant_message_content.append(content) # 添加到助手消息內容
                messages.append({
                    "role": "assistant", # 添加到消息
                    "content": assistant_message_content # 添加到消息內容
                })
                messages.append({
                    "role": "user", # 添加到消息
                    "content": [
                        {
                            "type": "tool_result", # 添加到消息
                            "tool_use_id": content.id, # 添加到消息
                            "content": result.content # 添加到消息內容
                        }
                    ]
                })

                # 從Claude獲取下一個回應
                response = self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20241022", # 使用Claude 3.5 Sonnet模型
                    max_tokens=1000, # 最大令牌數
                    messages=messages, # 用戶查詢
                    tools=available_tools # 可用工具
                )

                final_text.append(response.content[0].text) # 添加到最終文本

        return "\n".join(final_text)

    async def process_query_openai(self, query: str) -> str:
        """使用OpenAI和可用工具處理查詢

        Args:
            query: 用戶查詢

        Returns:
            str: 處理後的回應
        """   
        messages = [
            {
                "role": "system",
                "content": f"You are a helpful assistant. Please use tools when necessary."
            },
            {                
                "role": "user",
                "content": query
            }
        ]

        # 獲取可用工具
        available_tools = await self.get_available_tools() # 獲取可用工具

        is_finished = False # 標記是否完成
        final_text = []
        tool_results = []        
        while is_finished == False:
            # 初始OpenAI API調用
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages, # 用戶查詢
                tools=available_tools, # 可用工具
                tool_choice="auto", # 自動選擇工具
                max_tokens=1000 # 最大令牌數
            )            
            # 處理回應並處理工具調用
            for choice in response.choices:
                if choice.finish_reason == 'stop':
                    final_text.append(choice.message.content)
                    is_finished = True # 標記為完成
                    break # 如果完成原因是stop，則退出循環
                elif choice.finish_reason == 'tool_calls':
                    # 加入 assistant message 來保留 tool_call context
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": choice.message.tool_calls
                    })
                    for tool_call in choice.message.tool_calls:
                        tool_name = tool_call.function.name
                        server_name = tool_name.split("-")[0] # 獲取伺服器名稱
                        tool_name = tool_name.split("-")[1]
                        # 獲取工具參數
                        tool_args = tool_call.function.arguments
                        tool_args = json.loads(tool_args) # 將工具參數轉換為字典
                        # 執行工具調用 
                        mcpClient = await self.get_mcp_client(server_name) # 獲取MCP客戶端
                        result = await mcpClient.call_tool(tool_name, tool_args) # 調用工具
                        tool_results.append({"call": tool_name, "result": result}) # 添加到工具結果
                        final_text.append(f"[Calling tool {tool_name} with args {tool_args}]") # 添加到最終文本
                        messages.append({
                            "role": "tool", # 添加到消息
                            "tool_call_id": tool_call.id, # 添加到消息
                            "content": result.content[0].text
                        })
        return "\n".join(final_text)

    async def process_query_google(self, query: str) -> str:
        """使用Google GenAI和可用工具處理查詢
        
        Args:
            query: 用戶查詢
        Returns:
            str: 處理後的回應
        """
        available_tools = await self.get_available_tools() # 獲取可用工具
        is_finished = False # 標記是否完成
        final_text = []
        tool_results = []  

        # 初始Google GenAI API調用
        chat = self.client.aio.chats.create(
            model="gemini-2.5-pro", # "gemini-2.5-pro"
            config=types.GenerateContentConfig(
                system_instruction = f"You are a helpful assistant. Please use tools when necessary.",
                tools=available_tools,
                max_output_tokens=1000, # 最大輸出令牌數
            )
        )
        response = await chat.send_message_stream(query) # 發送用戶查詢並獲取流式回應
        while is_finished == False:  
            async for chunk in response: # 使用異步迭代器處理流式回應
                if chunk.text: # 如果有文本內容
                    final_text.append(chunk.text) # 添加到最終文本
                    is_finished = True # 標記為完成
                if chunk.function_calls: # 如果有工具調用
                    func_results = [] # 用於存儲工具結果
                    for function_call in chunk.function_calls:
                        tool_name = function_call.name
                        server_name = tool_name.split("-")[0] # 獲取伺服器名稱
                        tool_name = tool_name.split("-")[1]
                        tool_args = function_call.args
                        # 執行工具調用
                        mcpClient = await self.get_mcp_client(server_name) # 獲取MCP客戶端
                        result = await mcpClient.call_tool(tool_name, tool_args) # 調用工具
                        tool_results.append({"call": tool_name, "result": result}) # 添加到工具結果
                        final_text.append(f"[Calling tool {tool_name} with args {tool_args}]") # 添加到最終文本
                        func_results.append(result.content[0].text) # 添加到工具結果                    
                    response = await chat.send_message_stream(func_results) # 發送工具結果並獲取流式回應
        return "\n".join(final_text)

    async def chat_loop(self):
        """運行交互式聊天迴圈"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip() # 獲取用戶查詢
                
                if query.lower() == 'quit': # 如果用戶輸入quit
                    break # 退出迴圈

                if query.lower() == 'logs':
                    response = await self.session.read_resource("file:///logs/app.log")
                    print("\n" + response)
                    continue

                match self.model_vendor:
                    case ModelVendor.ANTHROPIC:
                        response = await self.process_query_anthropic(query) # 處理用戶查詢
                    case ModelVendor.GOOGLE:
                        response = await self.process_query_google(query) # 處理用戶查詢
                    case _:
                        response = await self.process_query_openai(query) # 處理用戶查詢
                print("\n" + response) # 打印回應

            except Exception as e:
                print(f"\nError: {str(e)}") # 打印錯誤

    async def logging_callback(self, server_name: str, params: LoggingMessageNotificationParams):
        """日誌回調函數，用於處理MCP伺服器的日誌消息

        Args:
            server_name: 伺服器名稱
            params: 日誌消息參數
        """
        print(f"[{server_name} 日誌回調] {params}") # 打印日誌消息

    async def cleanup(self):
        """清理資源"""
        for client in self.mcp_clients:
            await client.cleanup()  # 清理每個MCP客戶端的資源
            

import json
import jsonschema
async def main():    
    # 讀取servers-config.json
    with open('servers-config.json', 'r') as f:
        config = json.load(f)

    host = MCPHost(model_vendor=ModelVendor.ANTHROPIC, config=config) # 初始化MCPHost
    await host.create_mcp_clients() # 創建MCP客戶端
    await host.chat_loop() # 運行交互式聊天迴圈
    await host.cleanup() # 清理資源

if __name__ == "__main__":
    import sys
    asyncio.run(main()) # 運行主函數