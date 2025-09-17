# -*- coding: utf-8 -*-
"""
配置管理模块
统一管理应用程序的所有配置信息
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

class ConfigManager:
    """配置管理器
    
    负责加载和管理应用程序的所有配置
    """
    
    def __init__(self):
        """初始化配置管理器"""
        load_dotenv()
        self._config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载所有配置"""
        config = {
            # API配置
            'api': {
                'api_key': os.getenv('DEEPSEEK_API_KEY', 'sk-fbf0cbed7c3e4a778a6aca7379791de4'),
                'model_name': os.getenv('DEEPSEEK_MODEL_NAME', 'deepseek-chat'),
                'base_url': os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1'),
            },
            
            # 模型配置
            'model': {
                'nlu_model_path': os.getenv('NLU_MODEL_PATH', '/root/KG_inde/my_intent_model'),
                'max_sequence_length': int(os.getenv('MAX_SEQUENCE_LENGTH', '512')),
                'batch_size': int(os.getenv('BATCH_SIZE', '32')),
            },
            
            # 数据库配置
            'database': {
                'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
                'user_name': os.getenv('NEO4J_USERNAME', 'neo4j'),
                'password': os.getenv('NEO4J_PASSWORD', os.getenv('NEO4J_KEY', 'password')),
                'browserUrl': os.getenv('NEO4J_BROWSER_URL', 'http://localhost:7474/browser/'),
                'connection_timeout': int(os.getenv('NEO4J_TIMEOUT', '30')),
            },
            
            # 服务器配置
            'server': {
                'host': os.getenv('SERVER_HOST', 'localhost'),
                'port': int(os.getenv('SERVER_PORT', '5000')),
                'debug': os.getenv('DEBUG', 'False').lower() == 'true',
                'cors_origins': os.getenv('CORS_ORIGINS', 'http://localhost:8080').split(','),
            },
            
            # 大模型配置
            'llm': {
                'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '2000')),
                'temperature': float(os.getenv('LLM_TEMPERATURE', '0.7')),
            }
        }
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键（如 'api.deepseek_api_key'）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        # 导航到最后一级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return self._config.get('api', {})
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self._config.get('database', {})
    
    def get_server_config(self) -> Dict[str, Any]:
        """获取服务器配置"""
        return self._config.get('server', {})
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取大模型配置"""
        return self._config.get('llm', {})
    

    

    


# 全局配置实例
_config_manager = None

def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_config(key: str, default: Any = None) -> Any:
    """快捷方法：获取配置值"""
    return get_config_manager().get(key, default)