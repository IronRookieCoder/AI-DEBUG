"""LLM分析引擎模块，负责调用LLM进行代码和错误分析"""

import json
import os
import requests
from typing import Dict, Any, List, Optional

from ..config import get_config


class LLMClient:
    """LLM客户端，负责与LLM API通信"""
    
    def __init__(self):
        """初始化LLM客户端"""
        self.config = get_config("llm")
        self.api_key = self.config.get("api_key", os.environ.get("LLM_API_KEY", ""))
        self.model = self.config.get("model", "gpt-4")
        self.temperature = self.config.get("temperature", 0.3)
        self.max_tokens = self.config.get("max_tokens", 2000)
    
    def generate(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """
        调用LLM生成内容
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            
        Returns:
            生成的文本，失败时返回None
        """
        try:
            # 构建API请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            # 调用API
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"API调用失败: {response.status_code} - {response.text}")
                return None
            
        except Exception as e:
            print(f"LLM调用异常: {e}")
            return None


class ErrorAnalyzer:
    """错误分析器，负责解析错误信息"""
    
    def __init__(self):
        """初始化错误分析器"""
        self.llm_client = LLMClient()
    
    def analyze_error(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析错误信息
        
        Args:
            error_info: 输入层处理后的错误信息
            
        Returns:
            错误分析结果
        """
        # 构建提示词
        system_prompt = """你是一个专业的错误信息分析专家。请分析提供的错误信息，解释错误的含义、
        可能的原因，以及如何解决这个问题。尽可能详细地解释，包括可能的代码示例。格式化输出为JSON，
        包含以下字段：error_type, description, possible_causes (数组), solution_steps (数组)。"""
        
        error_raw = error_info.get("raw_content", "")
        error_category = error_info.get("parsed", {}).get("category", "未知错误")
        
        prompt = f"""请分析以下错误信息：
        
        错误类型: {error_category}
        原始错误信息: 
        ```
        {error_raw}
        ```
        
        请提供详细的错误分析和解决方案。"""
        
        # 调用LLM分析
        analysis_text = self.llm_client.generate(prompt, system_prompt)
        
        # 解析分析结果
        try:
            analysis = json.loads(analysis_text)
            return {
                "error_analysis": analysis
            }
        except json.JSONDecodeError:
            # 如果结果不是有效的JSON，则返回原始文本
            return {
                "error_analysis": {
                    "error_type": error_category,
                    "description": "分析过程遇到问题",
                    "raw_analysis": analysis_text,
                    "possible_causes": [],
                    "solution_steps": []
                }
            }


class CodeAnalyzer:
    """代码分析器，负责分析代码"""
    
    def __init__(self):
        """初始化代码分析器"""
        self.llm_client = LLMClient()
    
    def analyze_code(self, code_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析代码
        
        Args:
            code_info: 输入层处理后的代码信息
            
        Returns:
            代码分析结果
        """
        # 构建提示词
        system_prompt = """你是一个代码分析专家。请分析提供的代码，识别潜在的问题和改进点。
        你的分析应该包括代码的优缺点、潜在的bug、性能问题和安全隐患等。格式化输出为JSON，
        包含以下字段：code_quality, potential_bugs (数组), performance_issues (数组), 
        security_concerns (数组), improvement_suggestions (数组)。"""
        
        code_raw = code_info.get("raw_content", "")
        language = code_info.get("language", "未知语言")
        
        prompt = f"""请分析以下{language}代码：
        
        ```{language}
        {code_raw}
        ```
        
        请提供详细的代码分析，包括代码质量评估、潜在bug、性能优化建议和安全隐患。"""
        
        # 调用LLM分析
        analysis_text = self.llm_client.generate(prompt, system_prompt)
        
        # 解析分析结果
        try:
            analysis = json.loads(analysis_text)
            return {
                "code_analysis": analysis
            }
        except json.JSONDecodeError:
            # 如果结果不是有效的JSON，则返回原始文本
            return {
                "code_analysis": {
                    "code_quality": "无法评估",
                    "raw_analysis": analysis_text,
                    "potential_bugs": [],
                    "performance_issues": [],
                    "security_concerns": [],
                    "improvement_suggestions": []
                }
            }


class RootCauseAnalyzer:
    """根因分析器，负责推断问题的原因"""
    
    def __init__(self):
        """初始化根因分析器"""
        self.llm_client = LLMClient()
        
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
        # 构建提示词
        system_prompt = """你是一个专业的软件调试专家。请根据提供的信息（错误信息、代码、问题描述、日志等），
        分析问题的根本原因。你的回答应该详细、准确，并针对根因提供合理的解释。格式化输出为JSON，
        包含以下字段：root_cause, explanation, confidence_level (1-10), related_factors (数组)。"""
        
        # 构建输入信息
        input_parts = []
        
        # 添加错误信息
        if "error_message" in input_data.get("inputs", {}):
            error_raw = input_data["inputs"]["error_message"].get("raw_content", "")
            input_parts.append(f"错误信息:\n```\n{error_raw}\n```")
        
        # 添加代码信息
        if "code_snippet" in input_data.get("inputs", {}):
            code_raw = input_data["inputs"]["code_snippet"].get("raw_content", "")
            language = input_data["inputs"]["code_snippet"].get("language", "")
            input_parts.append(f"代码片段({language}):\n```{language}\n{code_raw}\n```")
        
        # 添加问题描述
        if "problem_description" in input_data.get("inputs", {}):
            desc_raw = input_data["inputs"]["problem_description"].get("raw_content", "")
            input_parts.append(f"问题描述:\n{desc_raw}")
        
        # 添加日志信息
        if "log_info" in input_data.get("inputs", {}):
            log_raw = input_data["inputs"]["log_info"].get("raw_content", "")
            input_parts.append(f"日志信息:\n```\n{log_raw}\n```")
        
        # 添加错误分析
        if error_analysis:
            input_parts.append(f"错误分析:\n{json.dumps(error_analysis, ensure_ascii=False, indent=2)}")
        
        # 添加代码分析
        if code_analysis:
            input_parts.append(f"代码分析:\n{json.dumps(code_analysis, ensure_ascii=False, indent=2)}")
        
        # 添加相似bug信息
        if similar_bugs:
            bugs_text = "\n".join([f"- {bug.get('title', '未知标题')}: {bug.get('description', '无描述')[:200]}..." 
                                 for bug in similar_bugs[:3]])
            input_parts.append(f"相似Bug信息:\n{bugs_text}")
        
        # 组合提示词
        prompt = "请分析以下信息，确定问题的根本原因：\n\n" + "\n\n".join(input_parts)
        
        # 调用LLM分析
        analysis_text = self.llm_client.generate(prompt, system_prompt)
        
        # 解析分析结果
        try:
            analysis = json.loads(analysis_text)
            return {
                "root_cause_analysis": analysis
            }
        except json.JSONDecodeError:
            # 如果结果不是有效的JSON，则返回原始文本
            return {
                "root_cause_analysis": {
                    "root_cause": "未能确定",
                    "explanation": "分析过程遇到问题",
                    "raw_analysis": analysis_text,
                    "confidence_level": 0,
                    "related_factors": []
                }
            }


class SolutionGenerator:
    """解决方案生成器，负责生成修复建议"""
    
    def __init__(self):
        """初始化解决方案生成器"""
        self.llm_client = LLMClient()
        
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
        # 构建提示词
        system_prompt = """你是一个专业的软件开发调试专家。请根据提供的信息（错误信息、代码、问题描述、日志、根因分析等），
        提供详细的解决方案。解决方案应该包括具体的修复步骤、代码修改建议和解释。格式化输出为JSON，
        包含以下字段：solution_summary, fix_steps (数组), code_changes (数组，每项包含original_code和fixed_code), 
        explanation, prevention_tips (数组)。"""
        
        # 构建输入信息
        input_parts = []
        
        # 添加错误信息
        if "error_message" in input_data.get("inputs", {}):
            error_raw = input_data["inputs"]["error_message"].get("raw_content", "")
            input_parts.append(f"错误信息:\n```\n{error_raw}\n```")
        
        # 添加代码信息
        if "code_snippet" in input_data.get("inputs", {}):
            code_raw = input_data["inputs"]["code_snippet"].get("raw_content", "")
            language = input_data["inputs"]["code_snippet"].get("language", "")
            input_parts.append(f"代码片段({language}):\n```{language}\n{code_raw}\n```")
        
        # 添加问题描述
        if "problem_description" in input_data.get("inputs", {}):
            desc_raw = input_data["inputs"]["problem_description"].get("raw_content", "")
            input_parts.append(f"问题描述:\n{desc_raw}")
        
        # 添加根因分析
        if root_cause:
            input_parts.append(f"根因分析:\n{json.dumps(root_cause, ensure_ascii=False, indent=2)}")
        
        # 添加相似bug的解决方案
        if similar_bugs:
            solutions_text = "\n".join([f"- Bug: {bug.get('title', '未知标题')}\n  解决方案: {bug.get('solution', '无解决方案')[:200]}..." 
                                     for bug in similar_bugs[:3] if 'solution' in bug])
            if solutions_text:
                input_parts.append(f"相似Bug的解决方案:\n{solutions_text}")
        
        # 组合提示词
        prompt = "请根据以下信息，提供详细的解决方案：\n\n" + "\n\n".join(input_parts)
        
        # 调用LLM生成解决方案
        solution_text = self.llm_client.generate(prompt, system_prompt)
        
        # 解析解决方案
        try:
            solution = json.loads(solution_text)
            return {
                "solution": solution
            }
        except json.JSONDecodeError:
            # 如果结果不是有效的JSON，则返回原始文本
            return {
                "solution": {
                    "solution_summary": "无法生成结构化解决方案",
                    "raw_solution": solution_text,
                    "fix_steps": [],
                    "code_changes": [],
                    "explanation": "",
                    "prevention_tips": []
                }
            }


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
    """LLM分析引擎，协调各个分析组件"""
    
    def __init__(self):
        """初始化分析引擎"""
        self.error_analyzer = ErrorAnalyzer()
        self.code_analyzer = CodeAnalyzer()
        self.root_cause_analyzer = RootCauseAnalyzer()
        self.solution_generator = SolutionGenerator()
        self.kb_client = BugKnowledgeBaseClient()
    
    def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析输入数据
        
        Args:
            input_data: 输入数据，包含处理后的错误信息、代码等
            
        Returns:
            分析结果
        """
        result = {
            "input_data": input_data,
            "analyses": {}
        }
        
        # 获取输入
        inputs = input_data.get("inputs", {})
        
        # 分析错误信息
        error_analysis = None
        if "error_message" in inputs:
            error_analysis = self.error_analyzer.analyze_error(inputs["error_message"])
            result["analyses"]["error_analysis"] = error_analysis
        
        # 分析代码
        code_analysis = None
        if "code_snippet" in inputs:
            code_analysis = self.code_analyzer.analyze_code(inputs["code_snippet"])
            result["analyses"]["code_analysis"] = code_analysis
        
        # 查询相似bug
        similar_bugs = self.kb_client.query_similar_bugs(input_data)
        if similar_bugs:
            result["similar_bugs"] = similar_bugs
        
        # 分析根因
        root_cause = self.root_cause_analyzer.analyze_root_cause(
            input_data, 
            error_analysis["error_analysis"] if error_analysis else None,
            code_analysis["code_analysis"] if code_analysis else None,
            similar_bugs
        )
        result["analyses"]["root_cause"] = root_cause
        
        # 生成解决方案
        solution = self.solution_generator.generate_solution(
            input_data,
            root_cause["root_cause_analysis"] if root_cause else None,
            similar_bugs
        )
        result["analyses"]["solution"] = solution
        
        return result


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
