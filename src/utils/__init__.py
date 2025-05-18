"""通用工具函数模块"""

import logging
import os
import json
from typing import Dict, Any, List, Optional, Union


logger = logging.getLogger(__name__)


def ensure_dir_exists(directory: str) -> bool:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory: 目录路径
        
    Returns:
        是否成功创建或目录已存在
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        return True
    except Exception as e:
        logger.error(f"创建目录 {directory} 失败: {e}")
        return False


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    加载JSON文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        JSON数据，加载失败时返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载JSON文件 {file_path} 失败: {e}")
        return None


def save_json_file(data: Dict[str, Any], file_path: str) -> bool:
    """
    保存JSON文件
    
    Args:
        data: 要保存的数据
        file_path: 文件路径
        
    Returns:
        是否保存成功
    """
    try:
        # 确保目录存在
        directory = os.path.dirname(file_path)
        ensure_dir_exists(directory)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存JSON文件 {file_path} 失败: {e}")
        return False


def detect_code_language(code: str) -> str:
    """
    检测代码语言
    
    Args:
        code: 代码字符串
        
    Returns:
        检测到的语言
    """
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


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本到指定长度
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后添加的后缀
        
    Returns:
        截断后的文本
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length-len(suffix)] + suffix


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并两个字典，包括嵌套字典
    
    Args:
        dict1: 第一个字典
        dict2: 第二个字典
        
    Returns:
        合并后的字典
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # 如果两个都是字典，递归合并
            result[key] = merge_dicts(result[key], value)
        else:
            # 否则直接覆盖
            result[key] = value
    
    return result


def format_error_message(error_type: str, message: str, file: str = None, 
                        line: int = None, column: int = None) -> str:
    """
    格式化错误消息
    
    Args:
        error_type: 错误类型
        message: 错误消息
        file: 文件路径
        line: 行号
        column: 列号
        
    Returns:
        格式化后的错误消息
    """
    parts = [f"{error_type}: {message}"]
    
    if file:
        location = f"File: {file}"
        if line is not None:
            location += f", Line: {line}"
            if column is not None:
                location += f", Column: {column}"
        parts.append(location)
    
    return "\n".join(parts)


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    从文本中提取关键词
    
    Args:
        text: 文本
        max_keywords: 最大关键词数量
        
    Returns:
        关键词列表
    """
    # 简单的关键词提取，实际应使用NLP技术
    words = text.lower().split()
    # 去除常见停用词
    stopwords = {"a", "an", "the", "is", "are", "was", "were", "in", "on", "at", "to", "for", "and", "or", "but"}
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    # 返回前N个最常见词
    from collections import Counter
    return [word for word, _ in Counter(keywords).most_common(max_keywords)]
