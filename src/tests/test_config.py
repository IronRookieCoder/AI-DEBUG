"""测试配置模块"""

import os
import json
import pytest
from src.config import ConfigManager, get_config


def test_config_manager_init():
    """测试配置管理器初始化"""
    config_manager = ConfigManager()
    assert config_manager is not None
    assert config_manager.config is not None


def test_get_config():
    """测试获取配置"""
    config = get_config()
    assert config is not None
    assert isinstance(config, dict)
    
    # 测试获取特定部分
    llm_config = get_config("llm")
    assert llm_config is not None
    assert "model" in llm_config


def test_update_config(tmpdir):
    """测试更新配置"""
    # 创建测试配置文件
    test_config = {
        "test": {
            "value": 123
        }
    }
    
    config_path = os.path.join(tmpdir, "test_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(test_config, f)
    
    # 初始化配置管理器
    config_manager = ConfigManager(config_path)
    
    # 更新配置
    new_config = {
        "test": {
            "value": 456
        }
    }
    
    result = config_manager.update_config(new_config)
    assert result is True
    
    # 检查配置是否已更新
    assert config_manager.config["test"]["value"] == 456
    
    # 检查文件是否已更新
    with open(config_path, "r", encoding="utf-8") as f:
        saved_config = json.load(f)
        assert saved_config["test"]["value"] == 456
