"""测试配置模块的环境变量处理功能"""

import os
import json
import tempfile
from unittest import mock
from pathlib import Path

import pytest
from src.config import ConfigManager


def test_environment_variable_substitution():
    """测试环境变量替换功能"""
    # 创建一个测试配置文件
    config_content = {
        "test": {
            "api_key": "${TEST_API_KEY}",
            "nested": {
                "value": "prefix_${NESTED_VAR}_suffix"
            },
            "normal_value": "普通值"
        }
    }
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp:
        json.dump(config_content, temp)
        temp_file_path = temp.name
    
    try:
        # 模拟环境变量
        with mock.patch.dict(os.environ, {
            'TEST_API_KEY': 'test_key_value',
            'NESTED_VAR': 'nested_value'
        }):
            # 初始化配置管理器
            config_manager = ConfigManager(temp_file_path, env_file=None)  # 不使用env文件
            
            # 验证环境变量是否被正确替换
            assert config_manager.config['test']['api_key'] == 'test_key_value'
            assert config_manager.config['test']['nested']['value'] == 'prefix_nested_value_suffix'
            assert config_manager.config['test']['normal_value'] == '普通值'
    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def test_missing_environment_variable():
    """测试缺失环境变量的情况"""
    # 创建一个测试配置文件
    config_content = {
        "test": {
            "api_key": "${MISSING_API_KEY}"
        }
    }
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp:
        json.dump(config_content, temp)
        temp_file_path = temp.name
    
    try:
        # 确保环境变量不存在
        with mock.patch.dict(os.environ, {}, clear=True):
            # 初始化配置管理器
            config_manager = ConfigManager(temp_file_path, env_file=None)  # 不使用env文件
            
            # 验证值保持不变
            assert config_manager.config['test']['api_key'] == '${MISSING_API_KEY}'
    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def test_env_file_loading():
    """测试从环境变量文件加载"""
    # 创建一个测试配置文件
    config_content = {
        "test": {
            "api_key": "${ENV_FILE_API_KEY}"
        }
    }
    
    # 创建临时环境变量文件
    env_content = "ENV_FILE_API_KEY=from_env_file_value"
      # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_config, \
         tempfile.NamedTemporaryFile(mode='w+', suffix='.env', delete=False) as temp_env:
        json.dump(config_content, temp_config)
        temp_config_path = temp_config.name
        
        temp_env.write(env_content)  # 直接写入字符串，而不是字节
        temp_env_path = temp_env.name
    
    try:
        # 清除可能影响测试的环境变量
        with mock.patch.dict(os.environ, {}, clear=True):
            # 初始化配置管理器，指定环境变量文件
            config_manager = ConfigManager(temp_config_path, env_file=temp_env_path)
            
            # 验证环境变量是否被正确加载和替换
            assert config_manager.config['test']['api_key'] == 'from_env_file_value'
    finally:
        # 清理临时文件
        if os.path.exists(temp_config_path):
            os.unlink(temp_config_path)
        if os.path.exists(temp_env_path):
            os.unlink(temp_env_path)
