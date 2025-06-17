# AI DEBUG 系统架构文档

本文档包含了 AI DEBUG 系统的架构设计图，使用 PlantUML 格式描述。

## 图表目录

1. [系统组件图](system_component_diagram.puml) - 展示系统的主要组件及其关系
2. [分析流程时序图](analysis_sequence_diagram.puml) - 展示系统如何处理分析请求
3. [对话模式时序图](dialog_sequence_diagram.puml) - 展示系统的交互式对话流程
4. [数据流图](data_flow_diagram.puml) - 展示系统中数据的流向
5. [部署架构图](deployment_diagram.puml) - 展示系统的部署结构
6. [用例图](use_case_diagram.puml) - 展示系统的功能用例

## 查看方式

这些 PlantUML 文件可以通过以下方式查看：

1. 使用 Visual Studio Code 的 PlantUML 插件
2. 在线 PlantUML 编辑器：[http://www.plantuml.com/plantuml/uml/](http://www.plantuml.com/plantuml/uml/)
3. 使用命令行工具将 .puml 文件转换为图片

## 图表说明

### 系统组件图

该图展示了 AI DEBUG 系统的主要组件及其关系，包括输入层、LLM 分析引擎、输出层、API 服务等。

### 分析流程时序图

该图展示了系统处理分析请求的流程，包括 API 服务模式和命令行分析模式两种工作方式。

### 对话模式时序图

该图展示了系统的交互式对话模式，用户如何通过 Web 界面与系统进行多轮对话。

### 数据流图

该图展示了系统中数据的流向，从用户输入到最终输出的整个过程。

### 部署架构图

该图展示了系统的部署结构，包括各个组件如何部署以及与外部服务的交互。

### 用例图

该图展示了系统的主要功能用例，包括不同角色（开发者、测试人员）如何使用系统。

## 更新时间

最后更新：2025 年 6 月 17 日
