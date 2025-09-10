from py2neo import Graph
from transformers import pipeline
import os
from typing import List, Dict, Any, Optional

class DSAGraphQA:
    """DSA知识图谱问答系统
    
    提供三个主要接口：
    1. find_entity_relations: 查找实体的所有相关关系
    2. find_entities_by_relation: 根据关系查找相关实体
    3. find_relation_by_entities: 查找两个实体之间的关系（支持双向查找）
    """
    def __init__(self,neo4j_uri,username,password):
        """初始化图数据库连接和NLP模型"""
        #1.连接Neo4j数据库
        self.graph=Graph(neo4j_uri, auth=(username, password))
        # 数据库中实际的关系类型（中文）
        self.relation_types = ["依赖", "包含", "属于", "同义", "相对", "拥有", "属性"]
        
       

    def find_entity_relations(self, entities: List[str], confidence_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """接口1: 接收实体列表，查找所有相关的关系和实体"""
        if not entities:
            raise ValueError("实体列表不能为空")
        
        query = f"""
        MATCH (src)-[r]->(dst)
        WHERE src.name IN {entities} OR dst.name IN {entities}
        RETURN 
          src.name AS source, 
          type(r) AS relation, 
          dst.name AS target,
          r.confidence AS confidence,
          r.source_sentence AS source_sentence
        ORDER BY r.confidence DESC
        """
        
        results = self.graph.run(query).data()
        valid_results = [r for r in results if r['confidence'] > confidence_threshold]
        
        
        
        return valid_results
    
    def find_entities_by_relation(self, entities: List[str], relation: str, confidence_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """接口2: 接收实体和关系，找到有这个关系的其他实体"""
        if not entities:
            raise ValueError("实体列表不能为空")
        if not relation:
            raise ValueError("关系类型不能为空")
        
        
        query = f"""
        MATCH (src)-[r:{relation}]->(dst)
        WHERE src.name IN {entities} OR dst.name IN {entities}
        RETURN 
          src.name AS source, 
          type(r) AS relation, 
          dst.name AS target,
          r.confidence AS confidence,
          r.source_sentence AS source_sentence
        ORDER BY r.confidence DESC
        """
        
        results = self.graph.run(query).data()
        valid_results = [r for r in results if r['confidence'] > confidence_threshold]
        
      
        return valid_results

    def find_relation_by_entities(self, entities: List[str], confidence_threshold: float = 0.8, bidirectional: bool = True) -> List[Dict[str, Any]]:
        """接口3: 接收两个实体，找到这两个实体之间的关系
        
        Args:
            entities: 包含两个实体的列表
            confidence_threshold: 置信度阈值，默认0.8
            bidirectional: 是否查找双向关系，默认True
            
        Returns:
            包含关系信息的列表，每个元素包含source、relation、target、confidence、source_sentence
        """
        if len(entities) != 2:
            raise ValueError("实体列表必须包含两个实体")
        
        entity1, entity2 = entities[0], entities[1]
        
        if bidirectional:
            # 查找双向关系：A->B 和 B->A
            query = f"""
            MATCH (src)-[r]->(dst)
            WHERE (src.name = '{entity1}' AND dst.name = '{entity2}') 
               OR (src.name = '{entity2}' AND dst.name = '{entity1}')
            RETURN 
              src.name AS source, 
              type(r) AS relation, 
              dst.name AS target,
              r.confidence AS confidence,
              r.source_sentence AS source_sentence,
              CASE 
                WHEN src.name = '{entity1}' AND dst.name = '{entity2}' THEN 'forward'
                ELSE 'reverse'
              END AS direction
            ORDER BY r.confidence DESC
            """
        else:
            # 只查找顺向关系：A->B
            query = f"""
            MATCH (src)-[r]->(dst)
            WHERE src.name = '{entity1}' AND dst.name = '{entity2}'
            RETURN 
              src.name AS source, 
              type(r) AS relation, 
              dst.name AS target,
              r.confidence AS confidence,
              r.source_sentence AS source_sentence,
              'forward' AS direction
            ORDER BY r.confidence DESC
            """
        
        results = self.graph.run(query).data()
        valid_results = [r for r in results if r['confidence'] > confidence_threshold]
        
 
        return valid_results
    
    def check_entities_exist(self, entities: List[str]) -> Dict[str, bool]:
        """检查实体是否在数据库中存在
        
        Args:
            entities: 要检查的实体列表
            
        Returns:
            字典，键为实体名，值为是否存在
        """
        if not entities:
            return {}
        
        query = f"""
        UNWIND {entities} AS entity_name
        OPTIONAL MATCH (n) WHERE n.name = entity_name
        RETURN entity_name, n IS NOT NULL AS exists
        """
        
        results = self.graph.run(query).data()
        return {r['entity_name']: r['exists'] for r in results}
    
    def get_entities_containing(self, keyword: str) -> List[str]:
        """获取包含指定关键词的实体列表
        
        Args:
            keyword: 关键词
            
        Returns:
            包含该关键词的实体名称列表
        """
        if not keyword:
            return []
        
        query = f"""
        MATCH (n) 
        WHERE n.name CONTAINS '{keyword}'
        RETURN n.name AS name
        ORDER BY n.name
        """
        
        results = self.graph.run(query).data()
        return [r['name'] for r in results]

    def query_graph(self, question: str, entities) -> Dict[str, Any]:
        """保持向后兼容的核心查询流程"""
        # 兼容原有接口
        if isinstance(entities, dict):
            if 'relation' in entities:
                results = self.find_entities_by_relation(
                    entities['entities'], 
                    entities['relation']
                )
            else:
                results = self.find_entity_relations(entities['entities'])
        else:
            results = self.find_entity_relations(entities)
        
        return self._format_results(question, results)



    def _format_results(self, question: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成带溯源信息的回答"""
        if not results:
            return {
                "question": question,
                "answer": "暂无可靠知识支持",
                "knowledge_trace": []
            }

        #1.生成核心答案
        main_answer = f"{results[0]['source']} → {results[0]['relation']} → {results[0]['target']}"

        #2.构造溯源信息
        trace_info = []
        for r in results:
            trace_info.append({
                "path": f"{r['source']} → {r['relation']} → {r['target']}",
                "confidence": r['confidence'],
                "source_sentence": r['source_sentence']
            })
        
        return {
            "question": question,
            "answer": main_answer,
            "knowledge_trace": trace_info
        }