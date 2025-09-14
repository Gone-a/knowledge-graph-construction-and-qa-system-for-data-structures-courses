# -*- coding: utf-8 -*-
"""
意图识别模块
提供NLU模型加载、意图识别和实体关系提取功能
"""

import torch
import json
import os
from typing import Dict, List, Any
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import logging

class IntentRecognizer:
    """意图识别器
    
    负责加载NLU模型，进行意图识别和实体关系提取
    """
    
    def __init__(self, model_path: str, knowledge_base: Dict[str, Any]):
        """
        初始化意图识别器
        
        Args:
            model_path: NLU模型路径
            knowledge_base: 知识库字典，包含entities和relations
        """
        self.model_path = model_path
        self.knowledge_base = knowledge_base
        self.tokenizer = None
        self.model = None
        self.id2label = None
        self.entities_kb = knowledge_base.get("entities", {})
        self.relations_kb = knowledge_base.get("relations", {})
        
        self._load_model()
        
    def _load_model(self):
        """加载NLU模型"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
            
            # 加载标签映射
            label_map_path = os.path.join(self.model_path, "label_map.json")
            with open(label_map_path, 'r', encoding='utf-8') as f:
                label_map = json.load(f)
                self.id2label = {int(k): v for k, v in label_map['id2label'].items()}
                
            logging.info("意图识别模型加载成功")
            
        except Exception as e:
            logging.error(f"加载意图识别模型失败: {e}")
            raise
    

    
    def recognize_intent(self, text: str) -> str:
        """
        识别文本意图
        
        Args:
            text: 输入文本
            
        Returns:
            str: 识别的意图类别
        """
        if not self.model or not self.tokenizer:
            raise RuntimeError("模型未正确加载")
            
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
            
            with torch.no_grad():
                logits = self.model(**inputs).logits
                
            predicted_id = logits.argmax().item()
            intent = self.id2label.get(predicted_id, "unknown")
            
            return intent
            
        except Exception as e:
            logging.error(f"意图识别失败: {e}")
            return "unknown"
    
    def extract_entities(self, text: str) -> List[str]:
        """
        从文本中提取实体
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 提取的实体列表
        """
        found_entities = []
        
        for entity_id, synonyms in self.entities_kb.items():
            for synonym in synonyms:
                if synonym in text:
                    found_entities.append(entity_id)
                    break
                    
        return found_entities
    
    def extract_relations(self, text: str) -> List[str]:
        """
        从文本中提取关系
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 提取的关系列表
        """
        found_relations = []
        
        for relation_id, synonyms in self.relations_kb.items():
            for synonym in synonyms:
                if synonym in text:
                    found_relations.append(relation_id)
                    break
                    
        return found_relations
    
    def understand(self, text: str) -> Dict[str, Any]:
        """
        综合理解文本，返回意图、实体和关系
        
        Args:
            text: 输入文本
            
        Returns:
            Dict: 包含intent、entities、relations的字典
        """
        intent = self.recognize_intent(text)
        entities = self.extract_entities(text)
        relations = self.extract_relations(text)
        
        return {
            "intent": intent,
            "entities": entities,
            "relations": relations
        }