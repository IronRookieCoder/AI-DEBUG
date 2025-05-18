"""输入层模块，负责处理各种输入数据"""

from typing import Dict, Any, Optional, List
import json


class InputProcessor:
    """
    输入处理器基类，所有输入处理器的父类
    """
    
    def process(self, data: Any) -> Dict[str, Any]:
        """
        处理输入数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理后的数据字典
        """
        raise NotImplementedError("子类必须实现此方法")


class ErrorMessageProcessor(InputProcessor):
    """
    错误信息处理器
    """
    
    def process(self, error_message: str) -> Dict[str, Any]:
        """
        处理错误消息
        
        Args:
            error_message: 错误消息字符串
            
        Returns:
            处理后的错误信息字典，包含解析后的错误类型、位置等信息
        """
        result = {
            "type": "error_message",
            "raw_content": error_message,
            "parsed": {}
        }
        
        # 解析错误信息
        # 根据常见的错误模式进行解析
        if "Syntax" in error_message:
            result["parsed"]["category"] = "syntax_error"
        elif "TypeError" in error_message:
            result["parsed"]["category"] = "type_error"
        elif "ReferenceError" in error_message:
            result["parsed"]["category"] = "reference_error"
        elif "Exception" in error_message:
            result["parsed"]["category"] = "exception"
        else:
            result["parsed"]["category"] = "unknown_error"
            
        # 解析错误位置
        import re
        line_match = re.search(r"line (\d+)", error_message)
        if line_match:
            result["parsed"]["line"] = int(line_match.group(1))
            
        file_match = re.search(r"File [\"'](.+?)[\"']", error_message)
        if file_match:
            result["parsed"]["file"] = file_match.group(1)
            
        return result


class CodeSnippetProcessor(InputProcessor):
    """
    代码片段处理器
    """
    
    def process(self, code: str) -> Dict[str, Any]:
        """
        处理代码片段
        
        Args:
            code: 代码片段字符串
            
        Returns:
            处理后的代码信息字典，包含代码内容、语言类型等
        """
        # 检测代码语言
        language = self._detect_language(code)
        
        result = {
            "type": "code_snippet",
            "raw_content": code,
            "language": language,
            "parsed": {
                "tokens": self._tokenize_code(code, language),
                "structure": self._extract_structure(code, language)
            }
        }
        return result
    
    def _detect_language(self, code: str) -> str:
        """检测代码语言"""
        # 简单的语言检测逻辑，实际项目中可能需要更复杂的算法
        if "import " in code and ("def " in code or "class " in code):
            return "python"
        elif "{" in code and "function" in code:
            return "javascript"
        elif "{" in code and ("public" in code or "private" in code or "class" in code):
            return "java"
        elif "#include" in code:
            return "c++"
        else:
            return "unknown"
    
    def _tokenize_code(self, code: str, language: str) -> List[Dict[str, Any]]:
        """将代码标记化"""
        # 简化版的代码标记化，实际应该使用专业的代码解析库
        tokens = []
        lines = code.split('\n')
        for i, line in enumerate(lines):
            tokens.append({
                "line": i + 1,
                "content": line,
                "indentation": len(line) - len(line.lstrip())
            })
        return tokens
    
    def _extract_structure(self, code: str, language: str) -> Dict[str, Any]:
        """提取代码结构"""
        # 简化版的结构提取，实际应该使用专业的AST解析
        structure = {
            "functions": [],
            "classes": [],
            "imports": []
        }
        
        lines = code.split('\n')
        for line in lines:
            line = line.strip()
            if language == "python":
                if line.startswith("def "):
                    fn_name = line.split("def ")[1].split("(")[0]
                    structure["functions"].append(fn_name)
                elif line.startswith("class "):
                    class_name = line.split("class ")[1].split("(")[0].split(":")[0]
                    structure["classes"].append(class_name)
                elif line.startswith("import ") or line.startswith("from "):
                    structure["imports"].append(line)
                    
        return structure


class ProblemDescriptionProcessor(InputProcessor):
    """
    问题描述处理器
    """
    
    def process(self, description: str) -> Dict[str, Any]:
        """
        处理问题描述
        
        Args:
            description: 问题描述文本
            
        Returns:
            处理后的问题描述字典，包含关键词提取等信息
        """
        result = {
            "type": "problem_description",
            "raw_content": description,
            "parsed": {
                "keywords": self._extract_keywords(description),
                "summary": self._summarize(description)
            }
        }
        return result
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取，实际应使用NLP技术
        words = text.lower().split()
        # 去除常见停用词
        stopwords = {"a", "an", "the", "is", "are", "was", "were", "in", "on", "at", "to", "for"}
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        # 返回前10个最常见词
        from collections import Counter
        return [word for word, _ in Counter(keywords).most_common(10)]
    
    def _summarize(self, text: str) -> str:
        """生成摘要"""
        # 简单的摘要方法，实际应使用更高级的文本摘要技术
        if len(text) <= 200:
            return text
        return text[:197] + "..."


class LogInfoProcessor(InputProcessor):
    """
    日志信息处理器
    """
    
    def process(self, log_text: str) -> Dict[str, Any]:
        """
        处理日志信息
        
        Args:
            log_text: 日志文本
            
        Returns:
            处理后的日志信息字典，包含时间戳、级别、消息等解析信息
        """
        result = {
            "type": "log_info",
            "raw_content": log_text,
            "parsed": {
                "entries": self._parse_log_entries(log_text)
            }
        }
        return result
    
    def _parse_log_entries(self, log_text: str) -> List[Dict[str, Any]]:
        """解析日志条目"""
        entries = []
        import re
        
        # 尝试匹配常见的日志格式
        log_lines = log_text.strip().split('\n')
        
        for line in log_lines:
            entry = {"raw": line}
            
            # 尝试解析时间戳
            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})', line)
            if timestamp_match:
                entry["timestamp"] = timestamp_match.group(1)
            
            # 尝试解析日志级别
            level_match = re.search(r'\b(ERROR|WARNING|INFO|DEBUG|CRITICAL|WARN)\b', line, re.IGNORECASE)
            if level_match:
                entry["level"] = level_match.group(1).upper()
            
            # 如果有时间戳或级别，那么可能消息是其后的内容
            if "timestamp" in entry or "level" in entry:
                message_parts = re.split(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}|\b(ERROR|WARNING|INFO|DEBUG|CRITICAL|WARN)\b', line, 1, re.IGNORECASE)
                if len(message_parts) > 1:
                    entry["message"] = message_parts[-1].strip()
            
            entries.append(entry)
        
        return entries


class InputManager:
    """
    输入管理器，负责协调各种输入处理器
    """
    
    def __init__(self):
        """初始化输入管理器"""
        self.processors = {
            "error_message": ErrorMessageProcessor(),
            "code_snippet": CodeSnippetProcessor(),
            "problem_description": ProblemDescriptionProcessor(),
            "log_info": LogInfoProcessor()
        }
    
    def process_input(self, input_type: str, data: Any) -> Optional[Dict[str, Any]]:
        """
        处理指定类型的输入
        
        Args:
            input_type: 输入类型，如"error_message"、"code_snippet"等
            data: 输入数据
            
        Returns:
            处理后的数据字典
        """
        processor = self.processors.get(input_type)
        if not processor:
            print(f"未找到类型为 {input_type} 的处理器")
            return None
        
        return processor.process(data)
    
    def process_combined_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理组合输入数据
        
        Args:
            input_data: 包含多种输入类型的字典
            
        Returns:
            处理后的组合数据字典
        """
        result = {"inputs": {}}
        
        for input_type, data in input_data.items():
            if input_type in self.processors:
                processed = self.process_input(input_type, data)
                if processed:
                    result["inputs"][input_type] = processed
        
        return result


# 创建全局输入管理器实例
input_manager = InputManager()


def process_input(input_type: str, data: Any) -> Optional[Dict[str, Any]]:
    """
    处理输入的便捷函数
    
    Args:
        input_type: 输入类型
        data: 输入数据
        
    Returns:
        处理后的数据
    """
    return input_manager.process_input(input_type, data)


def process_combined_input(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理组合输入的便捷函数
    
    Args:
        input_data: 包含多种输入类型的数据
        
    Returns:
        处理后的组合数据
    """
    return input_manager.process_combined_input(input_data)
