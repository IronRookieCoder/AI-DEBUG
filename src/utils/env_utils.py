"""环境变量工具模块，提供便捷的环境变量访问函数"""

import os
from typing import Any, Optional


def get_env(name: str, default: Any = None) -> Optional[str]:
    """
    获取环境变量
    
    Args:
        name: 环境变量名称
        default: 默认值，当环境变量不存在时返回
        
    Returns:
        环境变量值或默认值
    """
    return os.environ.get(name, default)


def get_bool_env(name: str, default: bool = False) -> bool:
    """
    获取布尔类型的环境变量
    
    Args:
        name: 环境变量名称
        default: 默认值，当环境变量不存在时返回
        
    Returns:
        布尔值
    """
    value = get_env(name)
    if value is None:
        return default
    
    # 将字符串转换为布尔值
    return value.lower() in ('true', 'yes', '1', 't', 'y')


def get_int_env(name: str, default: Optional[int] = None) -> Optional[int]:
    """
    获取整数类型的环境变量
    
    Args:
        name: 环境变量名称
        default: 默认值，当环境变量不存在或无法转换为整数时返回
        
    Returns:
        整数值或默认值
    """
    value = get_env(name)
    if value is None:
        return default
    
    try:
        return int(value)
    except ValueError:
        print(f"警告: 环境变量 {name} 的值 '{value}' 无法转换为整数，使用默认值 {default}")
        return default


def get_float_env(name: str, default: Optional[float] = None) -> Optional[float]:
    """
    获取浮点类型的环境变量
    
    Args:
        name: 环境变量名称
        default: 默认值，当环境变量不存在或无法转换为浮点数时返回
        
    Returns:
        浮点数值或默认值
    """
    value = get_env(name)
    if value is None:
        return default
    
    try:
        return float(value)
    except ValueError:
        print(f"警告: 环境变量 {name} 的值 '{value}' 无法转换为浮点数，使用默认值 {default}")
        return default
