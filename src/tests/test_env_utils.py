"""测试环境变量工具函数"""

import os
import sys
from unittest import mock

import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 直接导入模块
from src.utils.env_utils import get_env, get_bool_env, get_int_env, get_float_env


def test_get_env():
    """测试基本环境变量获取"""
    with mock.patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
        assert get_env('TEST_VAR') == 'test_value'
        assert get_env('NONEXISTENT_VAR') is None
        assert get_env('NONEXISTENT_VAR', 'default') == 'default'


def test_get_bool_env():
    """测试布尔环境变量获取"""
    test_values = {
        'TEST_TRUE1': 'true',
        'TEST_TRUE2': 'True',
        'TEST_TRUE3': 'yes',
        'TEST_TRUE4': '1',
        'TEST_FALSE1': 'false',
        'TEST_FALSE2': 'no',
        'TEST_FALSE3': '0',
        'TEST_INVALID': 'invalid'
    }
    
    with mock.patch.dict(os.environ, test_values):
        # 测试真值
        assert get_bool_env('TEST_TRUE1') is True
        assert get_bool_env('TEST_TRUE2') is True
        assert get_bool_env('TEST_TRUE3') is True
        assert get_bool_env('TEST_TRUE4') is True
        
        # 测试假值
        assert get_bool_env('TEST_FALSE1') is False
        assert get_bool_env('TEST_FALSE2') is False
        assert get_bool_env('TEST_FALSE3') is False
        
        # 测试无效值
        assert get_bool_env('TEST_INVALID') is False
        
        # 测试默认值
        assert get_bool_env('NONEXISTENT_VAR') is False
        assert get_bool_env('NONEXISTENT_VAR', True) is True


def test_get_int_env():
    """测试整数环境变量获取"""
    test_values = {
        'TEST_INT': '123',
        'TEST_NEGATIVE': '-456',
        'TEST_INVALID': 'not_a_number'
    }
    
    with mock.patch.dict(os.environ, test_values):
        assert get_int_env('TEST_INT') == 123
        assert get_int_env('TEST_NEGATIVE') == -456
        assert get_int_env('TEST_INVALID') is None
        assert get_int_env('TEST_INVALID', 0) == 0
        assert get_int_env('NONEXISTENT_VAR') is None
        assert get_int_env('NONEXISTENT_VAR', 789) == 789


def test_get_float_env():
    """测试浮点数环境变量获取"""
    test_values = {
        'TEST_FLOAT': '3.14',
        'TEST_INT_AS_FLOAT': '42',
        'TEST_NEGATIVE': '-2.718',
        'TEST_INVALID': 'not_a_number'
    }
    
    with mock.patch.dict(os.environ, test_values):
        assert get_float_env('TEST_FLOAT') == 3.14
        assert get_float_env('TEST_INT_AS_FLOAT') == 42.0
        assert get_float_env('TEST_NEGATIVE') == -2.718
        assert get_float_env('TEST_INVALID') is None
        assert get_float_env('TEST_INVALID', 0.0) == 0.0
        assert get_float_env('NONEXISTENT_VAR') is None
        assert get_float_env('NONEXISTENT_VAR', 1.23) == 1.23
