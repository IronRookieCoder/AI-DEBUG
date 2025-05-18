"""测试输入层模块"""

import pytest
from src.input_layer import (
    InputProcessor, ErrorMessageProcessor, CodeSnippetProcessor,
    ProblemDescriptionProcessor, LogInfoProcessor, InputManager,
    process_input, process_combined_input
)


def test_error_message_processor():
    """测试错误信息处理器"""
    processor = ErrorMessageProcessor()
    
    # 测试Python错误
    python_error = """Traceback (most recent call last):
  File "app.py", line 42, in <module>
    result = process_data(data)
  File "app.py", line 21, in process_data
    return data[0]['value'] / 0
ZeroDivisionError: division by zero"""
    
    result = processor.process(python_error)
    assert result["type"] == "error_message"
    assert result["raw_content"] == python_error
    assert result["parsed"]["category"] == "exception"
    assert result["parsed"]["line"] == 21
    assert result["parsed"]["file"] == "app.py"
    
    # 测试JavaScript错误
    js_error = "TypeError: Cannot read property 'map' of undefined at processData (/app/src/utils.js:25:10)"
    result = processor.process(js_error)
    assert result["type"] == "error_message"
    assert result["raw_content"] == js_error
    assert result["parsed"]["category"] == "type_error"


def test_code_snippet_processor():
    """测试代码片段处理器"""
    processor = CodeSnippetProcessor()
    
    # 测试Python代码
    python_code = """def process_data(data):
    if not data:
        return None
    return data[0]['value'] / 0

# 调用函数
result = process_data(data)"""
    
    result = processor.process(python_code)
    assert result["type"] == "code_snippet"
    assert result["language"] == "python"
    assert len(result["parsed"]["tokens"]) > 0
    assert "process_data" in result["parsed"]["structure"]["functions"]
    
    # 测试JavaScript代码
    js_code = """function processData(data) {
  if (!data) return null;
  return data.map(item => item.value);
}

// 调用函数
const result = processData(null);"""
    
    result = processor.process(js_code)
    assert result["type"] == "code_snippet"
    assert result["language"] == "javascript"
    assert len(result["parsed"]["tokens"]) > 0


def test_problem_description_processor():
    """测试问题描述处理器"""
    processor = ProblemDescriptionProcessor()
    
    description = "我在调用process_data函数时遇到了除零错误，函数接收一个数据数组，但是在某些情况下可能会尝试除以零。"
    
    result = processor.process(description)
    assert result["type"] == "problem_description"
    assert result["raw_content"] == description
    assert len(result["parsed"]["keywords"]) > 0
    assert len(result["parsed"]["summary"]) > 0


def test_log_info_processor():
    """测试日志信息处理器"""
    processor = LogInfoProcessor()
    
    log_text = """2023-06-15 14:30:22 INFO - 应用启动
2023-06-15 14:30:23 INFO - 开始处理数据
2023-06-15 14:30:24 ERROR - 处理数据时出错: division by zero
2023-06-15 14:30:25 INFO - 应用关闭"""
    
    result = processor.process(log_text)
    assert result["type"] == "log_info"
    assert result["raw_content"] == log_text
    assert len(result["parsed"]["entries"]) == 4
    
    # 检查是否正确解析了日志级别和时间戳
    error_entry = result["parsed"]["entries"][2]
    assert "level" in error_entry
    assert error_entry["level"] == "ERROR"
    assert "timestamp" in error_entry
    assert "2023-06-15" in error_entry["timestamp"]


def test_input_manager():
    """测试输入管理器"""
    manager = InputManager()
    
    # 测试单个输入处理
    error_message = "TypeError: Cannot read property 'map' of undefined"
    result = manager.process_input("error_message", error_message)
    assert result["type"] == "error_message"
    assert result["raw_content"] == error_message
    
    # 测试组合输入处理
    combined_input = {
        "error_message": error_message,
        "problem_description": "函数调用出错",
        "invalid_type": "这个不会被处理"
    }
    
    result = manager.process_combined_input(combined_input)
    assert "inputs" in result
    assert "error_message" in result["inputs"]
    assert "problem_description" in result["inputs"]
    assert "invalid_type" not in result["inputs"]


def test_convenience_functions():
    """测试便捷函数"""
    error_message = "TypeError: Cannot read property 'map' of undefined"
    
    # 测试process_input
    result = process_input("error_message", error_message)
    assert result["type"] == "error_message"
    
    # 测试process_combined_input
    combined_input = {
        "error_message": error_message,
        "problem_description": "函数调用出错"
    }
    
    result = process_combined_input(combined_input)
    assert "inputs" in result
    assert "error_message" in result["inputs"]
    assert "problem_description" in result["inputs"]
