# AI DEBUG 系统快速入门

这个快速入门指南将帮助您在几分钟内上手使用 AI DEBUG 系统。

## 1. 安装

### 设置 API 密钥（必须）

在开始使用之前，您需要设置 OpenAI API 密钥。最简单的方法是：

1. 在项目根目录创建一个名为 `.env` 的文件
2. 添加以下内容（替换为您的实际 API 密钥）：

```
OPENAI_API_KEY=your_actual_api_key_here
```

如果您没有手动创建此文件，启动脚本会为您创建一个模板文件，您需要编辑它。

### 使用启动脚本（推荐）

**Windows:**

```
start.bat
```

**Linux/Mac:**

```
chmod +x start.sh
./start.sh
```

启动脚本会自动设置虚拟环境并安装所需依赖。

### 使用 Docker（可选）

如果您已安装 Docker，可以使用以下命令启动：

```bash
docker-compose up -d
```

注意：使用 Docker 时，`.env` 文件中的环境变量会自动被传递到容器中。

## 2. 使用 Web 界面

启动系统后，打开浏览器访问：

```
http://localhost:5000
```

您将看到 AI DEBUG 系统的 Web 界面，可以：

1. 输入错误信息
2. 提供代码片段
3. 描述问题
4. 提供日志信息
5. 选择输出格式
6. 点击"分析调试"按钮获取结果

## 3. 命令行使用

通过命令行可以快速分析特定文件中的错误：

```bash
# Windows
start.bat --analyze --error examples/error_messages/python_zero_division.txt --code examples/code_snippets/python_division.py

# Linux/Mac
./start.sh --analyze --error examples/error_messages/python_zero_division.txt --code examples/code_snippets/python_division.py
```

## 4. API 使用

您可以通过 API 集成 AI DEBUG 系统到自己的应用中：

```bash
curl -X POST http://localhost:5000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "error_message": "TypeError: Cannot read property \"map\" of undefined",
    "code_snippet": "function processArray(arr) {\n  return arr.map(item => item.value);\n}",
    "problem_description": "调用processArray函数时出错",
    "output_format": "json"
  }'
```

## 5. 示例场景

### 场景 1：Python 除零错误

**错误信息：**

```
ZeroDivisionError: division by zero
```

**代码片段：**

```python
def process_data(data):
    return data[0]['value'] / data[1]['value']

test_data = [{'id': 1, 'value': 10}, {'id': 2, 'value': 0}]
result = process_data(test_data)
```

**系统分析：** 系统将检测到除以零的错误，分析根本原因，并提供修复建议。

### 场景 2：JavaScript 未定义属性

**错误信息：**

```
TypeError: Cannot read property 'map' of undefined
```

**代码片段：**

```javascript
function processData(data) {
  return data.map((item) => item.value);
}

const result = processData(null);
```

**系统分析：** 系统将识别出尝试对 null 或 undefined 调用 map 方法的错误，分析原因并提供解决方案。

## 6. 下一步

- 查看完整[README.md](README.md)了解更多功能
- 阅读[DEVELOPMENT.md](DEVELOPMENT.md)参与开发
- 尝试使用不同的错误和代码组合以熟悉系统功能

## 7. 故障排除

- **问题：** 启动失败  
  **解决：** 检查 Python 版本（需要 3.6+）和依赖安装

- **问题：** LLM API 错误  
  **解决：** 检查 src/config/config.json 中的 API 密钥配置

- **问题：** 分析结果不准确  
  **解决：** 尝试提供更完整的错误信息和代码上下文
