"""配置管理模块，负责加载和管理系统配置"""

import json
import os
import re
from typing import Dict, Any
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    # 如果没有安装dotenv库，提供空实现
    def load_dotenv(*args, **kwargs):
        print("警告: python-dotenv库未安装，无法从.env文件加载环境变量")
        return False


class ConfigManager:
    """配置管理器类，负责加载、验证和提供配置信息"""
    
    def __init__(self, config_path: str = None, env_file: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为None时使用默认路径
            env_file: 环境变量文件路径，默认为None时寻找项目根目录下的.env文件
        """
        # 加载环境变量文件
        if env_file is None:
            # 尝试在项目根目录查找.env文件
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            env_path = os.path.join(base_dir, ".env")
            if os.path.exists(env_path):
                load_dotenv(env_path)
                print(f"已加载环境变量文件: {env_path}")
            else:
                # 也检查config目录
                config_dir = os.path.dirname(os.path.abspath(__file__))
                env_path = os.path.join(config_dir, ".env")
                if os.path.exists(env_path):
                    load_dotenv(env_path)
                    print(f"已加载环境变量文件: {env_path}")
        else:
            # 使用指定的环境变量文件
            if os.path.exists(env_file):
                load_dotenv(env_file)
                print(f"已加载环境变量文件: {env_file}")
            else:
                print(f"警告: 环境变量文件不存在: {env_file}")
        
        if not config_path:
            # 使用默认配置路径
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, "config", "config.json")
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        从配置文件加载配置
        
        Returns:
            配置字典
        """
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            # 处理环境变量
            config = self._process_env_variables(config)
            return config
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}
    
    def _process_env_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理配置中的环境变量引用
        
        Args:
            config: 配置字典
            
        Returns:
            处理后的配置字典
        """
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, (dict, list)):
                    config[key] = self._process_env_variables(value)
                elif isinstance(value, str):
                    # 查找${ENV_VAR}格式的环境变量引用
                    env_var_pattern = r'\${([A-Za-z0-9_]+)}'
                    matches = re.findall(env_var_pattern, value)
                    
                    if matches:
                        for env_var in matches:
                            env_value = os.environ.get(env_var)
                            if env_value is not None:
                                # 替换环境变量引用
                                value = value.replace(f'${{{env_var}}}', env_value)
                            else:
                                print(f"警告: 环境变量 {env_var} 未设置")
                        config[key] = value
            return config
        elif isinstance(config, list):
            return [self._process_env_variables(item) for item in config]
        else:
            return config
    
    def get_config(self, section: str = None) -> Dict[str, Any]:
        """
        获取配置信息
        
        Args:
            section: 配置部分名称，默认为None返回全部配置
            
        Returns:
            配置字典或配置部分
        """
        if section:
            return self.config.get(section, {})
        return self.config
    
    def update_config(self, new_config: Dict[str, Any], save: bool = True) -> bool:
        """
        更新配置
        
        Args:
            new_config: 新的配置字典
            save: 是否保存到文件
            
        Returns:
            更新是否成功
        """
        try:
            self.config.update(new_config)
            if save:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"更新配置失败: {e}")
            return False


# 全局配置实例
config_manager = ConfigManager()


def get_config(section: str = None) -> Dict[str, Any]:
    """
    获取配置便捷函数
    
    Args:
        section: 配置部分名称
        
    Returns:
        配置字典或配置部分
    """
    return config_manager.get_config(section)
