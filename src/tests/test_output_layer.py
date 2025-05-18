"""测试输出层模块"""

import pytest
import json
from src.output_layer import (
    ResultFormatter, HTMLFormatter, JSONFormatter,
    InteractiveComponents, OutputManager, format_result
)


def test_result_formatter():
    """测试结果格式化器"""
    # 创建一个测试用的错误分析结果
    error_analysis = {
        "error_type": "ZeroDivisionError",
        "description": "尝试除以零",
        "possible_causes": ["除数为零", "未进行空值检查"],
        "solution_steps": ["添加除数为零的检查", "添加错误处理"]
    }
    
    # 测试错误分析格式化
    formatted = ResultFormatter.format_error_analysis(error_analysis)
    assert "错误分析" in formatted
    assert "ZeroDivisionError" in formatted
    assert "尝试除以零" in formatted
    assert "可能的原因" in formatted
    assert "解决步骤" in formatted
    
    # 创建一个测试用的代码分析结果
    code_analysis = {
        "code_quality": "较差",
        "potential_bugs": ["除以零风险", "未处理空值"],
        "performance_issues": ["循环效率低"],
        "security_concerns": [],
        "improvement_suggestions": ["添加错误处理", "重构循环"]
    }
    
    # 测试代码分析格式化
    formatted = ResultFormatter.format_code_analysis(code_analysis)
    assert "代码分析" in formatted
    assert "代码质量评估" in formatted
    assert "较差" in formatted
    assert "潜在问题" in formatted
    assert "性能问题" in formatted
    
    # 创建一个测试用的根因分析结果
    root_cause = {
        "root_cause": "函数未对除数进行检查",
        "explanation": "函数直接进行除法操作，没有检查除数是否为零",
        "confidence_level": 9,
        "related_factors": ["数据验证不足", "错误处理缺失"]
    }
    
    # 测试根因分析格式化
    formatted = ResultFormatter.format_root_cause(root_cause)
    assert "根因分析" in formatted
    assert "函数未对除数进行检查" in formatted
    assert "详细解释" in formatted
    assert "置信度" in formatted
    assert "9/10" in formatted
    
    # 创建一个测试用的解决方案
    solution = {
        "solution_summary": "添加除数检查和错误处理",
        "fix_steps": ["检查除数是否为零", "添加try-except块"],
        "code_changes": [
            {
                "original_code": "return data[0]['value'] / 0",
                "fixed_code": "if data[0]['value'] == 0:\n    return None\nreturn data[0]['value'] / value"
            }
        ],
        "explanation": "通过添加检查防止除以零错误",
        "prevention_tips": ["始终验证除数", "使用try-except处理异常"]
    }
    
    # 测试解决方案格式化
    formatted = ResultFormatter.format_solution(solution)
    assert "解决方案" in formatted
    assert "摘要" in formatted
    assert "添加除数检查和错误处理" in formatted
    assert "修复步骤" in formatted
    assert "代码修改" in formatted
    assert "原始代码" in formatted
    assert "修改后代码" in formatted
    
    # 测试相似bug格式化
    similar_bugs = [
        {
            "title": "处理零除错误",
            "description": "函数在处理数据时未检查除数是否为零",
            "solution": "添加检查逻辑防止除以零",
            "similarity": 0.95
        },
        {
            "title": "数据验证问题",
            "description": "输入数据未经过验证导致错误",
            "solution": "添加数据验证步骤",
            "similarity": 0.85
        }
    ]
    
    formatted = ResultFormatter.format_similar_bugs(similar_bugs)
    assert "相似Bug记录" in formatted
    assert "处理零除错误" in formatted
    assert "数据验证问题" in formatted
    assert "相似度" in formatted
    
    # 测试完整结果格式化
    full_result = {
        "analyses": {
            "error_analysis": {"error_analysis": error_analysis},
            "code_analysis": {"code_analysis": code_analysis},
            "root_cause": {"root_cause_analysis": root_cause},
            "solution": {"solution": solution}
        },
        "similar_bugs": similar_bugs
    }
    
    formatted = ResultFormatter.format_full_result(full_result)
    assert "AI DEBUG 分析报告" in formatted
    assert "根因分析" in formatted
    assert "解决方案" in formatted
    assert "错误分析" in formatted
    assert "代码分析" in formatted
    assert "相似Bug记录" in formatted


def test_html_formatter():
    """测试HTML格式化器"""
    # 使用上面测试中的样例数据
    result = {
        "analyses": {
            "root_cause": {
                "root_cause_analysis": {
                    "root_cause": "测试根因",
                    "explanation": "测试解释",
                    "confidence_level": 8,
                    "related_factors": ["因素1", "因素2"]
                }
            }
        }
    }
    
    html = HTMLFormatter.format_to_html(result)
    assert "<!DOCTYPE html>" in html
    assert "<html>" in html
    assert "测试根因" in html
    assert "测试解释" in html


def test_json_formatter():
    """测试JSON格式化器"""
    result = {"test": "value", "nested": {"key": "value"}}
    
    json_str = JSONFormatter.format_to_json(result)
    assert isinstance(json_str, str)
    
    # 解析回JSON测试是否正确
    parsed = json.loads(json_str)
    assert parsed["test"] == "value"
    assert parsed["nested"]["key"] == "value"


def test_interactive_components():
    """测试交互组件"""
    feedback_html = InteractiveComponents.generate_feedback_html()
    assert "<div class=\"feedback-container\">" in feedback_html
    assert "请评价此分析结果" in feedback_html
    
    follow_up_html = InteractiveComponents.generate_follow_up_html()
    assert "<div class=\"follow-up-container\">" in follow_up_html
    assert "后续问题" in follow_up_html


def test_output_manager():
    """测试输出管理器"""
    manager = OutputManager()
    
    result = {
        "analyses": {
            "root_cause": {
                "root_cause_analysis": {
                    "root_cause": "测试根因",
                    "explanation": "测试解释",
                    "confidence_level": 8,
                    "related_factors": ["因素1", "因素2"]
                }
            }
        }
    }
    
    # 测试不同格式的输出
    markdown = manager.format_result(result, "markdown")
    assert "# AI DEBUG 分析报告" in markdown
    assert "## 根因分析" in markdown
    
    html = manager.format_result(result, "html")
    assert "<!DOCTYPE html>" in html
    assert "AI DEBUG 分析报告" in html
    
    json_output = manager.format_result(result, "json")
    assert "\"root_cause\":" in json_output
    
    # 测试不支持的格式
    unsupported = manager.format_result(result, "unsupported")
    assert "不支持的输出格式" in unsupported


def test_format_result_function():
    """测试格式化结果便捷函数"""
    result = {
        "analyses": {
            "root_cause": {
                "root_cause_analysis": {
                    "root_cause": "测试根因",
                    "explanation": "测试解释"
                }
            }
        }
    }
    
    formatted = format_result(result, "markdown")
    assert "# AI DEBUG 分析报告" in formatted
    assert "测试根因" in formatted
