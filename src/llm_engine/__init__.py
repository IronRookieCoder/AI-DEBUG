"""LLM分析引擎模块，负责模拟资深工程师思路进行代码和错误分析"""

import json
import os
import re
import time
import datetime
import traceback
import logging
import requests
from typing import Dict, Any, List, Optional, Tuple, Union
from abc import ABC, abstractmethod

# 从providers模块导入LLM提供者实现
from .providers import (
    LLMProvider, OpenAIProvider, AzureOpenAIProvider, 
    AnthropicProvider, create_llm_provider, OPENAI_SDK_AVAILABLE
)

# 尝试导入httpx库以支持AnthropicProvider
try:
    import httpx
except ImportError:
    pass

try:
    from openai import OpenAI, AzureOpenAI
except ImportError:
    pass

from ..config import get_config

# 配置日志
logger = logging.getLogger(__name__)


class LLMClient:
    """LLM客户端，负责与LLM API通信"""
    
    def __init__(self):
        """初始化LLM客户端"""
        self.config = get_config("llm")
        self.provider_type = self.config.get("provider", "openai")
        provider_config = {
            "api_key": self.config.get("api_key", os.environ.get("LLM_API_KEY", "")),
            "model": self.config.get("model", "gpt-4"),
            "temperature": self.config.get("temperature", 0.3),
            "max_tokens": self.config.get("max_tokens", 2000),
            "endpoint": self.config.get("endpoint", os.environ.get("LLM_ENDPOINT", "")),
            "deployment_name": self.config.get("deployment_name", "")
        }
        self.provider = create_llm_provider(self.provider_type, provider_config)
        
        if not self.provider:
            logger.warning(f"无法创建LLM提供者实例，将使用OpenAI作为默认提供者")
            self.provider = OpenAIProvider(
                api_key=provider_config["api_key"],
                model=provider_config["model"],
                temperature=provider_config["temperature"],
                max_tokens=provider_config["max_tokens"]
            )
    
    def generate(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """
        调用LLM生成内容
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            
        Returns:
            生成的文本，失败时返回None
        """
        if not self.provider:
            logger.error("LLM提供者未初始化")
            return None
        
        return self.provider.generate_text(prompt, system_prompt)
    
    def generate_with_retry(self, prompt: str, system_prompt: str = None, max_retries: int = 2) -> Optional[str]:
        """
        带重试的LLM调用
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            max_retries: 最大重试次数
            
        Returns:
            生成的文本，所有重试都失败时返回None
        """
        for attempt in range(max_retries + 1):
            result = self.generate(prompt, system_prompt)
            if result:
                return result
            logger.warning(f"LLM调用失败，正在重试 ({attempt+1}/{max_retries+1})")
        
        logger.error(f"所有LLM调用尝试均失败")
        return None


class ErrorMessageParser:
    """
    错误信息解析模块，负责解析错误信息，提取关键信息
    
    模拟资深工程师如何分析错误信息：
    1. 首先识别错误类型和严重程度
    2. 分析错误发生的位置和调用堆栈
    3. 提取关键的错误描述和参数
    4. 将非结构化的错误信息转换为结构化格式
    """
    
    def __init__(self):
        """初始化错误信息解析器"""
        self.llm_client = LLMClient()
        # 常见错误类型的正则表达式模式
        self.error_patterns = {
            "python": {
                "syntax": r"SyntaxError",
                "type": r"TypeError",
                "name": r"NameError",
                "attribute": r"AttributeError",
                "index": r"IndexError",
                "key": r"KeyError",
                "value": r"ValueError",
                "import": r"ImportError",
                "zero_division": r"ZeroDivisionError",
                "assertion": r"AssertionError",
                "runtime": r"RuntimeError",
                "indentation": r"IndentationError"
            },
            "javascript": {
                "syntax": r"SyntaxError",
                "type": r"TypeError",
                "reference": r"ReferenceError",
                "range": r"RangeError",
                "uri": r"URIError",
                "eval": r"EvalError",
                "internal": r"InternalError"
            },
            "java": {
                "null_pointer": r"NullPointerException",
                "class_cast": r"ClassCastException",
                "index_out_of_bounds": r"IndexOutOfBoundsException",
                "arithmetic": r"ArithmeticException",
                "illegal_argument": r"IllegalArgumentException",
                "io": r"IOException"
            }
        }
    
    def parse_error(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析错误信息，提取关键信息
        
        Args:
            error_info: 输入层处理后的错误信息
            
        Returns:
            解析后的错误信息
        """
        raw_error = error_info.get("raw_content", "")
        
        # 1. 预处理：使用规则进行基本解析
        basic_parsed = self._rule_based_parsing(raw_error)
        
        # 2. 使用LLM进行深入分析
        llm_parsed = self._llm_based_parsing(raw_error, basic_parsed)
        
        # 3. 合并结果
        result = {**basic_parsed, **llm_parsed}
        
        return {
            "parsed_error": result
        }
    
    def _rule_based_parsing(self, raw_error: str) -> Dict[str, Any]:
        """
        基于规则的错误信息解析
        
        Args:
            raw_error: 原始错误信息
            
        Returns:
            基础解析结果
        """
        result = {
            "error_type": "未知",
            "error_language": "未知",
            "stack_trace": [],
            "error_location": {},
            "error_message": raw_error
        }
        
        # 尝试提取错误类型
        for language, patterns in self.error_patterns.items():
            for error_type, pattern in patterns.items():
                if re.search(pattern, raw_error):
                    result["error_type"] = error_type
                    result["error_language"] = language
                    break
            if result["error_type"] != "未知":
                break
        
        # 尝试提取Python堆栈跟踪
        if "Traceback (most recent call last)" in raw_error:
            result["error_language"] = "python"
            stack_trace = []
            
            # 提取堆栈
            stack_lines = re.findall(r'File "([^"]+)", line (\d+), in (\S+)', raw_error)
            for file_path, line_num, function in stack_lines:
                stack_trace.append({
                    "file": file_path,
                    "line": int(line_num),
                    "function": function
                })
            
            result["stack_trace"] = stack_trace
            
            # 提取最后一行的错误类型和消息
            error_match = re.search(r'([A-Za-z0-9_]+Error): (.+)$', raw_error, re.MULTILINE)
            if error_match:
                result["error_type"] = error_match.group(1)
                result["error_message"] = error_match.group(2)
            
            # 提取最后一个错误位置作为主要位置
            if stack_trace:
                result["error_location"] = stack_trace[-1]
        
        # 尝试提取JavaScript堆栈跟踪
        elif "at " in raw_error and ("TypeError" in raw_error or "ReferenceError" in raw_error):
            result["error_language"] = "javascript"
            stack_trace = []
            
            # 提取错误类型和消息
            error_match = re.search(r'([A-Za-z0-9_]+Error):?\s*(.+?)(?:\n|$)', raw_error)
            if error_match:
                result["error_type"] = error_match.group(1)
                result["error_message"] = error_match.group(2).strip()
            
            # 提取堆栈
            stack_lines = re.findall(r'at (?:(\S+) \(([^:]+):(\d+):(\d+)\)|([^:]+):(\d+):(\d+))', raw_error)
            for line in stack_lines:
                if line[0]:  # 包含函数名的格式
                    stack_trace.append({
                        "function": line[0],
                        "file": line[1],
                        "line": int(line[2]),
                        "column": int(line[3])
                    })
                else:  # 不包含函数名的格式
                    stack_trace.append({
                        "file": line[4],
                        "line": int(line[5]),
                        "column": int(line[6])
                    })
            
            result["stack_trace"] = stack_trace
            
            # 提取第一个错误位置作为主要位置
            if stack_trace:
                result["error_location"] = stack_trace[0]
        
        return result
    
    def _llm_based_parsing(self, raw_error: str, basic_parsed: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于LLM的深入错误分析
        
        Args:
            raw_error: 原始错误信息
            basic_parsed: 基础解析结果
            
        Returns:
            LLM分析结果
        """
        # 构建提示词
        system_prompt = """你是一个专业的错误信息分析专家。请分析提供的错误信息，提取关键信息并解构错误。
        你需要分析：
        1. 错误的根本原因
        2. 错误严重程度（致命、严重、警告、轻微）
        3. 错误可能的环境和前提条件
        4. 相关的变量或参数值
        5. 此类错误的常见触发场景
        
        请以JSON格式返回结果，包含以下字段：
        {
          "root_cause_summary": "简短的根本原因描述",
          "severity": "错误严重程度",
          "affected_components": ["受影响的组件列表"],
          "common_triggers": ["常见触发场景列表"],
          "environmental_factors": ["可能的环境因素列表"],
          "relevant_variables": ["相关变量或参数"]
        }
        """
        
        # 构建错误信息提示
        prompt = f"""请分析以下错误信息，提取关键信息并提供深入分析：
        
        ```
        {raw_error}
        ```
        
        已知的基本信息：
        - 错误类型: {basic_parsed["error_type"]}
        - 错误语言: {basic_parsed["error_language"]}
        - 错误位置: {json.dumps(basic_parsed["error_location"], ensure_ascii=False)}
        """
        
        # 调用LLM
        analysis_text = self.llm_client.generate_with_retry(prompt, system_prompt)
        
        # 解析结果
        try:
            if analysis_text:
                analysis = json.loads(analysis_text)
                return analysis
            else:
                logger.warning("LLM未返回有效结果")
                return {}
        except json.JSONDecodeError:
            logger.warning("无法解析LLM返回的JSON")
            return {
                "root_cause_summary": "未能自动解析",
                "severity": "未知",
                "affected_components": [],
                "common_triggers": [],
                "environmental_factors": [],
                "relevant_variables": [],
                "raw_analysis": analysis_text
            }


class CodeAnalyzer:
    """
    代码分析器，负责分析代码语义和识别潜在缺陷
    模拟资深工程师如何分析代码：
    1. 理解代码意图和整体结构
    2. 检查代码语法和逻辑错误
    3. 评估代码质量和最佳实践
    4. 识别性能瓶颈和优化机会
    5. 发现安全漏洞和风险点
    6. 提供具体改进建议
    """
    
    def __init__(self):
        """初始化代码分析器"""
        self.llm_client = LLMClient()
        
        # 代码质量评估标准
        self.quality_metrics = [
            "可读性", "可维护性", "模块化", "复杂度", "命名规范",
            "注释完整性", "异常处理", "测试覆盖率"
        ]
        
        # 不同语言的常见bug模式
        self.common_bug_patterns = {
            "python": [
                "空引用", "类型错误", "索引越界", "字典键错误", "循环条件错误",
                "无效参数", "未初始化变量", "资源泄漏", "文件读写错误"
            ],
            "javascript": [
                "undefined行为", "类型转换错误", "闭包问题", "异步错误",
                "DOM操作错误", "事件处理问题", "跨域问题"
            ],
            "java": [
                "空指针异常", "类型转换异常", "并发问题", "内存泄漏", 
                "资源未关闭", "IO异常处理"
            ]
        }
    
    def analyze_code(self, code_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析代码
        
        Args:
            code_info: 输入层处理后的代码信息
            
        Returns:
            代码分析结果
        """
        code_raw = code_info.get("raw_content", "")
        language = code_info.get("language", "未知语言").lower()
        filename = code_info.get("filename", "")
        context = code_info.get("context", "")
        
        # 获取语言特定的代码分析策略
        analysis_strategy = self._get_language_specific_analysis(language)
        
        # 第一步：基本代码结构和语法分析
        syntax_analysis = self._analyze_syntax(code_raw, language)
        
        # 第二步：深度语义分析
        semantic_analysis = self._analyze_semantics(code_raw, language, filename, context)
        
        # 第三步：组合分析结果
        combined_analysis = self._combine_analysis_results(syntax_analysis, semantic_analysis, language)
        
        return {
            "code_analysis": combined_analysis
        }
    
    def _get_language_specific_analysis(self, language: str) -> Dict[str, Any]:
        """获取特定语言的分析策略"""
        # 语言特定的分析配置
        default_strategy = {
            "complexity_threshold": 10,  # 默认复杂度阈值
            "max_function_lines": 50,    # 函数最大行数
            "common_bugs": self.common_bug_patterns.get(language, []),
            "quality_focus": self.quality_metrics,
            "performance_patterns": []
        }
        
        strategies = {
            "python": {
                **default_strategy,
                "performance_patterns": [
                    "列表推导式", "生成器表达式", "GIL限制", "不必要的全局变量",
                    "循环中的不必要操作", "重复字符串连接"
                ],
                "security_patterns": [
                    "SQL注入", "命令注入", "不安全的反序列化", "硬编码凭证"
                ]
            },
            "javascript": {
                **default_strategy,
                "performance_patterns": [
                    "DOM操作频繁", "事件监听器未移除", "闭包内存泄漏",
                    "不必要的重渲染", "大文件加载"
                ],
                "security_patterns": [
                    "XSS漏洞", "CSRF漏洞", "不安全的JSON解析", "敏感数据暴露"
                ]
            },
            "java": {
                **default_strategy,
                "performance_patterns": [
                    "线程池使用", "字符串连接", "IO操作优化", "集合选择不当",
                    "对象创建过多"
                ],
                "security_patterns": [
                    "不安全的反序列化", "权限检查缺失", "硬编码凭证", "敏感数据日志记录"
                ]
            }
        }
        
        return strategies.get(language, default_strategy)
    
    def _analyze_syntax(self, code: str, language: str) -> Dict[str, Any]:
        """
        基本语法分析
        
        Args:
            code: 代码内容
            language: 代码语言
            
        Returns:
            语法分析结果
        """
        system_prompt = f"""你是一位资深{language}开发专家。请对以下代码进行基本的语法和结构分析，
        识别可能的语法错误、结构问题和风格不一致。请注意这只是初步分析，不需要深入语义。
        
        返回JSON格式结果，包含以下字段：
        {{
          "syntax_issues": [
            {{
              "issue_type": "语法问题类型",
              "description": "详细描述",
              "severity": "高/中/低",
              "line_reference": "相关行号或代码片段"
            }}
          ],
          "code_structure": {{
            "complexity_score": 1-10的数值,
            "main_components": ["主要组件列表"],
            "structure_quality": "良好/一般/较差",
            "structure_issues": ["结构问题列表"]
          }},
          "style_consistency": {{
            "naming_convention": "一致/不一致",
            "indentation": "一致/不一致",
            "comment_quality": "良好/一般/缺乏"
          }}
        }}"""
        
        prompt = f"""请分析以下{language}代码的语法和结构：
        
        ```{language}
        {code}
        ```
        
        请提供语法问题、代码结构评估和代码风格一致性分析。"""
        
        # 调用LLM分析
        analysis_text = self.llm_client.generate_with_retry(prompt, system_prompt)
        
        # 解析分析结果
        try:
            return json.loads(analysis_text)
        except json.JSONDecodeError:
            logger.warning("无法解析语法分析的JSON结果")
            return {
                "syntax_issues": [],
                "code_structure": {
                    "complexity_score": 5,
                    "main_components": [],
                    "structure_quality": "无法评估",
                    "structure_issues": []
                },
                "style_consistency": {
                    "naming_convention": "无法评估",
                    "indentation": "无法评估",
                    "comment_quality": "无法评估"
                },
                "raw_analysis": analysis_text
            }
    
    def _analyze_semantics(self, code: str, language: str, filename: str, context: str) -> Dict[str, Any]:
        """
        深度语义分析
        
        Args:
            code: 代码内容
            language: 代码语言
            filename: 文件名
            context: 上下文信息
            
        Returns:
            语义分析结果
        """
        system_prompt = f"""你是一位精通{language}的资深软件架构师。请对以下代码进行深入的语义分析，
        评估代码逻辑、可能的bug、性能问题和安全隐患。请考虑代码的上下文和文件名提供的信息。
        
        返回JSON格式结果，包含以下字段：
        {{
          "logic_analysis": {{
            "purpose": "代码目的描述",
            "logic_flow": "逻辑流程描述",
            "edge_cases": ["未处理的边缘情况列表"],
            "logic_issues": [
              {{
                "issue": "逻辑问题描述",
                "impact": "影响",
                "severity": "高/中/低"
              }}
            ]
          }},
          "potential_bugs": [
            {{
              "bug_type": "bug类型",
              "description": "描述",
              "likely_outcome": "可能导致的结果",
              "fix_suggestion": "修复建议"
            }}
          ],
          "performance_issues": [
            {{
              "issue": "性能问题描述",
              "impact": "影响",
              "optimization": "优化建议"
            }}
          ],
          "security_concerns": [
            {{
              "vulnerability": "安全漏洞类型",
              "description": "描述",
              "severity": "高/中/低",
              "mitigation": "缓解措施"
            }}
          ]
        }}"""
        
        # 构建上下文提示
        context_info = ""
        if context:
            context_info = f"\n代码上下文：\n{context}"
        
        if filename:
            context_info += f"\n文件名：{filename}"
        
        prompt = f"""请对以下{language}代码进行深入的语义分析：
        
        ```{language}
        {code}
        ```{context_info}
        
        请分析代码逻辑、潜在bug、性能问题和安全隐患。考虑代码意图、可能的边缘情况和执行路径。"""
        
        # 调用LLM分析
        analysis_text = self.llm_client.generate_with_retry(prompt, system_prompt)
        
        # 解析分析结果
        try:
            return json.loads(analysis_text)
        except json.JSONDecodeError:
            logger.warning("无法解析语义分析的JSON结果")
            return {
                "logic_analysis": {
                    "purpose": "无法确定",
                    "logic_flow": "无法分析",
                    "edge_cases": [],
                    "logic_issues": []
                },
                "potential_bugs": [],
                "performance_issues": [],
                "security_concerns": [],
                "raw_analysis": analysis_text
            }
    
    def _combine_analysis_results(self, syntax_analysis: Dict[str, Any], 
                                semantic_analysis: Dict[str, Any],
                                language: str) -> Dict[str, Any]:
        """
        组合不同层次的分析结果
        
        Args:
            syntax_analysis: 语法分析结果
            semantic_analysis: 语义分析结果
            language: 代码语言
            
        Returns:
            综合分析结果
        """
        # 评估代码质量
        code_quality_score = self._evaluate_code_quality(syntax_analysis, semantic_analysis)
        
        # 构造综合结果
        result = {
            "code_quality": {
                "overall_score": code_quality_score,
                "summary": self._generate_quality_summary(code_quality_score),
                "strengths": self._identify_code_strengths(syntax_analysis, semantic_analysis),
                "weaknesses": self._identify_code_weaknesses(syntax_analysis, semantic_analysis)
            },
            "potential_bugs": semantic_analysis.get("potential_bugs", []),
            "performance_issues": semantic_analysis.get("performance_issues", []),
            "security_concerns": semantic_analysis.get("security_concerns", []),
            "improvement_suggestions": self._generate_improvement_suggestions(
                syntax_analysis, semantic_analysis, language
            )
        }
        
        return result
    
    def _evaluate_code_quality(self, syntax_analysis: Dict[str, Any], 
                             semantic_analysis: Dict[str, Any]) -> int:
        """评估代码质量得分（1-10）"""
        # 初始分数为中等
        score = 5
        
        # 基于语法分析调整分数
        structure = syntax_analysis.get("code_structure", {})
        complexity_score = structure.get("complexity_score", 5)
        structure_quality = structure.get("structure_quality", "一般")
        style = syntax_analysis.get("style_consistency", {})
        
        # 基于复杂度调整（复杂度越高，得分越低）
        score -= (complexity_score - 5) * 0.3
        
        # 基于结构质量调整
        if structure_quality == "良好":
            score += 1
        elif structure_quality == "较差":
            score -= 1
        
        # 基于代码风格调整
        if style.get("naming_convention") == "一致":
            score += 0.5
        if style.get("indentation") == "一致":
            score += 0.5
        if style.get("comment_quality") == "良好":
            score += 0.5
        
        # 基于语义分析调整分数
        logic_issues = semantic_analysis.get("logic_analysis", {}).get("logic_issues", [])
        bugs = semantic_analysis.get("potential_bugs", [])
        security = semantic_analysis.get("security_concerns", [])
        
        # 严重问题数量
        severe_issues = sum(1 for issue in logic_issues if issue.get("severity") == "高")
        severe_issues += sum(1 for issue in security if issue.get("severity") == "高")
        
        # 基于严重问题数量调整
        score -= severe_issues * 0.8
        
        # 基于总体问题数量调整分数
        total_issues = len(logic_issues) + len(bugs) + len(security)
        score -= total_issues * 0.2
        
        # 确保分数在1-10之间
        return max(1, min(10, round(score)))
    
    def _generate_quality_summary(self, score: int) -> str:
        """基于分数生成质量概述"""
        if score >= 8:
            return "代码质量优秀，结构清晰，符合最佳实践。"
        elif score >= 6:
            return "代码质量良好，有少量可改进之处。"
        elif score >= 4:
            return "代码质量一般，存在多处需要改进的地方。"
        else:
            return "代码质量较差，需要进行大量重构。"
    
    def _identify_code_strengths(self, syntax_analysis: Dict[str, Any], 
                               semantic_analysis: Dict[str, Any]) -> List[str]:
        """识别代码的优点"""
        strengths = []
        
        # 从语法分析中提取优点
        structure = syntax_analysis.get("code_structure", {})
        style = syntax_analysis.get("style_consistency", {})
        
        if structure.get("complexity_score", 10) <= 5:
            strengths.append("代码复杂度适中")
        
        if structure.get("structure_quality") == "良好":
            strengths.append("代码结构清晰")
            
        if style.get("naming_convention") == "一致":
            strengths.append("命名规范统一")
            
        if style.get("comment_quality") == "良好":
            strengths.append("注释详细清晰")
            
        if style.get("indentation") == "一致":
            strengths.append("缩进格式一致")
        
        # 从语义分析中提取优点
        logic = semantic_analysis.get("logic_analysis", {})
        if logic.get("edge_cases", []) == []:
            strengths.append("考虑了边缘情况")
            
        if logic.get("logic_issues", []) == []:
            strengths.append("逻辑结构合理")
            
        # 如果没有找到优点，添加一个通用评价
        if not strengths:
            strengths.append("代码基本功能实现")
            
        return strengths
    
    def _identify_code_weaknesses(self, syntax_analysis: Dict[str, Any], 
                                semantic_analysis: Dict[str, Any]) -> List[str]:
        """识别代码的缺点"""
        weaknesses = []
        
        # 从语法分析中提取缺点
        structure = syntax_analysis.get("code_structure", {})
        style = syntax_analysis.get("style_consistency", {})
        
        if structure.get("complexity_score", 0) > 7:
            weaknesses.append("代码复杂度过高")
        
        if structure.get("structure_quality") == "较差":
            weaknesses.append("代码结构混乱")
            
        if style.get("naming_convention") == "不一致":
            weaknesses.append("命名规范不统一")
            
        if style.get("comment_quality") == "缺乏":
            weaknesses.append("注释不足")
            
        # 从语义分析中提取缺点
        logic = semantic_analysis.get("logic_analysis", {})
        bugs = semantic_analysis.get("potential_bugs", [])
        performance = semantic_analysis.get("performance_issues", [])
        security = semantic_analysis.get("security_concerns", [])
        
        if logic.get("edge_cases", []):
            weaknesses.append("未处理的边缘情况")
            
        if logic.get("logic_issues", []):
            weaknesses.append("存在逻辑问题")
            
        if bugs:
            weaknesses.append("存在潜在bug")
            
        if performance:
            weaknesses.append("存在性能问题")
            
        if security:
            weaknesses.append("存在安全隐患")
            
        return weaknesses
    
    def _generate_improvement_suggestions(self, syntax_analysis: Dict[str, Any], 
                                        semantic_analysis: Dict[str, Any],
                                        language: str) -> List[Dict[str, str]]:
        """生成改进建议"""
        suggestions = []
        
        # 收集各类问题
        syntax_issues = syntax_analysis.get("syntax_issues", [])
        structure_issues = syntax_analysis.get("code_structure", {}).get("structure_issues", [])
        logic_issues = semantic_analysis.get("logic_analysis", {}).get("logic_issues", [])
        bugs = semantic_analysis.get("potential_bugs", [])
        performance = semantic_analysis.get("performance_issues", [])
        security = semantic_analysis.get("security_concerns", [])
        
        # 为语法问题生成建议
        for issue in syntax_issues:
            suggestions.append({
                "area": "语法",
                "description": issue.get("description", ""),
                "suggestion": f"修复语法问题: {issue.get('description', '')}"
            })
        
        # 为结构问题生成建议
        for issue in structure_issues:
            suggestions.append({
                "area": "结构",
                "description": issue,
                "suggestion": f"改进代码结构: {issue}"
            })
        
        # 为逻辑问题生成建议
        for issue in logic_issues:
            suggestions.append({
                "area": "逻辑",
                "description": issue.get("issue", ""),
                "suggestion": f"修复逻辑问题: {issue.get('issue', '')}"
            })
        
        # 为潜在bug生成建议
        for bug in bugs:
            suggestions.append({
                "area": "Bug修复",
                "description": bug.get("description", ""),
                "suggestion": bug.get("fix_suggestion", f"修复潜在bug: {bug.get('description', '')}")
            })
        
        # 为性能问题生成建议
        for issue in performance:
            suggestions.append({
                "area": "性能优化",
                "description": issue.get("issue", ""),
                "suggestion": issue.get("optimization", f"优化性能: {issue.get('issue', '')}")
            })
        
        # 为安全问题生成建议
        for issue in security:
            suggestions.append({
                "area": "安全加固",
                "description": issue.get("description", ""),
                "suggestion": issue.get("mitigation", f"解决安全隐患: {issue.get('description', '')}")
            })
        
        # 添加语言特定的最佳实践建议
        language_specific_suggestions = self._get_language_specific_suggestions(language)
        suggestions.extend(language_specific_suggestions)
        
        # 限制建议数量，按优先级排序
        if len(suggestions) > 10:
            # 优先保留严重问题的建议
            security_suggestions = [s for s in suggestions if s["area"] == "安全加固"]
            bug_suggestions = [s for s in suggestions if s["area"] == "Bug修复"]
            other_suggestions = [s for s in suggestions 
                               if s["area"] not in ["安全加固", "Bug修复"]]
            
            # 按优先级组合
            suggestions = security_suggestions + bug_suggestions + other_suggestions[:max(0, 10 - len(security_suggestions) - len(bug_suggestions))]
        
        return suggestions
    
    def _get_language_specific_suggestions(self, language: str) -> List[Dict[str, str]]:
        """获取特定语言的最佳实践建议"""
        suggestions = []
        
        if language == "python":
            suggestions = [
                {
                    "area": "Python最佳实践",
                    "description": "使用列表推导式替代显式循环",
                    "suggestion": "考虑使用列表推导式以提高代码简洁性和性能"
                },
                {
                    "area": "Python最佳实践",
                    "description": "使用上下文管理器处理资源",
                    "suggestion": "使用 'with' 语句处理文件和资源，确保资源正确释放"
                }
            ]
        elif language == "javascript":
            suggestions = [
                {
                    "area": "JavaScript最佳实践",
                    "description": "使用现代ES6+特性",
                    "suggestion": "考虑使用箭头函数、解构赋值、模板字符串等现代JavaScript特性"
                },
                {
                    "area": "JavaScript最佳实践",
                    "description": "避免回调地狱",
                    "suggestion": "使用Promise或async/await代替多层嵌套回调"
                }
            ]
        elif language == "java":
            suggestions = [
                {
                    "area": "Java最佳实践",
                    "description": "使用Stream API处理集合",
                    "suggestion": "考虑使用Stream API简化集合操作并提高可读性"
                },
                {
                    "area": "Java最佳实践",
                    "description": "优化StringBuilder使用",
                    "suggestion": "字符串连接操作中使用StringBuilder替代+运算符"
                }
            ]
        
        return suggestions


class ProblemCauseInferenceModule:
    """
    问题原因推理模块，负责根因分析
    模拟资深工程师如何推理问题根因：
    1. 收集各种相关信息（错误信息、代码、日志等）
    2. 分析错误链和依赖关系
    3. 识别关键问题触发点
    4. 通过因果推理确定根本原因
    5. 评估可能的解决方案
    6. 提供详细的问题原因解释
    """
    
    def __init__(self):
        """初始化问题原因推理模块"""
        self.llm_client = LLMClient()
        
        # 常见问题模式库
        self.problem_patterns = {
            "data_issues": [
                "数据类型不匹配", "空值/空引用", "格式错误", "超出范围值",
                "未初始化", "被意外修改", "编码问题", "精度丢失"
            ],
            "logic_issues": [
                "条件判断错误", "边界条件处理", "算法实现错误", "状态管理错误",
                "异常流程未处理", "并发/竞态条件", "递归终止条件"
            ],
            "system_issues": [
                "资源不足", "权限问题", "配置错误", "依赖问题",
                "网络问题", "文件系统错误", "环境差异"
            ],
            "code_issues": [
                "语法错误", "库使用错误", "API误用", "版本不兼容",
                "内存管理错误", "命名冲突", "循环依赖"
            ]
        }
    
    def analyze_root_cause(self, input_data: Dict[str, Any], 
                          error_analysis: Dict[str, Any] = None,
                          code_analysis: Dict[str, Any] = None,
                          similar_bugs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        分析问题根因
        
        Args:
            input_data: 所有输入数据
            error_analysis: 错误分析结果
            code_analysis: 代码分析结果
            similar_bugs: 相似bug信息
            
        Returns:
            根因分析结果
        """
        # 1. 预处理和信息整合
        integrated_info = self._preprocess_information(input_data, error_analysis, code_analysis)
        
        # 2. 初步根因分类
        cause_categories = self._categorize_potential_causes(integrated_info)
        
        # 3. 深度根因分析
        root_cause = self._deep_causal_analysis(integrated_info, cause_categories, similar_bugs)
        
        # 4. 形成结论
        conclusion = self._form_conclusion(root_cause, input_data)
        
        return {
            "root_cause_analysis": conclusion
        }
    
    def _preprocess_information(self, input_data: Dict[str, Any], 
                              error_analysis: Dict[str, Any] = None,
                              code_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        预处理和整合信息
        
        Args:
            input_data: 所有输入数据
            error_analysis: 错误分析结果
            code_analysis: 代码分析结果
            
        Returns:
            整合后的信息
        """
        integrated_info = {
            "error_data": {},
            "code_data": {},
            "context_data": {},
            "log_data": {}
        }
        
        # 提取并整合错误信息
        if "error_message" in input_data.get("inputs", {}):
            error_raw = input_data["inputs"]["error_message"].get("raw_content", "")
            integrated_info["error_data"]["raw"] = error_raw
            
            # 如果有错误分析结果，整合它
            if error_analysis:
                integrated_info["error_data"]["analysis"] = error_analysis
        
        # 提取并整合代码信息
        if "code_snippet" in input_data.get("inputs", {}):
            code_raw = input_data["inputs"]["code_snippet"].get("raw_content", "")
            language = input_data["inputs"]["code_snippet"].get("language", "")
            integrated_info["code_data"]["raw"] = code_raw
            integrated_info["code_data"]["language"] = language
            
            # 如果有代码分析结果，整合它
            if code_analysis:
                integrated_info["code_data"]["analysis"] = code_analysis
        
        # 提取并整合问题描述
        if "problem_description" in input_data.get("inputs", {}):
            desc_raw = input_data["inputs"]["problem_description"].get("raw_content", "")
            integrated_info["context_data"]["problem_description"] = desc_raw
        
        # 提取并整合日志信息
        if "log_info" in input_data.get("inputs", {}):
            log_raw = input_data["inputs"]["log_info"].get("raw_content", "")
            integrated_info["log_data"]["raw"] = log_raw
            
            # 尝试从日志中提取关键信息
            integrated_info["log_data"]["key_events"] = self._extract_key_log_events(log_raw)
        
        return integrated_info
    
    def _extract_key_log_events(self, log_raw: str) -> List[Dict[str, str]]:
        """从日志中提取关键事件"""
        # 如果日志为空，返回空列表
        if not log_raw:
            return []
        
        # 使用LLM提取关键日志事件
        system_prompt = """你是一位专业的日志分析专家。请从提供的日志信息中提取关键事件，
        重点关注错误、警告和异常状况。以JSON数组格式返回结果，每个事件包含timestamp、level、
        message、component（如果有）字段。只提取与问题直接相关的关键事件，最多10个。"""
        
        prompt = f"""请从以下日志中提取关键事件，特别是与错误或异常相关的事件：
        
        ```
        {log_raw[:2000]}  # 限制长度以防止超出LLM上下文
        ```
        
        请以JSON格式返回关键事件列表。"""
        
        # 调用LLM分析
        analysis_text = self.llm_client.generate_with_retry(prompt, system_prompt)
        
        # 解析分析结果
        try:
            events = json.loads(analysis_text)
            return events
        except json.JSONDecodeError:
            logger.warning("无法解析日志事件的JSON结果")
            return []
    
    def _categorize_potential_causes(self, integrated_info: Dict[str, Any]) -> Dict[str, float]:
        """
        初步根因分类
        
        Args:
            integrated_info: 整合后的信息
            
        Returns:
            潜在原因分类及其概率
        """
        # 初始化各种原因类别的可能性分数
        categories = {
            "data_issues": 0.0,
            "logic_issues": 0.0,
            "system_issues": 0.0,
            "code_issues": 0.0
        }
        
        # 基于错误信息调整分数
        if "error_data" in integrated_info and integrated_info["error_data"]:
            error_raw = integrated_info["error_data"].get("raw", "")
            error_analysis = integrated_info["error_data"].get("analysis", {})
            
            # 根据错误类型调整分数
            if "TypeError" in error_raw or "ValueError" in error_raw:
                categories["data_issues"] += 0.3
            
            if "IndexError" in error_raw or "KeyError" in error_raw:
                categories["logic_issues"] += 0.3
                categories["data_issues"] += 0.2
            
            if "PermissionError" in error_raw or "ConnectionError" in error_raw:
                categories["system_issues"] += 0.4
            
            if "SyntaxError" in error_raw or "ImportError" in error_raw:
                categories["code_issues"] += 0.4
            
            # 根据错误分析进一步调整
            if error_analysis:
                root_cause = error_analysis.get("root_cause_summary", "")
                affected_components = error_analysis.get("affected_components", [])
                
                for component in affected_components:
                    if "database" in component.lower() or "data" in component.lower():
                        categories["data_issues"] += 0.2
                    elif "network" in component.lower() or "system" in component.lower():
                        categories["system_issues"] += 0.2
        
        # 基于代码分析调整分数
        if "code_data" in integrated_info and integrated_info["code_data"]:
            code_analysis = integrated_info["code_data"].get("analysis", {})
            
            if code_analysis:
                # 潜在bug
                bugs = code_analysis.get("potential_bugs", [])
                for bug in bugs:
                    bug_type = bug.get("bug_type", "").lower()
                    
                    if any(pattern in bug_type for pattern in ["type", "null", "undefined", "reference"]):
                        categories["data_issues"] += 0.15
                    elif any(pattern in bug_type for pattern in ["logic", "condition", "loop"]):
                        categories["logic_issues"] += 0.15
                    elif any(pattern in bug_type for pattern in ["syntax", "import", "declaration"]):
                        categories["code_issues"] += 0.15
                
                # 安全问题通常与系统或代码有关
                security_concerns = code_analysis.get("security_concerns", [])
                if security_concerns:
                    categories["system_issues"] += 0.1 * len(security_concerns)
                    categories["code_issues"] += 0.05 * len(security_concerns)
        
        # 标准化分数
        total = sum(categories.values())
        if total > 0:
            for category in categories:
                categories[category] /= total
        else:
            # 如果没有线索，默认平均分配
            for category in categories:
                categories[category] = 0.25
        
        return categories
    
    def _deep_causal_analysis(self, integrated_info: Dict[str, Any], 
                           cause_categories: Dict[str, float],
                           similar_bugs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        深度因果分析
        
        Args:
            integrated_info: 整合后的信息
            cause_categories: 潜在原因分类
            similar_bugs: 相似bug信息
            
        Returns:
            深度分析结果
        """
        # 构建提示词
        system_prompt = """你是一位经验丰富的软件调试专家，精通根因分析。请基于提供的所有信息，
        深入分析问题的根本原因。你的分析应该包括：
        
        1. 详细的根因描述
        2. 因果链分析（事件如何导致了最终的问题）
        3. 相关的代码结构或系统组件
        4. 你的信心水平(1-10)及理由
        
        请以JSON格式返回结果，包含以下字段：
        {
          "root_cause": "简明的根因描述",
          "causal_chain": ["因果链中的事件1", "事件2", ...],
          "explanation": "详细的解释，包括技术细节",
          "affected_components": ["受影响的组件1", "组件2", ...],
          "evidence": ["支持你分析的证据1", "证据2", ...],
          "confidence_level": 信心水平(1-10),
          "confidence_explanation": "信心水平的解释"
        }"""
        
        # 准备分析上下文
        context_parts = []
        
        # 添加错误信息
        if "error_data" in integrated_info and integrated_info["error_data"]:
            error_raw = integrated_info["error_data"].get("raw", "")
            if error_raw:
                context_parts.append(f"错误信息:\n```\n{error_raw}\n```")
            
            error_analysis = integrated_info["error_data"].get("analysis", {})
            if error_analysis:
                context_parts.append(f"错误分析:\n{json.dumps(error_analysis, ensure_ascii=False, indent=2)}")
        
        # 添加代码信息
        if "code_data" in integrated_info and integrated_info["code_data"]:
            code_raw = integrated_info["code_data"].get("raw", "")
            language = integrated_info["code_data"].get("language", "")
            if code_raw:
                context_parts.append(f"代码片段({language}):\n```{language}\n{code_raw}\n```")
            
            code_analysis = integrated_info["code_data"].get("analysis", {})
            if code_analysis:
                # 摘要代码分析，避免过长
                potential_bugs = code_analysis.get("potential_bugs", [])
                performance_issues = code_analysis.get("performance_issues", [])
                security_concerns = code_analysis.get("security_concerns", [])
                
                summary = {
                    "potential_bugs": potential_bugs,
                    "performance_issues": performance_issues,
                    "security_concerns": security_concerns
                }
                
                context_parts.append(f"代码分析摘要:\n{json.dumps(summary, ensure_ascii=False, indent=2)}")
        
        # 添加问题描述
        if "context_data" in integrated_info and integrated_info["context_data"]:
            problem_desc = integrated_info["context_data"].get("problem_description", "")
            if problem_desc:
                context_parts.append(f"问题描述:\n{problem_desc}")
        
        # 添加日志关键事件
        if "log_data" in integrated_info and integrated_info["log_data"]:
            key_events = integrated_info["log_data"].get("key_events", [])
            if key_events:
                context_parts.append(f"日志关键事件:\n{json.dumps(key_events, ensure_ascii=False, indent=2)}")
        
        # 添加潜在原因分类
        context_parts.append(f"潜在原因分类:\n{json.dumps(cause_categories, ensure_ascii=False, indent=2)}")
        
        # 添加相似bug信息
        if similar_bugs:
            similar_bugs_summary = []
            for bug in similar_bugs[:3]:  # 只取前三个最相似的
                similar_bugs_summary.append({
                    "title": bug.get("title", "未知标题"),
                    "root_cause": bug.get("root_cause", "未知原因"),
                    "similarity": bug.get("similarity", 0)
                })
            
            if similar_bugs_summary:
                context_parts.append(f"相似问题:\n{json.dumps(similar_bugs_summary, ensure_ascii=False, indent=2)}")
        
        # 组合提示词
        prompt = "请基于以下信息，深入分析问题的根本原因：\n\n" + "\n\n".join(context_parts)
        
        # 调用LLM分析
        analysis_text = self.llm_client.generate_with_retry(prompt, system_prompt)
        
        # 解析分析结果
        try:
            analysis = json.loads(analysis_text)
            return analysis
        except json.JSONDecodeError:
            logger.warning("无法解析深度因果分析的JSON结果")
            return {
                "root_cause": "无法确定",
                "causal_chain": [],
                "explanation": "分析过程遇到问题，无法生成结构化结果。原始分析：" + analysis_text[:500],
                "affected_components": [],
                "evidence": [],
                "confidence_level": 1,
                "confidence_explanation": "由于分析结果解析失败，置信度很低"
            }
    
    def _form_conclusion(self, root_cause_analysis: Dict[str, Any], 
                        input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        形成最终分析结论
        
        Args:
            root_cause_analysis: 根因分析结果
            input_data: 原始输入数据
            
        Returns:
            最终结论
        """
        # 提取根因分析的关键信息
        root_cause = root_cause_analysis.get("root_cause", "未能确定根本原因")
        explanation = root_cause_analysis.get("explanation", "")
        causal_chain = root_cause_analysis.get("causal_chain", [])
        affected_components = root_cause_analysis.get("affected_components", [])
        confidence_level = root_cause_analysis.get("confidence_level", 0)
        confidence_explanation = root_cause_analysis.get("confidence_explanation", "")
        evidence = root_cause_analysis.get("evidence", [])
        
        # 提取问题类型
        problem_type = self._determine_problem_type(root_cause, input_data)
        
        # 确定严重程度
        severity = self._determine_severity(root_cause, input_data, affected_components)
        
        # 相关因素
        related_factors = self._extract_related_factors(causal_chain, affected_components, evidence)
        
        # 形成最终结论
        conclusion = {
            "root_cause": root_cause,
            "explanation": explanation,
            "problem_type": problem_type,
            "severity": severity,
            "causal_chain": causal_chain,
            "affected_components": affected_components,
            "related_factors": related_factors,
            "confidence_level": confidence_level,
            "confidence_explanation": confidence_explanation
        }
        
        return conclusion
    
    def _determine_problem_type(self, root_cause: str, input_data: Dict[str, Any]) -> str:
        """确定问题类型"""
        # 默认未分类
        problem_type = "未分类"
        
        # 基于根因描述的关键词确定问题类型
        root_cause_lower = root_cause.lower()
        
        # 数据相关问题
        data_patterns = ["空值", "null", "undefined", "类型错误", "type error", 
                        "数据格式", "数据不一致", "缺少数据"]
        
        # 逻辑相关问题
        logic_patterns = ["逻辑错误", "条件判断", "边界条件", "算法错误", 
                         "状态管理", "异常流程", "竞态条件"]
        
        # 系统相关问题
        system_patterns = ["资源不足", "内存溢出", "权限不足", "配置错误", 
                          "网络问题", "环境差异", "依赖问题"]
        
        # 代码相关问题
        code_patterns = ["语法错误", "实现错误", "方法调用", "接口使用", 
                        "版本不兼容", "缺失功能"]
        
        # 检查根因描述中是否包含特定模式
        if any(pattern in root_cause_lower for pattern in data_patterns):
            problem_type = "数据问题"
        elif any(pattern in root_cause_lower for pattern in logic_patterns):
            problem_type = "逻辑问题"
        elif any(pattern in root_cause_lower for pattern in system_patterns):
            problem_type = "系统问题"
        elif any(pattern in root_cause_lower for pattern in code_patterns):
            problem_type = "代码问题"
        
        # 如果通过关键词无法确定，查看错误信息
        if problem_type == "未分类" and "error_message" in input_data.get("inputs", {}):
            error_raw = input_data["inputs"]["error_message"].get("raw_content", "").lower()
            
            if any(s in error_raw for s in ["typeerror", "valueerror", "keyerror", "indexerror"]):
                problem_type = "数据问题"
            elif any(s in error_raw for s in ["logicerror", "assertionerror"]):
                problem_type = "逻辑问题"
            elif any(s in error_raw for s in ["ioerror", "permissionerror", "memoryerror", "connectionerror"]):
                problem_type = "系统问题"
            elif any(s in error_raw for s in ["syntaxerror", "importerror", "attributeerror", "nameerror"]):
                problem_type = "代码问题"
        
        return problem_type
    
    def _determine_severity(self, root_cause: str, 
                         input_data: Dict[str, Any], 
                         affected_components: List[str]) -> str:
        """确定问题严重程度"""
        # 默认中等严重性
        severity = "中"
        
        # 基于错误信息和影响的组件数量确定严重程度
        if "error_message" in input_data.get("inputs", {}):
            error_raw = input_data["inputs"]["error_message"].get("raw_content", "").lower()
            
            # 关键严重性词
            critical_patterns = ["crash", "崩溃", "fatal", "致命", "数据丢失", "data loss", "严重漏洞"]
            high_patterns = ["error", "错误", "exception", "异常", "无法", "失败"]
            low_patterns = ["warning", "警告", "minor", "轻微", "deprecated", "不推荐"]
            
            # 检查错误信息中的严重性词
            if any(pattern in error_raw for pattern in critical_patterns):
                severity = "高"
            elif any(pattern in error_raw for pattern in high_patterns):
                severity = "中高"
            elif any(pattern in error_raw for pattern in low_patterns):
                severity = "低"
        
        # 基于受影响组件调整严重程度
        if affected_components:
            # 如果影响组件数量大于3，提高严重程度
            if len(affected_components) > 3:
                if severity == "低":
                    severity = "中"
                elif severity == "中":
                    severity = "中高"
                elif severity == "中高":
                    severity = "高"
            
            # 检查核心组件是否受影响
            core_components = ["database", "security", "authentication", "payment", "core", "主模块", "数据库", "安全", "认证", "支付"]
            if any(any(core in comp.lower() for core in core_components) for comp in affected_components):
                if severity != "高":
                    severity = "高"
        
        return severity
    
    def _extract_related_factors(self, causal_chain: List[str], 
                               affected_components: List[str],
                               evidence: List[str]) -> List[str]:
        """提取相关因素"""
        related_factors = []
        
        # 从因果链中提取相关因素
        if causal_chain:
            related_factors.extend([f"链式事件: {event}" for event in causal_chain])
        
        # 从受影响组件中提取相关因素
        if affected_components:
            related_factors.extend([f"影响组件: {comp}" for comp in affected_components])
        
        # 从证据中提取相关因素
        if evidence:
            related_factors.extend([f"相关证据: {evid}" for evid in evidence])
        
        return related_factors


class FixSuggestionGenerator:
    """
    修复建议生成器，负责生成详细的解决方案
    模拟资深工程师如何提供修复建议：
    1. 基于根因分析生成解决思路
    2. 提供具体的修复步骤和代码修改
    3. 详细解释修复的原理和效果
    4. 提供相关的最佳实践和预防措施
    5. 考虑不同的修复选项和权衡
    6. 提供长期解决方案和改进建议
    """
    
    def __init__(self):
        """初始化修复建议生成器"""
        self.llm_client = LLMClient()
        
        # 修复策略模板
        self.fix_strategies = {
            "data_issues": [
                "添加数据验证和处理",
                "修复类型错误",
                "处理边缘情况和空值",
                "修正数据格式和编码",
                "增加默认值和回退逻辑"
            ],
            "logic_issues": [
                "修正条件判断",
                "优化算法实现",
                "处理边界条件",
                "修复状态管理",
                "改进异常处理流程"
            ],
            "system_issues": [
                "调整系统配置",
                "修复依赖问题",
                "解决权限和安全问题",
                "优化资源使用",
                "修复网络和连接问题"
            ],
            "code_issues": [
                "修复语法错误",
                "重构代码结构",
                "优化API使用方式",
                "解决版本兼容性问题",
                "实现缺失功能"
            ]
        }
        
        # 不同语言的代码修复模板
        self.language_fix_templates = {
            "python": {
                "空值检查": "if variable is None:\n    # 处理空值情况",
                "异常处理": "try:\n    # 可能抛出异常的代码\nexcept ExceptionType as e:\n    # 处理异常",
                "资源管理": "with open(file_path, 'r') as file:\n    # 使用文件"
            },
            "javascript": {
                "空值检查": "if (variable === undefined || variable === null) {\n    // 处理空值情况\n}",
                "异常处理": "try {\n    // 可能抛出异常的代码\n} catch (error) {\n    // 处理异常\n}",
                "事件监听": "element.addEventListener('event', handler);\n// 清理时\nelement.removeEventListener('event', handler);"
            },
            "java": {
                "空值检查": "if (variable == null) {\n    // 处理空值情况\n}",
                "资源管理": "try (Resource resource = new Resource()) {\n    // 使用资源\n}",
                "异常处理": "try {\n    // 可能抛出异常的代码\n} catch (Exception e) {\n    // 处理异常\n}"
            }
        }
    
    def generate_solution(self, input_data: Dict[str, Any], 
                         root_cause: Dict[str, Any] = None,
                         similar_bugs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        生成解决方案
        
        Args:
            input_data: 所有输入数据
            root_cause: 根因分析结果
            similar_bugs: 相似bug信息
            
        Returns:
            解决方案
        """
        # 1. 准备上下文信息
        context_info = self._prepare_context(input_data, root_cause, similar_bugs)
        
        # 2. 确定修复策略
        fix_strategy = self._determine_fix_strategy(context_info)
        
        # 3. 生成详细的解决方案
        solution = self._generate_detailed_solution(context_info, fix_strategy)
        
        # 4. 增加解决方案质量检查
        solution = self._enhance_solution_quality(solution, context_info)
        
        return {
            "solution": solution
        }
    
    def _prepare_context(self, input_data: Dict[str, Any], 
                       root_cause: Dict[str, Any] = None,
                       similar_bugs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        准备上下文信息
        
        Args:
            input_data: 所有输入数据
            root_cause: 根因分析结果
            similar_bugs: 相似bug信息
            
        Returns:
            上下文信息
        """
        context = {
            "error_info": {},
            "code_info": {},
            "problem_info": {},
            "root_cause_info": {},
            "similar_solutions": []
        }
        
        # 提取错误信息
        if "error_message" in input_data.get("inputs", {}):
            error_data = input_data["inputs"]["error_message"]
            context["error_info"] = {
                "raw": error_data.get("raw_content", ""),
                "type": error_data.get("error_type", "未知错误类型"),
                "language": error_data.get("language", "未知语言")
            }
        
        # 提取代码信息
        if "code_snippet" in input_data.get("inputs", {}):
            code_data = input_data["inputs"]["code_snippet"]
            context["code_info"] = {
                "raw": code_data.get("raw_content", ""),
                "language": code_data.get("language", "未知语言"),
                "filename": code_data.get("filename", "")
            }
        
        # 提取问题描述
        if "problem_description" in input_data.get("inputs", {}):
            desc_data = input_data["inputs"]["problem_description"]
            context["problem_info"] = {
                "description": desc_data.get("raw_content", "")
            }
        
        # 提取根因信息
        if root_cause:
            context["root_cause_info"] = {
                "root_cause": root_cause.get("root_cause", "未知原因"),
                "explanation": root_cause.get("explanation", ""),
                "problem_type": root_cause.get("problem_type", "未知问题类型"),
                "causal_chain": root_cause.get("causal_chain", []),
                "affected_components": root_cause.get("affected_components", [])
            }
        
        # 提取相似bug的解决方案
        if similar_bugs:
            for bug in similar_bugs[:3]:  # 只使用前三个最相似的
                if "solution" in bug:
                    context["similar_solutions"].append({
                        "title": bug.get("title", "未知问题"),
                        "solution": bug.get("solution", "无解决方案"),
                        "similarity": bug.get("similarity", 0)
                    })
        
        return context
    
    def _determine_fix_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        确定修复策略
        
        Args:
            context: 上下文信息
            
        Returns:
            修复策略
        """
        # 初始化修复策略
        strategy = {
            "approach": "未确定",
            "strategies": [],
            "difficulty": "中",
            "estimated_impact": "中",
            "target_components": [],
            "language_specific_patterns": []
        }
        
        # 根据问题类型选择修复策略
        problem_type = context.get("root_cause_info", {}).get("problem_type", "")
        
        if problem_type in ["数据问题", "data_issues"]:
            strategy["approach"] = "数据修复"
            strategy["strategies"] = self.fix_strategies.get("data_issues", [])
        elif problem_type in ["逻辑问题", "logic_issues"]:
            strategy["approach"] = "逻辑修复"
            strategy["strategies"] = self.fix_strategies.get("logic_issues", [])
        elif problem_type in ["系统问题", "system_issues"]:
            strategy["approach"] = "系统修复"
            strategy["strategies"] = self.fix_strategies.get("system_issues", [])
        elif problem_type in ["代码问题", "code_issues"]:
            strategy["approach"] = "代码修复"
            strategy["strategies"] = self.fix_strategies.get("code_issues", [])
        else:
            # 如果问题类型未知，使用根因描述进行分析
            root_cause = context.get("root_cause_info", {}).get("root_cause", "").lower()
            
            if any(term in root_cause for term in ["空值", "null", "undefined", "类型", "数据"]):
                strategy["approach"] = "数据修复"
                strategy["strategies"] = self.fix_strategies.get("data_issues", [])
            elif any(term in root_cause for term in ["逻辑", "条件", "算法", "判断"]):
                strategy["approach"] = "逻辑修复"
                strategy["strategies"] = self.fix_strategies.get("logic_issues", [])
            elif any(term in root_cause for term in ["系统", "配置", "环境", "资源", "权限"]):
                strategy["approach"] = "系统修复"
                strategy["strategies"] = self.fix_strategies.get("system_issues", [])
            elif any(term in root_cause for term in ["代码", "语法", "实现", "函数"]):
                strategy["approach"] = "代码修复"
                strategy["strategies"] = self.fix_strategies.get("code_issues", [])
            else:
                # 默认策略
                strategy["approach"] = "综合修复"
                strategy["strategies"] = ["修复代码错误", "优化实现", "增加异常处理", "完善防御性编程"]
        
        # 确定目标组件
        affected_components = context.get("root_cause_info", {}).get("affected_components", [])
        if affected_components:
            strategy["target_components"] = affected_components
        
        # 获取语言特定的修复模式
        language = context.get("code_info", {}).get("language", "").lower()
        if language in self.language_fix_templates:
            strategy["language_specific_patterns"] = list(self.language_fix_templates[language].values())
        
        # 评估难度和影响
        root_cause = context.get("root_cause_info", {}).get("root_cause", "")
        causal_chain = context.get("root_cause_info", {}).get("causal_chain", [])
        
        # 复杂的因果链表明问题更复杂
        if len(causal_chain) > 3:
            strategy["difficulty"] = "高"
        
        # 影响多个组件的问题通常更严重
        if len(affected_components) > 2:
            strategy["estimated_impact"] = "高"
        
        return strategy
    
    def _generate_detailed_solution(self, context: Dict[str, Any], 
                                  fix_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成详细的解决方案
        
        Args:
            context: 上下文信息
            fix_strategy: 修复策略
            
        Returns:
            详细解决方案
        """
        # 构建提示词
        system_prompt = """你是一位资深的软件工程师和调试专家。请根据提供的信息，生成详细的修复方案。
        你的解决方案应该包括：
        

        1. 简明的解决方案总结
        2. 详细的修复步骤
        3. 具体的代码修改建议（包含原始代码和修复后的代码）
        4. 修复原理的解释
        5. 预防类似问题的建议
        6. 替代解决方案（如果适用）
        
        请确保你的解决方案直接针对根本原因，并且代码修改是准确、可实施的。以JSON格式返回，
        包含以下字段：
        {
          "solution_summary": "简短的解决方案总结",
          "fix_steps": ["详细的修复步骤1", "步骤2", ...],
          "code_changes": [
            {
              "file": "文件名或位置描述",
              "original_code": "原始代码片段",
              "fixed_code": "修复后的代码片段",
              "explanation": "此修改的解释"
            },
            ...
          ],
          "explanation": "解决方案的详细解释，包括为何有效",
          "prevention_tips": ["预防类似问题的建议1", "建议2", ...],
          "alternative_solutions": ["替代解决方案1", "解决方案2", ...]
        }"""
        
        # 准备分析上下文
        context_parts = []
        
        # 添加错误信息
        if "error_info" in context and context["error_info"]:
            error_raw = context["error_info"].get("raw", "")
            if error_raw:
                context_parts.append(f"错误信息:\n```\n{error_raw}\n```")
        
        # 添加代码信息
        if "code_info" in context and context["code_info"]:
            code_raw = context["code_info"].get("raw", "")
            language = context["code_info"].get("language", "")
            if code_raw:
                context_parts.append(f"代码片段({language}):\n```{language}\n{code_raw}\n```")
        
        # 添加问题描述
        if "problem_info" in context and context["problem_info"]:
            problem_desc = context["problem_info"].get("description", "")
            if problem_desc:
                context_parts.append(f"问题描述:\n{problem_desc}")
        
        # 添加根因分析
        if "root_cause_info" in context and context["root_cause_info"]:
            root_cause_text = f"""根因分析:
- 问题根因: {context['root_cause_info'].get('root_cause', '未知')}
- 问题类型: {context['root_cause_info'].get('problem_type', '未知')}
- 详细解释: {context['root_cause_info'].get('explanation', '无详细解释')}
- 影响组件: {', '.join(context['root_cause_info'].get('affected_components', ['未知']))}
"""
            context_parts.append(root_cause_text)
        
        # 添加修复策略信息
        strategy_text = f"""修复策略:
- 方法: {fix_strategy.get('approach', '未确定')}
- 建议策略: {', '.join(fix_strategy.get('strategies', ['无具体策略']))}
- 目标组件: {', '.join(fix_strategy.get('target_components', ['未指定']))}
"""
        context_parts.append(strategy_text)
        
        # 添加相似bug的解决方案
        if "similar_solutions" in context and context["similar_solutions"]:
            solutions_text = "相似问题的解决方案:\n"
            for sol in context["similar_solutions"]:
                solutions_text += f"- {sol.get('title', '未知问题')}: {sol.get('solution', '无解决方案')[:200]}...\n"
            context_parts.append(solutions_text)
        
        # 组合提示词
        prompt = "请根据以下信息，提供详细的修复方案：\n\n" + "\n\n".join(context_parts)
        
        # 调用LLM生成解决方案
        solution_text = self.llm_client.generate_with_retry(prompt, system_prompt)
        
        # 解析解决方案
        try:
            solution = json.loads(solution_text)
            return solution
        except json.JSONDecodeError:
            logger.warning("无法解析解决方案的JSON结果")
            return {
                "solution_summary": "无法生成结构化解决方案",
                "raw_solution": solution_text,
                "fix_steps": [],
                "code_changes": [],
                "explanation": "解析JSON时出现错误，请查看原始解决方案文本。",
                "prevention_tips": [],
                "alternative_solutions": []
            }
    
    def _enhance_solution_quality(self, solution: Dict[str, Any], 
                                context: Dict[str, Any]) -> Dict[str, Any]:
        """
        增强解决方案质量
        
        Args:
            solution: 原始解决方案
            context: 上下文信息
            
        Returns:
            增强后的解决方案
        """
        # 如果原始解决方案结构不完整，不进行增强
        if "raw_solution" in solution:
            return solution
        
        # 获取代码语言
        language = context.get("code_info", {}).get("language", "").lower()
        
        # 1. 确保代码修改部分结构完整
        code_changes = solution.get("code_changes", [])
        enhanced_code_changes = []
        
        for change in code_changes:
            # 确保每个代码修改都有必要的字段
            enhanced_change = {
                "file": change.get("file", "未指定文件"),
                "original_code": change.get("original_code", ""),
                "fixed_code": change.get("fixed_code", ""),
                "explanation": change.get("explanation", "无解释")
            }
            
            # 检查修改是否有意义（不为空且原始代码与修复代码不完全相同）
            original = enhanced_change["original_code"].strip()
            fixed = enhanced_change["fixed_code"].strip()
            
            if original and fixed and original != fixed:
                enhanced_code_changes.append(enhanced_change)
        
        solution["code_changes"] = enhanced_code_changes
        
        # 2. 确保修复步骤清晰可执行
        fix_steps = solution.get("fix_steps", [])
        if not fix_steps:
            # 如果没有修复步骤，根据代码修改生成
            fix_steps = []
            for i, change in enumerate(enhanced_code_changes, 1):
                fix_steps.append(f"步骤{i}: 修改文件 {change.get('file', '未指定文件')} - {change.get('explanation', '进行代码修改')}")
        
        solution["fix_steps"] = fix_steps
        
        # 3. 确保预防建议有实际价值
        prevention_tips = solution.get("prevention_tips", [])
        if not prevention_tips:
            # 根据问题类型提供通用预防建议
            problem_type = context.get("root_cause_info", {}).get("problem_type", "")
            
            if problem_type in ["数据问题", "data_issues"]:
                prevention_tips = [
                    "添加完善的输入数据验证",
                    "实现更健壮的错误处理机制",
                    "在关键操作前添加类型和空值检查"
                ]
            elif problem_type in ["逻辑问题", "logic_issues"]:
                prevention_tips = [
                    "添加更多的单元测试，尤其是边界条件",
                    "实现更清晰的条件判断逻辑",
                    "在复杂条件中添加详细注释"
                ]
            elif problem_type in ["系统问题", "system_issues"]:
                prevention_tips = [
                    "建立系统监控和告警机制",
                    "实现优雅的系统降级策略",
                    "定期检查系统配置和依赖"
                ]
            elif problem_type in ["代码问题", "code_issues"]:
                prevention_tips = [
                    "实施代码审查流程",
                    "使用静态代码分析工具",
                    "遵循语言和项目的编码规范"
                ]
            else:
                prevention_tips = [
                    "增加单元测试和集成测试覆盖率",
                    "实施更严格的代码审查流程",
                    "提高日志质量以便更好地诊断问题"
                ]
        
        solution["prevention_tips"] = prevention_tips
        
        # 4. 添加替代解决方案（如果没有）
        if "alternative_solutions" not in solution or not solution["alternative_solutions"]:
            solution["alternative_solutions"] = self._generate_alternative_solutions(context, solution)
        
        return solution
    
    def _generate_alternative_solutions(self, context: Dict[str, Any], 
                                      main_solution: Dict[str, Any]) -> List[str]:
        """生成替代解决方案"""
        # 获取问题类型和语言
        problem_type = context.get("root_cause_info", {}).get("problem_type", "")
        language = context.get("code_info", {}).get("language", "").lower()
        
        alternatives = []
        
        # 根据问题类型生成替代方案
        if problem_type in ["数据问题", "data_issues"]:
            alternatives = [
                f"使用{language}的数据验证库来实现更严格的类型检查",
                "采用防御性编程技术，为所有可能的空值情况添加回退策略",
                "重构数据处理逻辑，使用函数式编程模式处理数据流"
            ]
        elif problem_type in ["逻辑问题", "logic_issues"]:
            alternatives = [
                "重新设计算法或逻辑流程，考虑更简单的实现方式",
                "引入状态机模式来管理复杂的条件和状态转换",
                "使用更声明式的编程风格来表达业务逻辑"
            ]
        elif problem_type in ["系统问题", "system_issues"]:
            alternatives = [
                "使用配置管理系统统一管理所有环境配置",
                "实现服务降级策略，在资源不足时优雅降级",
                "使用依赖注入模式简化系统组件间的依赖关系"
            ]
        elif problem_type in ["代码问题", "code_issues"]:
            alternatives = [
                "重构代码以提高可读性和可维护性",
                "采用设计模式解决特定的架构问题",
                "引入更现代的语言特性或库来简化实现"
            ]
        else:
            alternatives = [
                "实施更全面的错误处理策略",
                "重新评估当前架构是否适合问题域",
                "考虑使用更专业的工具或库解决特定问题"
            ]
        
        return alternatives


class BugKnowledgeBaseClient:
    """Bug知识库客户端，负责与知识库交互"""
    
    def __init__(self):
        """初始化Bug知识库客户端"""
        self.config = get_config("bug_knowledge_base")
        self.endpoint = self.config.get("endpoint", "http://localhost:8000/query")
        self.top_k = self.config.get("top_k", 5)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.75)
    
    def query_similar_bugs(self, query_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        查询相似bug
        
        Args:
            query_data: 查询数据，包含错误信息、代码等
            
        Returns:
            相似bug列表
        """
        try:
            # 准备查询数据
            payload = {
                "query": self._prepare_query_text(query_data),
                "top_k": self.top_k,
                "threshold": self.similarity_threshold
            }
            
            # 调用API
            response = requests.post(
                self.endpoint,
                json=payload
            )
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                return results
            else:
                print(f"知识库查询失败: {response.status_code} - {response.text}")
                return []
            
        except Exception as e:
            print(f"知识库查询异常: {e}")
            return []
    
    def _prepare_query_text(self, query_data: Dict[str, Any]) -> str:
        """准备查询文本"""
        query_parts = []
        
        # 从输入数据中提取查询文本
        inputs = query_data.get("inputs", {})
        
        # 添加错误信息
        if "error_message" in inputs:
            error_raw = inputs["error_message"].get("raw_content", "")
            query_parts.append(error_raw)
        
        # 添加问题描述
        if "problem_description" in inputs:
            desc_raw = inputs["problem_description"].get("raw_content", "")
            query_parts.append(desc_raw)
        
        # 添加代码片段（可能需要限制长度）
        if "code_snippet" in inputs:
            code_raw = inputs["code_snippet"].get("raw_content", "")
            if len(code_raw) > 500:  # 限制代码长度
                code_raw = code_raw[:500]
            query_parts.append(code_raw)
        
        # 组合查询文本
        return " ".join(query_parts)


class AnalysisEngine:
    """
    LLM分析引擎，协调各个分析组件
    模拟资深工程师如何处理bug：
    1. 收集和整理所有信息
    2. 分析错误信息，提取关键线索
    3. 分析代码，找出潜在问题
    4. 进行根因推理，确定根本原因
    5. 参考历史经验和最佳实践
    6. 生成详细的修复方案
    7. 提供预防措施建议
    """
    
    def __init__(self):
        """初始化分析引擎"""
        # 实例化各个分析组件
        self.error_parser = ErrorMessageParser()
        self.code_analyzer = CodeAnalyzer()
        self.problem_cause_inference = ProblemCauseInferenceModule()
        self.fix_suggestion_generator = FixSuggestionGenerator()
        self.kb_client = BugKnowledgeBaseClient()
        
        # 分析流程配置
        self.analysis_pipeline = {
            "error_analysis": True,
            "code_analysis": True,
            "similar_bugs_lookup": True,
            "root_cause_analysis": True,
            "solution_generation": True
        }
    
    def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析输入数据
        
        Args:
            input_data: 输入数据，包含处理后的错误信息、代码等
            
        Returns:
            分析结果
        """
        # 初始化结果结构
        result = {
            "input_data": input_data,
            "analyses": {},
            "metadata": {
                "analysis_timestamp": self._get_timestamp(),
                "analysis_duration_ms": 0,
                "components_used": []
            }
        }
        
        # 记录分析开始时间
        start_time = time.time()
        
        # 获取输入
        inputs = input_data.get("inputs", {})
          # 执行分析流程
        try:
            # 1. 分析错误信息
            error_analysis = None
            if "error_message" in inputs and self.analysis_pipeline["error_analysis"]:
                error_analysis = self.error_parser.parse_error(inputs["error_message"])
                result["analyses"]["error_analysis"] = error_analysis
                result["metadata"]["components_used"].append("ErrorMessageParser")
            
            # 2. 分析代码
            code_analysis = None
            if "code_snippet" in inputs and self.analysis_pipeline["code_analysis"]:
                code_analysis = self.code_analyzer.analyze_code(inputs["code_snippet"])
                result["analyses"]["code_analysis"] = code_analysis
                result["metadata"]["components_used"].append("CodeAnalyzer")
            
            # 3. 查询相似bug
            similar_bugs = []
            if self.analysis_pipeline["similar_bugs_lookup"]:
                similar_bugs = self.kb_client.query_similar_bugs(input_data)
                if similar_bugs:
                    result["similar_bugs"] = similar_bugs
                    result["metadata"]["components_used"].append("BugKnowledgeBaseClient")
            
            # 4. 分析根因
            root_cause = None
            if self.analysis_pipeline["root_cause_analysis"]:
                root_cause = self.problem_cause_inference.analyze_root_cause(
                    input_data, 
                    error_analysis["parsed_error"] if error_analysis else None,
                    code_analysis["code_analysis"] if code_analysis else None,
                    similar_bugs
                )
                result["analyses"]["root_cause"] = root_cause
                result["metadata"]["components_used"].append("ProblemCauseInferenceModule")
            
            # 5. 生成解决方案
            solution = None
            if self.analysis_pipeline["solution_generation"]:
                solution = self.fix_suggestion_generator.generate_solution(
                    input_data,
                    root_cause["root_cause_analysis"] if root_cause else None,
                    similar_bugs
                )
                result["analyses"]["solution"] = solution
                result["metadata"]["components_used"].append("FixSuggestionGenerator")
              # 6. 整合分析结果，生成摘要
            result["summary"] = self._generate_analysis_summary(result)
            
        except Exception as e:
            # 记录分析过程中的异常
            logging.exception(f"分析过程发生异常: {e}")
            result["error"] = {
                "message": str(e),
                "traceback": traceback.format_exc()
            }
        
        # 计算分析持续时间
        end_time = time.time()
        result["metadata"]["analysis_duration_ms"] = int((end_time - start_time) * 1000)
        
        return result
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.datetime.now().isoformat()
    
    def _generate_analysis_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成分析结果摘要
        
        Args:
            result: 完整分析结果
            
        Returns:
            分析摘要
        """
        summary = {
            "title": "问题分析摘要",
            "problem_identified": False,
            "root_cause_identified": False,
            "solution_provided": False,
            "key_findings": [],
            "recommendation": ""
        }
        
        # 检查是否成功识别问题
        if "error_analysis" in result["analyses"]:
            error_data = result["analyses"]["error_analysis"].get("parsed_error", {})
            if error_data and error_data.get("error_type") != "未知":
                summary["problem_identified"] = True
                summary["key_findings"].append(f"识别到{error_data.get('error_language', '未知语言')}的{error_data.get('error_type', '未知')}错误")
        
        # 检查是否成功识别代码问题
        if "code_analysis" in result["analyses"]:
            code_data = result["analyses"]["code_analysis"].get("code_analysis", {})
            potential_bugs = code_data.get("potential_bugs", [])
            if potential_bugs:
                summary["problem_identified"] = True
                summary["key_findings"].append(f"在代码中发现了{len(potential_bugs)}个潜在问题")
        
        # 检查是否成功识别根因
        if "root_cause" in result["analyses"]:
            root_cause_data = result["analyses"]["root_cause"].get("root_cause_analysis", {})
            if root_cause_data and root_cause_data.get("root_cause") != "未能确定":
                summary["root_cause_identified"] = True
                summary["key_findings"].append(f"根本原因: {root_cause_data.get('root_cause', '未知')}")
                
                # 添加因果链信息
                causal_chain = root_cause_data.get("causal_chain", [])
                if causal_chain:
                    summary["key_findings"].append("识别出问题的因果链")
        
        # 检查是否成功生成解决方案
        if "solution" in result["analyses"]:
            solution_data = result["analyses"]["solution"].get("solution", {})
            if solution_data and "raw_solution" not in solution_data:
                summary["solution_provided"] = True
                summary["key_findings"].append(f"解决方案: {solution_data.get('solution_summary', '未知')}")
                
                # 添加修复步骤数量
                fix_steps = solution_data.get("fix_steps", [])
                if fix_steps:
                    summary["key_findings"].append(f"提供了{len(fix_steps)}个修复步骤")
                
                # 添加代码修改建议数量
                code_changes = solution_data.get("code_changes", [])
                if code_changes:
                    summary["key_findings"].append(f"提供了{len(code_changes)}处代码修改建议")
        
        # 添加相似bug信息
        if "similar_bugs" in result and result["similar_bugs"]:
            similar_bugs = result["similar_bugs"]
            summary["key_findings"].append(f"找到了{len(similar_bugs)}个相似的历史问题")
        
        # 生成总体建议
        if summary["solution_provided"]:
            summary["recommendation"] = "建议按照提供的解决方案实施修复"
        elif summary["root_cause_identified"]:
            summary["recommendation"] = "已识别根本原因，但需要人工制定解决方案"
        elif summary["problem_identified"]:
            summary["recommendation"] = "已识别问题，但需要进一步分析根本原因"
        else:
            summary["recommendation"] = "无法自动分析，建议人工审查"
        
        return summary


# 创建全局分析引擎实例
analysis_engine = AnalysisEngine()


def analyze(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    分析输入数据的便捷函数
    
    Args:
        input_data: 输入数据
        
    Returns:
        分析结果
    """
    return analysis_engine.analyze(input_data)
