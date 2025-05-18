"""LLM提供者模块，负责与各种LLM API进行交互"""

import json
import logging
import os
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod

# 尝试导入OpenAI和httpx库
try:
    import openai
    from openai import OpenAI, AzureOpenAI
    import httpx
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False

# 确保requests库始终可用
import requests

# 配置日志
logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """LLM提供者的抽象基类，定义了与LLM交互的通用接口"""
    
    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """
        生成文本的抽象方法
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            **kwargs: 额外参数
            
        Returns:
            生成的文本，失败时返回None
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API实现（使用官方SDK或直接请求）"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", temperature: float = 0.3, max_tokens: int = 2000):
        """初始化OpenAI提供者"""
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 根据是否可用OpenAI SDK决定使用哪种实现方式
        if OPENAI_SDK_AVAILABLE:
            self.client = OpenAI(api_key=api_key)
            self._implementation = "sdk"
        else:
            self._implementation = "requests"
            self.api_base = "https://api.openai.com/v1/chat/completions"
    
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """调用OpenAI API生成文本"""
        try:
            # 构建消息
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            logger.debug(f"调用OpenAI API，模型: {self.model}, prompt长度: {len(prompt)}")
            
            if self._implementation == "sdk":
                # 使用SDK调用
                response = self.client.chat.completions.create(
                    model=kwargs.get("model", self.model),
                    messages=messages,
                    temperature=kwargs.get("temperature", self.temperature),
                    max_tokens=kwargs.get("max_tokens", self.max_tokens)
                )
                return response.choices[0].message.content
            else:
                # 使用requests调用
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                data = {
                    "model": kwargs.get("model", self.model),
                    "messages": messages,
                    "temperature": kwargs.get("temperature", self.temperature),
                    "max_tokens": kwargs.get("max_tokens", self.max_tokens)
                }
                
                response = requests.post(
                    self.api_base,
                    headers=headers,
                    json=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"OpenAI API调用失败: {response.status_code} - {response.text}")
                    return None
            
        except Exception as e:
            logger.exception(f"OpenAI调用异常: {e}")
            return None


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI API实现（使用官方SDK或直接请求）"""
    
    def __init__(self, api_key: str, endpoint: str, deployment_name: str, 
                 temperature: float = 0.3, max_tokens: int = 2000):
        """初始化Azure OpenAI提供者"""
        self.api_key = api_key
        self.endpoint = endpoint
        self.deployment_name = deployment_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_version = "2023-05-15"  # 可配置
        
        # 根据是否可用OpenAI SDK决定使用哪种实现方式
        if OPENAI_SDK_AVAILABLE:
            self.client = AzureOpenAI(
                api_key=api_key,
                api_version=self.api_version,
                azure_endpoint=endpoint
            )
            self._implementation = "sdk"
        else:
            self._implementation = "requests"
            self.api_base = f"{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version={self.api_version}"
    
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """调用Azure OpenAI API生成文本"""
        try:
            # 构建消息
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            logger.debug(f"调用Azure OpenAI API，部署名称: {self.deployment_name}, prompt长度: {len(prompt)}")
            
            if self._implementation == "sdk":
                # 使用SDK调用
                response = self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=messages,
                    temperature=kwargs.get("temperature", self.temperature),
                    max_tokens=kwargs.get("max_tokens", self.max_tokens)
                )
                return response.choices[0].message.content
            else:
                # 使用requests调用
                headers = {
                    "Content-Type": "application/json",
                    "api-key": self.api_key
                }
                
                data = {
                    "messages": messages,
                    "temperature": kwargs.get("temperature", self.temperature),
                    "max_tokens": kwargs.get("max_tokens", self.max_tokens)
                }
                
                response = requests.post(
                    self.api_base,
                    headers=headers,
                    json=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"Azure OpenAI API调用失败: {response.status_code} - {response.text}")
                    return None
            
        except Exception as e:
            logger.exception(f"Azure OpenAI调用异常: {e}")
            return None


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API实现"""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229", temperature: float = 0.3, max_tokens: int = 2000):
        """初始化Anthropic提供者"""
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_base = "https://api.anthropic.com/v1/messages"
        
        # 使用httpx库进行API调用（如果可用）
        if OPENAI_SDK_AVAILABLE:
            self.client = httpx.Client(timeout=90.0)  # 设置更长的超时时间
            self._implementation = "httpx"
        else:
            self._implementation = "requests"
    
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """调用Anthropic API生成文本"""
        try:
            # 构建API请求
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            
            data = {
                "model": kwargs.get("model", self.model),
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "messages": [{"role": "user", "content": prompt}]
            }
            
            if system_prompt:
                data["system"] = system_prompt
            
            # 调用API
            logger.debug(f"调用Anthropic API，模型: {self.model}, prompt长度: {len(prompt)}")
            
            if self._implementation == "httpx":
                # 使用httpx调用
                response = self.client.post(
                    self.api_base,
                    headers=headers,
                    json=data
                )
            else:
                # 使用requests调用
                response = requests.post(
                    self.api_base,
                    headers=headers,
                    json=data,
                    timeout=90
                )
            
            if response.status_code == 200:
                result = response.json()
                return result["content"][0]["text"]
            else:
                logger.error(f"Anthropic API调用失败: {response.status_code} - {response.text}")
                return None
            
        except Exception as e:
            logger.exception(f"Anthropic调用异常: {e}")
            return None


# 工厂函数创建LLM提供者
def create_llm_provider(provider_type: str, config: Dict[str, Any]) -> Optional[LLMProvider]:
    """
    创建LLM提供者实例
    
    Args:
        provider_type: 提供者类型，如 'openai', 'azure', 'anthropic'
        config: 配置参数
    
    Returns:
        LLM提供者实例，失败时返回None
    """
    try:
        if provider_type.lower() == 'openai':
            return OpenAIProvider(
                api_key=config.get('api_key'),
                model=config.get('model', 'gpt-4'),
                temperature=config.get('temperature', 0.3),
                max_tokens=config.get('max_tokens', 2000)
            )
        elif provider_type.lower() == 'azure':
            return AzureOpenAIProvider(
                api_key=config.get('api_key'),
                endpoint=config.get('endpoint'),
                deployment_name=config.get('deployment_name'),
                temperature=config.get('temperature', 0.3),
                max_tokens=config.get('max_tokens', 2000)
            )
        elif provider_type.lower() == 'anthropic':
            return AnthropicProvider(
                api_key=config.get('api_key'),
                model=config.get('model', 'claude-3-opus-20240229'),
                temperature=config.get('temperature', 0.3),
                max_tokens=config.get('max_tokens', 2000)
            )
        else:
            logger.error(f"不支持的LLM提供者类型: {provider_type}")
            return None
    except Exception as e:
        logger.exception(f"创建LLM提供者实例失败: {e}")
        return None
