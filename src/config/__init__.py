"""配置管理模块，负责加载和管理系统配置"""

import json
import os
from typing import Dict, Any


class ConfigManager:
    """配置管理器类，负责加载、验证和提供配置信息"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为None时使用默认路径
        """
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
            return config
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}
    
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
