"""LLM分析引擎测试模块"""

import unittest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径，以便导入项目模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 从llm_engine模块导入需要测试的类和函数
from src.llm_engine import (
    LLMClient,
    ErrorMessageParser, 
    CodeAnalyzer, 
    ProblemCauseInferenceModule, 
    FixSuggestionGenerator,
    AnalysisEngine,
    analyze
)

# 从providers模块导入LLM提供者类
from src.llm_engine.providers import (
    LLMProvider,
    OpenAIProvider,
    AzureOpenAIProvider,
    AnthropicProvider,
    create_llm_provider
)


class TestLLMProviders(unittest.TestCase):
    """测试LLM提供者"""
    
    @patch('src.llm_engine.providers.OPENAI_SDK_AVAILABLE', False)
    @patch('src.llm_engine.providers.requests.post')
    def test_openai_provider(self, mock_post, mock_sdk):
        """测试OpenAI提供者"""
        # 模拟API返回
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "测试回复"}}]
        }
        mock_post.return_value = mock_response
        
        # 创建提供者并调用方法
        provider = OpenAIProvider(api_key="test_key")
        self.assertEqual(provider._implementation, "requests")  # 确认使用requests实现
        result = provider.generate_text("测试提示")
        
        # 验证结果
        self.assertEqual(result, "测试回复")
        mock_post.assert_called_once()
    
    @patch('src.llm_engine.providers.OPENAI_SDK_AVAILABLE', False)
    @patch('src.llm_engine.providers.requests.post')
    def test_azure_provider(self, mock_post, mock_sdk):
        """测试Azure OpenAI提供者"""
        # 模拟API返回
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "测试回复"}}]
        }
        mock_post.return_value = mock_response
        
        # 创建提供者并调用方法
        provider = AzureOpenAIProvider(
            api_key="test_key", 
            endpoint="https://test.openai.azure.com", 
            deployment_name="test-deployment"
        )
        self.assertEqual(provider._implementation, "requests")  # 确认使用requests实现
        result = provider.generate_text("测试提示")
        
        # 验证结果
        self.assertEqual(result, "测试回复")
        mock_post.assert_called_once()
    
    @patch('src.llm_engine.providers.OPENAI_SDK_AVAILABLE', False)
    @patch('src.llm_engine.providers.requests.post')
    def test_anthropic_provider(self, mock_post, mock_sdk):
        """测试Anthropic提供者"""
        # 模拟API返回
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "测试回复"}]
        }
        mock_post.return_value = mock_response
        
        # 创建提供者并调用方法
        provider = AnthropicProvider(api_key="test_key")
        self.assertEqual(provider._implementation, "requests")  # 确认使用requests实现
        result = provider.generate_text("测试提示")
        
        # 验证结果
        self.assertEqual(result, "测试回复")
        mock_post.assert_called_once()


class TestLLMClient(unittest.TestCase):
    """测试LLM客户端"""
    
    @patch('src.llm_engine.providers.create_llm_provider')
    def test_generate(self, mock_create_provider):
        """测试生成方法"""
        # 模拟提供者
        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider.generate_text.return_value = "测试回复"
        mock_create_provider.return_value = mock_provider
        
        # 创建客户端并调用方法
        client = LLMClient()
        result = client.generate("测试提示")
        
        # 验证结果
        self.assertEqual(result, "测试回复")
        mock_provider.generate_text.assert_called_once()


class TestErrorMessageParser(unittest.TestCase):
    """测试错误信息解析器"""
    
    @patch('src.llm_engine.LLMClient.generate_with_retry')
    def test_parse_error(self, mock_generate):
        """测试错误解析"""
        # 模拟LLM返回
        mock_generate.return_value = json.dumps({
            "root_cause_summary": "测试根因",
            "severity": "中",
            "affected_components": ["测试组件"],
            "common_triggers": ["测试触发"],
            "environmental_factors": ["测试环境"],
            "relevant_variables": ["测试变量"]
        })
        
        # 创建解析器并调用方法
        parser = ErrorMessageParser()
        result = parser.parse_error({
            "raw_content": "TypeError: Cannot read property 'x' of undefined"
        })
        
        # 验证结果
        self.assertIn("parsed_error", result)
        self.assertEqual(result["parsed_error"]["root_cause_summary"], "测试根因")
        self.assertEqual(result["parsed_error"]["severity"], "中")
        mock_generate.assert_called_once()


class TestCodeAnalyzer(unittest.TestCase):
    """测试代码分析器"""
    
    @patch('src.llm_engine.LLMClient.generate_with_retry')
    def test_analyze_code(self, mock_generate):
        """测试代码分析"""
        # 模拟语法分析返回
        mock_generate.side_effect = [
            # 语法分析返回
            json.dumps({
                "syntax_issues": [],
                "code_structure": {
                    "complexity_score": 3,
                    "main_components": ["测试组件"],
                    "structure_quality": "良好",
                    "structure_issues": []
                },
                "style_consistency": {
                    "naming_convention": "一致",
                    "indentation": "一致",
                    "comment_quality": "良好"
                }
            }),
            # 语义分析返回
            json.dumps({
                "logic_analysis": {
                    "purpose": "测试目的",
                    "logic_flow": "测试流程",
                    "edge_cases": [],
                    "logic_issues": []
                },
                "potential_bugs": [{
                    "bug_type": "空值检查缺失",
                    "description": "可能会导致空引用异常",
                    "likely_outcome": "程序崩溃",
                    "fix_suggestion": "添加非空检查"
                }],
                "performance_issues": [],
                "security_concerns": []
            })
        ]
        
        # 创建分析器并调用方法
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_code({
            "raw_content": "function test() { return data.value; }",
            "language": "javascript"
        })
        
        # 验证结果
        self.assertIn("code_analysis", result)
        code_analysis = result["code_analysis"]
        self.assertIn("code_quality", code_analysis)
        self.assertIn("potential_bugs", code_analysis)
        self.assertEqual(len(code_analysis["potential_bugs"]), 1)
        self.assertEqual(code_analysis["potential_bugs"][0]["bug_type"], "空值检查缺失")
        
        # 验证调用次数
        self.assertEqual(mock_generate.call_count, 2)


class TestProblemCauseInferenceModule(unittest.TestCase):
    """测试问题原因推理模块"""
    
    @patch('src.llm_engine.LLMClient.generate_with_retry')
    def test_analyze_root_cause(self, mock_generate):
        """测试根因分析"""
        # 模拟LLM返回
        mock_generate.return_value = json.dumps({
            "root_cause": "未检查输入值是否为null",
            "causal_chain": ["用户输入为空", "未进行空值检查", "引发空引用异常"],
            "explanation": "函数没有验证输入参数，导致在处理空值时抛出异常",
            "affected_components": ["数据验证层", "用户输入处理"],
            "evidence": ["错误显示空引用", "代码中缺少条件判断"],
            "confidence_level": 8,
            "confidence_explanation": "错误模式与典型的空引用问题匹配"
        })
        
        # 创建模块并调用方法
        inference = ProblemCauseInferenceModule()
        result = inference.analyze_root_cause({
            "inputs": {
                "error_message": {
                    "raw_content": "TypeError: Cannot read property 'x' of undefined"
                },
                "code_snippet": {
                    "raw_content": "function test(data) { return data.value; }",
                    "language": "javascript"
                }
            }
        })
        
        # 验证结果
        self.assertIn("root_cause_analysis", result)
        analysis = result["root_cause_analysis"]
        self.assertEqual(analysis["root_cause"], "未检查输入值是否为null")
        self.assertEqual(analysis["problem_type"], "数据问题")  # 应该基于根因自动确定问题类型
        self.assertEqual(len(analysis["causal_chain"]), 3)
        
        # 验证调用次数
        mock_generate.assert_called_once()


class TestFixSuggestionGenerator(unittest.TestCase):
    """测试修复建议生成器"""
    
    @patch('src.llm_engine.LLMClient.generate_with_retry')
    def test_generate_solution(self, mock_generate):
        """测试解决方案生成"""
        # 模拟LLM返回
        mock_generate.return_value = json.dumps({
            "solution_summary": "添加输入参数的空值检查",
            "fix_steps": [
                "在函数开头添加参数验证",
                "添加错误处理逻辑",
                "提供有意义的错误消息"
            ],
            "code_changes": [{
                "file": "main.js",
                "original_code": "function test(data) { return data.value; }",
                "fixed_code": "function test(data) { if (!data) throw new Error('数据不能为空'); return data.value; }",
                "explanation": "添加参数非空检查，避免空引用异常"
            }],
            "explanation": "通过添加输入验证防止空引用错误",
            "prevention_tips": [
                "始终验证函数输入",
                "使用防御性编程技术",
                "添加适当的错误处理"
            ],
            "alternative_solutions": [
                "使用可选链操作符 ?.",
                "使用默认值模式",
                "使用专门的验证库"
            ]
        })
        
        # 创建生成器并调用方法
        generator = FixSuggestionGenerator()
        result = generator.generate_solution(
            {
                "inputs": {
                    "error_message": {
                        "raw_content": "TypeError: Cannot read property 'value' of undefined"
                    },
                    "code_snippet": {
                        "raw_content": "function test(data) { return data.value; }",
                        "language": "javascript"
                    }
                }
            },
            {
                "root_cause": "未检查输入值是否为null",
                "problem_type": "数据问题",
                "explanation": "函数没有验证输入参数，导致在处理空值时抛出异常"
            }
        )
        
        # 验证结果
        self.assertIn("solution", result)
        solution = result["solution"]
        self.assertEqual(solution["solution_summary"], "添加输入参数的空值检查")
        self.assertEqual(len(solution["fix_steps"]), 3)
        self.assertEqual(len(solution["code_changes"]), 1)
        self.assertEqual(len(solution["prevention_tips"]), 3)
        
        # 验证调用次数
        mock_generate.assert_called_once()


class TestAnalysisEngine(unittest.TestCase):
    """测试分析引擎"""
    
    @patch('src.llm_engine.ErrorMessageParser.parse_error')
    @patch('src.llm_engine.CodeAnalyzer.analyze_code')
    @patch('src.llm_engine.ProblemCauseInferenceModule.analyze_root_cause')
    @patch('src.llm_engine.FixSuggestionGenerator.generate_solution')
    def test_analyze(self, mock_generate_solution, mock_analyze_root_cause, 
                   mock_analyze_code, mock_parse_error):
        """测试整体分析流程"""
        # 模拟各组件返回
        mock_parse_error.return_value = {"parsed_error": {"error_type": "TypeError", "error_language": "javascript"}}
        mock_analyze_code.return_value = {"code_analysis": {"potential_bugs": [{"bug_type": "空值检查缺失"}]}}
        mock_analyze_root_cause.return_value = {"root_cause_analysis": {"root_cause": "未检查空值"}}
        mock_generate_solution.return_value = {"solution": {"solution_summary": "添加空值检查"}}
        
        # 创建引擎并调用方法
        engine = AnalysisEngine()
        result = engine.analyze({
            "inputs": {
                "error_message": {
                    "raw_content": "TypeError: Cannot read property 'value' of undefined"
                },
                "code_snippet": {
                    "raw_content": "function test(data) { return data.value; }",
                    "language": "javascript"
                }
            }
        })
        
        # 验证结果
        self.assertIn("analyses", result)
        self.assertIn("error_analysis", result["analyses"])
        self.assertIn("code_analysis", result["analyses"])
        self.assertIn("root_cause", result["analyses"])
        self.assertIn("solution", result["analyses"])
        self.assertIn("summary", result)
        
        # 验证调用次数
        mock_parse_error.assert_called_once()
        mock_analyze_code.assert_called_once()
        mock_analyze_root_cause.assert_called_once()
        mock_generate_solution.assert_called_once()


if __name__ == '__main__':
    unittest.main()
