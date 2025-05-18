# AI DEBUG 系统

基于 LLM 的智能调试系统，可以分析错误信息、代码片段和日志信息，提供智能化的 BUG 分析和修复建议。

## 系统架构

本系统包含以下主要组件：

- 数据获取：从 GitLab 和 TD 系统爬取数据（已存在）
- 数据清洗预处理：清理噪音数据、文本预处理、代码结构化处理（已存在）
- BUG 知识库：混合存储、向量化模块、检索模块、用户界面（已存在）
- 输入层：处理错误信息、代码片段、问题描述和日志信息
- LLM 分析引擎：错误信息解析、代码分析、原因推断、修复建议
- 输出层：结果展示、交互功能
- 系统集成：chatWorkflow、CICD 流程、实时诊断（已存在）
- API 服务：对外提供服务接口

## 安装指南

### 前提条件

- Python 3.6+
- 虚拟环境（推荐）
- Git（用于克隆代码库）

### 安装步骤

1. 克隆代码库

   ```bash
   git clone [repository-url] AI-DEBUG
   cd AI-DEBUG
   ```

2. 使用提供的启动脚本（会自动创建虚拟环境并安装依赖）
   - Windows: `start.bat`
   - Linux/Mac: `bash start.sh`

### 手动安装

1. 创建虚拟环境

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

AI DEBUG 系统提供两种使用方式：

### 1. API 服务模式

启动 Web 服务，提供 API 接口和 Web 界面。

```bash
# 使用启动脚本
./start.sh
# 或者在Windows上
start.bat

# 手动启动
python main.py api [--host HOST] [--port PORT] [--debug]
```

启动后，可以通过浏览器访问 `http://localhost:5000` 使用 Web 界面。

### 2. 命令行分析模式

直接从命令行分析特定的错误、代码或日志文件。

```bash
# 使用启动脚本
./start.sh --analyze --error examples/error_messages/python_zero_division.txt --code examples/code_snippets/python_division.py

# 手动启动
python main.py analyze --error <错误文件> --code <代码文件> [--description <描述文件>] [--log <日志文件>] [--output <格式>] [--output-file <输出文件>]
```

## API 文档

### 分析端点

**POST /api/v1/analyze**

请求体示例：

```json
{
  "error_message": "TypeError: Cannot read property 'map' of undefined",
  "code_snippet": "function processArray(arr) {\n  return arr.map(item => item.value);\n}",
  "problem_description": "调用processArray函数时出错",
  "log_info": "2023-06-15 14:30:22 ERROR - 处理数据时出错",
  "output_format": "json"
}
```

响应示例：

```json
{
  "analyses": {
    "error_analysis": { ... },
    "code_analysis": { ... },
    "root_cause": { ... },
    "solution": { ... }
  },
  "similar_bugs": [ ... ]
}
```

### 健康检查端点

**GET /api/v1/health**

### 反馈端点

**POST /api/v1/feedback**

## 示例

系统提供了一些示例文件，可以用来测试功能：

- 错误信息示例: `examples/error_messages/`
- 代码片段示例: `examples/code_snippets/`
- 日志示例: `examples/log_samples/`

使用示例文件测试系统：

```bash
./start.sh --analyze --error examples/error_messages/python_zero_division.txt --code examples/code_snippets/python_division.py --log examples/log_samples/app_log.txt --output markdown
```

## 开发指南

### 项目结构

```
main.py             # 主入口文件
README.md           # 项目说明文档
requirements.txt    # 依赖项列表
src/                # 源代码目录
├── api_service/    # API服务模块
├── config/         # 配置模块
├── input_layer/    # 输入层模块
├── llm_engine/     # LLM分析引擎模块
├── output_layer/   # 输出层模块
├── tests/          # 测试模块
└── utils/          # 工具模块
examples/           # 示例文件目录
start.sh            # Linux/Mac启动脚本
start.bat           # Windows启动脚本
```

### 运行测试

```bash
# 激活虚拟环境后
pytest src/tests/
```

## 配置说明

配置文件位于 `src/config/config.json`，可以修改以下设置：

### LLM 配置

```json
"llm": {
  "provider": "openai",       // LLM提供者: openai, azure, anthropic
  "model": "gpt-4",           // 模型名称
  "api_key": "${OPENAI_API_KEY}", // API密钥
  "temperature": 0.3,         // 温度参数
  "max_tokens": 2000,         // 最大生成令牌数
  "endpoint": "${AZURE_OPENAI_ENDPOINT}", // Azure OpenAI端点
  "deployment_name": "${AZURE_OPENAI_DEPLOYMENT}" // Azure OpenAI部署名称
}
```

### 其他配置

- Bug 知识库配置
- API 服务配置
- 日志配置

系统支持使用环境变量来设置敏感信息（如 API 密钥）。有两种方式可以设置环境变量：

### 1. 使用环境变量文件（推荐）

在项目根目录创建一个 `.env` 文件（或复制 `.env.example`），然后设置您的环境变量：

```
# OpenAI API配置
OPENAI_API_KEY=your_actual_api_key_here

# Azure OpenAI配置（如果使用Azure提供者）
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
LLM_API_KEY=your-azure-api-key

# Anthropic API配置（如果使用Anthropic提供者）
ANTHROPIC_API_KEY=your-anthropic-api-key
```

系统启动时会自动加载此文件中的环境变量。

### 2. 手动设置环境变量

或者，您可以在启动系统前手动设置环境变量：

```bash
# Windows
set OPENAI_API_KEY=your_actual_api_key_here

# Linux/Mac
export OPENAI_API_KEY=your_actual_api_key_here
```

## 常见问题

**Q: 如何更换 LLM 提供者？**  
A: 修改 `src/config/config.json` 中的 `llm.provider` 字段，可选值有 "openai"、"azure" 和 "anthropic"。不同提供者需要配置不同的环境变量，请参考配置说明。系统会自动使用当前版本的 OpenAI SDK（如果安装了）或回退到 HTTP API 请求。

**Q: 如何更换 LLM 模型？**  
A: 修改 `src/config/config.json` 中的 `llm.model` 字段。对于 OpenAI 提供者，可以设置为 "gpt-4"、"gpt-3.5-turbo" 等；对于 Azure OpenAI，请使用您的部署名称；对于 Anthropic，可以使用 "claude-3-opus-20240229" 等 Claude 模型。

**Q: 如何连接到自定义的 Bug 知识库？**  
A: 修改 `src/config/config.json` 中的 `bug_knowledge_base.endpoint` 字段。

**Q: 系统支持哪些编程语言的错误分析？**  
A: 系统主要支持 Python 和 JavaScript，但也能处理 Java、C++等常见语言的错误信息。
