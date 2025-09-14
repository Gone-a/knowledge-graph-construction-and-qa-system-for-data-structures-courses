# -*- coding: utf-8 -*-
"""
实体关系提取模块
从knowledge_base导入知识库定义
"""

from .knowledge_base import KNOWLEDGE_BASE

# 为了兼容性，也可以直接导出
__all__ = ['KNOWLEDGE_BASE']