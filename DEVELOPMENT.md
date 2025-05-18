# AI DEBUG 系统开发文档

本文档为 AI DEBUG 系统的开发指南，旨在帮助开发者理解系统架构、扩展功能和维护代码。

## 架构概述

AI DEBUG 系统采用模块化设计，主要包含以下核心组件：

1. **输入层**：负责处理和标准化各种输入数据（错误信息、代码片段、问题描述和日志信息）
2. **LLM 分析引擎**：利用大型语言模型进行错误分析、代码分析、根因推断和解决方案生成
3. **Bug 知识库**：存储和检索历史 bug 记录，用于辅助分析
4. **输出层**：将分析结果格式化成不同形式（Markdown、HTML、JSON 等）
5. **API 服务**：提供 Web 界面和 RESTful API 接口

## 核心模块说明

### 输入层 (`src/input_layer`)

输入层负责标准化和初步处理用户输入，将原始数据转换为结构化格式。

主要类：

- `InputProcessor`：输入处理器基类
- `ErrorMessageProcessor`：错误信息处理器
- `CodeSnippetProcessor`：代码片段处理器
- `ProblemDescriptionProcessor`：问题描述处理器
- `LogInfoProcessor`：日志信息处理器
- `InputManager`：协调各种处理器的管理器

扩展指南：

- 添加新的输入类型：创建新的处理器类继承自`InputProcessor`，并在`InputManager`中注册
- 改进现有处理器：优化解析逻辑，增强特征提取能力

### LLM 分析引擎 (`src/llm_engine`)

分析引擎是系统的核心，负责利用 LLM 进行深入分析和推理。

主要类：

- `providers`模块：
  - `LLMProvider`：LLM 提供者的抽象基类
  - `OpenAIProvider`：OpenAI API 实现（支持 SDK 和 HTTP API）
  - `AzureOpenAIProvider`：Azure OpenAI API 实现（支持 SDK 和 HTTP API）
  - `AnthropicProvider`：Anthropic Claude API 实现
  - `create_llm_provider`：工厂函数，用于创建不同的 LLM 提供者实例
- `LLMClient`：与 LLM API 通信的客户端，使用工厂方法创建并管理不同的 LLM 提供者
- `ErrorMessageParser`：错误信息分析器
- `CodeAnalyzer`：代码分析器
- `ProblemCauseInferenceModule`：根因推断模块
- `FixSuggestionGenerator`：修复建议生成器
- `BugKnowledgeBaseClient`：与 Bug 知识库交互的客户端
- `AnalysisEngine`：协调各分析器的引擎

扩展指南：

- 添加新的分析器：创建新的分析器类，专注于特定类型的分析
- 改进提示词：优化各分析器中的提示词模板，提高 LLM 响应质量
- 支持新的 LLM：在`providers.py`中实现新的`LLMProvider`子类并在`create_llm_provider`工厂函数中注册

### 输出层 (`src/output_layer`)

输出层负责将分析结果格式化为不同形式，以适应不同的使用场景。

主要类：

- `ResultFormatter`：Markdown 格式化器
- `HTMLFormatter`：HTML 格式化器
- `JSONFormatter`：JSON 格式化器
- `InteractiveComponents`：交互组件生成器
- `OutputManager`：输出管理器

扩展指南：

- 添加新的输出格式：创建新的格式化器类
- 改进交互组件：优化 HTML 交互组件的设计和功能
- 自定义输出样式：修改格式化器中的输出模板

### API 服务 (`src/api_service`)

API 服务提供 HTTP 接口和 Web 界面，使系统能够被外部调用和使用。

主要类：

- `AIDebugAPI`：API 服务类

扩展指南：

- 添加新的 API 端点：在`register_routes`方法中注册新路由
- 改进 Web 界面：修改`templates/index.html`
- 添加认证机制：实现 API 密钥或其他认证方式

### 配置管理 (`src/config`)

配置模块负责加载和管理系统配置。

主要类：

- `ConfigManager`：配置管理器

扩展指南：

- 添加新的配置项：修改`config.json`并在相应模块中使用
- 环境变量配置：系统支持两种方式设置环境变量
  1. 使用环境变量文件：在项目根目录创建`.env`文件
  2. 直接在系统中设置环境变量

环境变量文件格式示例：

```
# API密钥配置
OPENAI_API_KEY=sk-your-api-key-here

# 其他配置
DEBUG=true
```

### 工具模块 (`src/utils`)

工具模块提供各种辅助函数和通用功能。

扩展指南：

- 添加新的工具函数：根据需要增加辅助函数
- 优化现有功能：改进错误处理、日志记录等

## 开发流程

### 添加新功能

1. **明确需求**：明确新功能的目标和需求
2. **设计接口**：设计功能的接口和与其他模块的交互方式
3. **编写测试**：先编写单元测试
4. **实现功能**：编写代码实现功能
5. **测试验证**：运行测试确保功能正常
6. **文档更新**：更新相关文档

### 代码风格

- 遵循 PEP 8 规范
- 使用类型注解
- 为所有公共函数和类编写文档字符串
- 使用有意义的变量名和函数名

### 测试策略

- 单元测试：针对各个模块的独立功能
- 集成测试：测试模块间的交互
- 端到端测试：模拟真实用户场景

## 部署指南

### 开发环境

1. 克隆代码库
2. 创建虚拟环境：`python -m venv venv`
3. 激活虚拟环境
4. 安装开发依赖：`pip install -r requirements.txt`
5. 配置环境变量：创建`.env`文件并设置必要的环境变量

### 生产环境

推荐使用 Docker 部署：

1. 创建`.env`文件并设置必要的环境变量
2. 构建 Docker 镜像：`docker build -t ai-debug .`
3. 运行容器：`docker-compose up -d`（使用环境变量文件）

也可以使用传统方式部署：

1. 设置生产环境配置
2. 使用 Gunicorn 或 uWSGI 作为 WSGI 服务器
3. 配置 Nginx 或 Apache 作为前端代理

## 故障排除

### 常见问题

1. **LLM API 连接失败**

   - 检查 API 密钥是否正确
   - 检查网络连接
   - 查看 API 服务状态

2. **Bug 知识库查询失败**

   - 检查知识库服务是否运行
   - 验证端点配置是否正确
   - 检查认证信息

3. **系统性能问题**
   - 优化 LLM 请求频率和内容
   - 考虑缓存常见查询结果
   - 监控系统资源使用情况

## 未来扩展计划

1. **支持更多语言**：添加对更多编程语言的专项支持
2. **改进分析质量**：优化提示词工程，提高分析准确性
3. **用户反馈学习**：基于用户反馈改进系统
4. **离线模式**：支持本地部署的 LLM 模型
5. **IDE 集成**：开发 VS Code、JetBrains 等 IDE 的插件集成

## 贡献指南

欢迎贡献代码、改进文档或报告问题。请遵循以下步骤：

1. Fork 代码库
2. 创建功能分支：`git checkout -b feature-name`
3. 提交更改：`git commit -m 'Add some feature'`
4. 推送到分支：`git push origin feature-name`
5. 提交 Pull Request

## 联系方式

如有任何问题或建议，请联系项目维护团队。
