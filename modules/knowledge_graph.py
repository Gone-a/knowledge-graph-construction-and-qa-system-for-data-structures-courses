# -*- coding: utf-8 -*-
"""
知识图谱查询模块
提供Neo4j图数据库查询功能，支持实体关系查询和图谱问答
"""

from py2neo import Graph
import os
from typing import List, Dict, Any, Optional
import logging
import re
import time
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import threading

class KnowledgeGraphQuery:
    """知识图谱查询器
    
    提供高效的图数据库查询接口，支持缓存和性能优化
    """
    
    # 常量定义
    MAX_ENTITY_LENGTH = 100
    MAX_ENTITIES_PER_QUERY = 50
    DEFAULT_CONFIDENCE_THRESHOLD = 0.8
    QUERY_RESULT_LIMIT = 1000
    FLOAT_PRECISION = 1e-10
    
    def __init__(self, neo4j_uri: str, username: str, password: str, max_workers: int = 4):
        """
        初始化知识图谱查询器
        
        Args:
            neo4j_uri: Neo4j数据库URI
            username: 用户名
            password: 密码
            max_workers: 最大并发工作线程数
            
        Raises:
            ConnectionError: 数据库连接失败
            ValueError: 参数验证失败
        """
        self._validate_params(neo4j_uri, username, password)
        
        try:
            # 连接Neo4j数据库
            self.graph = Graph(neo4j_uri, auth=(username, password))
            # 测试连接
            self.graph.run("RETURN 1").data()
            logging.info("Neo4j数据库连接成功")
            
        except Exception as e:
            logging.error(f"Neo4j数据库连接失败: {e}")
            raise ConnectionError(f"无法连接到Neo4j数据库: {e}")
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # 查询缓存
        self.query_cache = {}
        self.cache_lock = threading.RLock()
        self.cache_ttl = 600  # 10分钟缓存
    
    def _validate_params(self, neo4j_uri: str, username: str, password: str):
        """验证初始化参数"""
        if not neo4j_uri or not isinstance(neo4j_uri, str):
            raise ValueError("neo4j_uri不能为空且必须是字符串")
        if not username or not isinstance(username, str):
            raise ValueError("username不能为空且必须是字符串")
        if not password or not isinstance(password, str):
            raise ValueError("password不能为空且必须是字符串")
    
    def _get_cache_key(self, query_type: str, *args) -> str:
        """生成缓存键"""
        return f"{query_type}:{'|'.join(str(arg) for arg in args)}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """获取缓存结果"""
        with self.cache_lock:
            if cache_key in self.query_cache:
                result, timestamp = self.query_cache[cache_key]
                if time.time() - timestamp < self.cache_ttl:
                    return result
                else:
                    del self.query_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: Any):
        """缓存查询结果"""
        with self.cache_lock:
            self.query_cache[cache_key] = (result, time.time())
            # 清理过期缓存
            current_time = time.time()
            expired_keys = [
                key for key, (_, timestamp) in self.query_cache.items()
                if current_time - timestamp >= self.cache_ttl
            ]
            for key in expired_keys:
                del self.query_cache[key]

    def _validate_entities(self, entities: List[str]) -> List[str]:
        """验证和清理实体列表"""
        if not entities:
            return []
        
        # 过滤和清理实体
        cleaned_entities = []
        for entity in entities[:self.MAX_ENTITIES_PER_QUERY]:
            if isinstance(entity, str) and len(entity.strip()) <= self.MAX_ENTITY_LENGTH:
                cleaned_entity = re.sub(r'[^\w\s\u4e00-\u9fff]', '', entity.strip())
                if cleaned_entity:
                    cleaned_entities.append(cleaned_entity)
        
        return cleaned_entities
    
    def find_entity_relations(self, entity: str, confidence_threshold: float = None) -> List[Dict[str, Any]]:
        """
        查找实体的所有相关关系（带缓存）
        
        Args:
            entity: 实体名称
            confidence_threshold: 置信度阈值
            
        Returns:
            List[Dict]: 关系列表
        """
        if confidence_threshold is None:
            confidence_threshold = self.DEFAULT_CONFIDENCE_THRESHOLD
        
        # 检查缓存
        cache_key = self._get_cache_key('entity_relations', entity, confidence_threshold)
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            logging.info(f"返回缓存的实体关系: {entity}")
            return cached_result
            
        try:
            # 清理实体名称
            cleaned_entities = self._validate_entities([entity])
            if not cleaned_entities:
                return []
            
            entity = cleaned_entities[0]
            
            # 优化的Cypher查询，使用索引
            cypher_query = """
            MATCH (n)-[r]-(m)
            WHERE n.name CONTAINS $entity OR m.name CONTAINS $entity
            AND (r.confidence IS NULL OR r.confidence >= $threshold)
            RETURN DISTINCT 
                n.name as entity1, 
                type(r) as relation, 
                m.name as entity2,
                COALESCE(r.confidence, 1.0) as confidence
            ORDER BY confidence DESC
            LIMIT $limit
            """
            
            start_time = time.time()
            result = self.graph.run(cypher_query, 
                                  entity=entity, 
                                  threshold=confidence_threshold,
                                  limit=self.QUERY_RESULT_LIMIT).data()
            
            query_time = time.time() - start_time
            logging.info(f"找到实体 '{entity}' 的 {len(result)} 个关系，查询耗时: {query_time:.3f}s")
            
            # 缓存结果
            self._cache_result(cache_key, results)
            
            return results
            
        except Exception as e:
            logging.error(f"查找实体关系失败: {e}")
            return []
    
    def find_entities_by_relation(self, entities: List[str], relation: str, 
                                confidence_threshold: float = None) -> List[Dict[str, Any]]:
        """
        根据关系和实体查找相关实体（带缓存）
        
        Args:
            entities: 实体列表
            relation: 关系类型
            confidence_threshold: 置信度阈值
            
        Returns:
            List[Dict]: 查询结果
        """
        if confidence_threshold is None:
            confidence_threshold = self.DEFAULT_CONFIDENCE_THRESHOLD
        
        # 检查缓存
        cache_key = self._get_cache_key('entities_by_relation', str(entities), relation, confidence_threshold)
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            logging.info(f"返回缓存的关系查询结果: {relation}")
            return cached_result
            
        try:
            # 验证和清理输入
            cleaned_entities = self._validate_entities(entities)
            if not cleaned_entities or not relation:
                return []
            
            relation = re.sub(r'[^\w\s\u4e00-\u9fff]', '', relation.strip())
            
            # 构建Cypher查询
            cypher_query = """
            MATCH (n)-[r]-(m)
            WHERE (n.name IN $entities OR m.name IN $entities)
            AND (type(r) CONTAINS $relation OR r.name CONTAINS $relation)
            AND (r.confidence IS NULL OR r.confidence >= $threshold)
            RETURN DISTINCT 
                n.name as entity1, 
                type(r) as relation_type,
                r.name as relation_name,
                m.name as entity2,
                COALESCE(r.confidence, 1.0) as confidence
            ORDER BY confidence DESC
            LIMIT $limit
            """
            
            start_time = time.time()
            result = self.graph.run(cypher_query,
                                  entities=cleaned_entities,
                                  relation=relation,
                                  threshold=confidence_threshold,
                                  limit=self.QUERY_RESULT_LIMIT).data()
            
            query_time = time.time() - start_time
            logging.info(f"根据关系 '{relation}' 找到 {len(result)} 个相关实体，查询耗时: {query_time:.3f}s")
            
            # 缓存结果
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logging.error(f"根据关系查找实体失败: {e}")
            return []
    
    def find_relation_by_entities(self, entities: List[str], 
                                confidence_threshold: float = None,
                                bidirectional: bool = True,
                                include_indirect: bool = True) -> List[Dict[str, Any]]:
        """
        查找两个实体之间的关系（支持直接和间接关系，带缓存）
        
        Args:
            entities: 实体列表（至少2个）
            confidence_threshold: 置信度阈值
            bidirectional: 是否双向查找
            include_indirect: 是否包含间接关系
            
        Returns:
            List[Dict]: 关系列表
        """
        if confidence_threshold is None:
            confidence_threshold = self.DEFAULT_CONFIDENCE_THRESHOLD
        
        # 检查缓存
        cache_key = self._get_cache_key('relation_by_entities', str(entities), confidence_threshold, bidirectional, include_indirect)
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            logging.info(f"返回缓存的实体关系查询结果: {entities[:2]}")
            return cached_result
            
        try:
            # 验证输入
            cleaned_entities = self._validate_entities(entities)
            if len(cleaned_entities) < 2:
                return []
            
            entity1, entity2 = cleaned_entities[0], cleaned_entities[1]
            results = []
            
            # 首先查找直接关系
            if bidirectional:
                direct_query = """
                MATCH (n)-[r]-(m)
                WHERE ((n.name = $entity1 AND m.name = $entity2) OR
                       (n.name = $entity2 AND m.name = $entity1))
                AND (r.confidence IS NULL OR r.confidence >= $threshold)
                RETURN DISTINCT 
                    n.name as entity1, 
                    type(r) as relation_type,
                    r.name as relation_name,
                    m.name as entity2,
                    COALESCE(r.confidence, 1.0) as confidence,
                    'direct' as relation_path
                ORDER BY confidence DESC
                LIMIT $limit
                """
            else:
                direct_query = """
                MATCH (n)-[r]->(m)
                WHERE n.name = $entity1 AND m.name = $entity2
                AND (r.confidence IS NULL OR r.confidence >= $threshold)
                RETURN DISTINCT 
                    n.name as entity1, 
                    type(r) as relation_type,
                    r.name as relation_name,
                    m.name as entity2,
                    COALESCE(r.confidence, 1.0) as confidence,
                    'direct' as relation_path
                ORDER BY confidence DESC
                LIMIT $limit
                """
            
            direct_results = self.graph.run(direct_query,
                                          entity1=entity1,
                                          entity2=entity2,
                                          threshold=confidence_threshold,
                                          limit=self.QUERY_RESULT_LIMIT).data()
            results.extend(direct_results)
            
            # 如果没有直接关系且允许间接关系，查找间接关系
            if not direct_results and include_indirect:
                if bidirectional:
                    indirect_query = """
                    MATCH (n)-[r1]-(middle)-[r2]-(m)
                    WHERE ((n.name = $entity1 AND m.name = $entity2) OR
                           (n.name = $entity2 AND m.name = $entity1))
                    AND (r1.confidence IS NULL OR r1.confidence >= $threshold)
                    AND (r2.confidence IS NULL OR r2.confidence >= $threshold)
                    RETURN DISTINCT 
                        n.name as entity1, 
                        type(r1) + ' -> ' + middle.name + ' -> ' + type(r2) as relation_type,
                        middle.name as relation_name,
                        m.name as entity2,
                        COALESCE(r1.confidence * r2.confidence, 0.8) as confidence,
                        'indirect' as relation_path
                    ORDER BY confidence DESC
                    LIMIT 10
                    """
                else:
                    indirect_query = """
                    MATCH (n)-[r1]->(middle)-[r2]->(m)
                    WHERE n.name = $entity1 AND m.name = $entity2
                    AND (r1.confidence IS NULL OR r1.confidence >= $threshold)
                    AND (r2.confidence IS NULL OR r2.confidence >= $threshold)
                    RETURN DISTINCT 
                        n.name as entity1, 
                        type(r1) + ' -> ' + middle.name + ' -> ' + type(r2) as relation_type,
                        middle.name as relation_name,
                        m.name as entity2,
                        COALESCE(r1.confidence * r2.confidence, 0.8) as confidence,
                        'indirect' as relation_path
                    ORDER BY confidence DESC
                    LIMIT 10
                    """
                
                indirect_results = self.graph.run(indirect_query,
                                                 entity1=entity1,
                                                 entity2=entity2,
                                                 threshold=confidence_threshold).data()
                results.extend(indirect_results)
            
            return results
            
        except Exception as e:
            logging.error(f"查找实体间关系失败: {e}")
            return []
    
    def get_entities_containing(self, keyword: str, limit: int = 50) -> List[str]:
        """
        获取包含关键词的实体
        
        Args:
            keyword: 关键词
            limit: 结果限制
            
        Returns:
            List[str]: 实体列表
        """
        try:
            if not keyword or not isinstance(keyword, str):
                return []
            
            keyword = re.sub(r'[^\w\s\u4e00-\u9fff]', '', keyword.strip())
            if not keyword:
                return []
            
            cypher_query = """
            MATCH (n)
            WHERE n.name CONTAINS $keyword
            RETURN DISTINCT n.name as entity
            ORDER BY n.name
            LIMIT $limit
            """
            
            result = self.graph.run(cypher_query, keyword=keyword, limit=limit).data()
            return [record['entity'] for record in result]
            
        except Exception as e:
            logging.error(f"搜索实体失败: {e}")
            return []
    
    def query_graph(self, question: str, entities: List[str] = None) -> Dict[str, Any]:
        """
        通用图查询接口
        
        Args:
            question: 问题文本
            entities: 相关实体列表
            
        Returns:
            Dict: 查询结果
        """
        try:
            result = {
                'question': question,
                'entities': entities or [],
                'relations': [],
                'answer': '',
                'confidence': 0.0
            }
            
            if entities and len(entities) >= 2:
                # 查找实体间关系
                relations = self.find_relation_by_entities(entities)
                result['relations'] = relations
                
                if relations:
                    # 生成简单答案
                    rel = relations[0]
                    result['answer'] = f"{rel['entity1']}与{rel['entity2']}的关系是：{rel.get('relation_name', rel.get('relation_type', '未知'))}"
                    result['confidence'] = rel.get('confidence', 0.0)
            
            elif entities and len(entities) == 1:
                # 查找单个实体的关系
                relations = self.find_entity_relations(entities[0])
                result['relations'] = relations[:10]  # 限制返回数量
                
                if relations:
                    result['answer'] = f"{entities[0]}相关的关系有：" + ", ".join([f"{r['relation']}" for r in relations[:5]])
                    result['confidence'] = max([r.get('confidence', 0.0) for r in relations])
            
            return result
            
        except Exception as e:
            logging.error(f"图查询失败: {e}")
            return {
                'question': question,
                'entities': entities or [],
                'relations': [],
                'answer': '查询失败',
                'confidence': 0.0
            }
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'graph'):
            # py2neo没有显式的close方法，但可以清理缓存
            self.find_entity_relations.cache_clear()
            logging.info("知识图谱连接已关闭")

# 为了兼容性，保留原有的类名
DSAGraphQAFixed = KnowledgeGraphQuery