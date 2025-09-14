from py2neo import Graph
from typing import List, Dict, Any

class DSAGraphQAFixed:
    """DSA知识图谱问答系统"""
    
    def __init__(self, neo4j_uri: str, username: str, password: str):
        """初始化图数据库连接"""
        self.graph = Graph(neo4j_uri, auth=(username, password))
        
        # 数据库中实际的关系类型（中文）
        self.relation_types = ["依赖", "包含", "属于", "同义", "相对", "拥有", "属性"]
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
    
    def _validate_entities(self, entities: List[str]) -> List[str]:
        """验证和清理实体列表
        
        Args:
            entities: 实体列表
            
        Returns:
            清理后的实体列表
            
        Raises:
            ValueError: 实体验证失败
            TypeError: 类型错误
        """
        if entities is None:
            raise TypeError("实体列表不能为None")
        
        if not isinstance(entities, list):
            raise TypeError("entities必须是列表类型")
        
        if not entities:
            raise ValueError("实体列表不能为空")
        
        if len(entities) > self.MAX_ENTITIES_PER_QUERY:
            raise ValueError(f"实体数量不能超过{self.MAX_ENTITIES_PER_QUERY}个")
        
        clean_entities = []
        for i, entity in enumerate(entities):
            if entity is None:
                continue
            
            # 转换为字符串并清理
            entity_str = str(entity).strip()
            
            if not entity_str:
                continue
            
            if len(entity_str) > self.MAX_ENTITY_LENGTH:
                raise ValueError(f"第{i+1}个实体名称过长（最大{self.MAX_ENTITY_LENGTH}字符）: {entity_str[:50]}...")
            
            # 基本的安全检查 - 防止明显的注入尝试
            if self._contains_suspicious_patterns(entity_str):
                raise ValueError(f"实体名称包含可疑字符: {entity_str}")
            
            clean_entities.append(entity_str)
        
        if not clean_entities:
            raise ValueError("没有有效的实体")
        
        return clean_entities
    
    def _contains_suspicious_patterns(self, text: str) -> bool:
        """检查文本是否包含可疑的注入模式
        
        Args:
            text: 要检查的文本
            
        Returns:
            是否包含可疑模式
        """
        suspicious_patterns = [
            r"[';]",  # 分号和单引号
            r"\b(DROP|DELETE|CREATE|ALTER|MERGE)\b",  # 危险的Cypher关键词
            r"//",  # 注释符号
            r"/\*.*\*/",  # 块注释
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _validate_confidence_threshold(self, confidence_threshold: float) -> float:
        """验证置信度阈值
        
        Args:
            confidence_threshold: 置信度阈值
            
        Returns:
            验证后的置信度阈值
            
        Raises:
            ValueError: 置信度阈值无效
            TypeError: 类型错误
        """
        if not isinstance(confidence_threshold, (int, float)):
            raise TypeError("置信度阈值必须是数字类型")
        
        if not (0.0 <= confidence_threshold <= 1.0):
            raise ValueError("置信度阈值必须在0.0到1.0之间")
        
        return float(confidence_threshold)
    
    def _execute_query(self, query: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """安全执行Cypher查询
        
        Args:
            query: Cypher查询语句
            parameters: 查询参数
            
        Returns:
            查询结果
            
        Raises:
            Exception: 查询执行失败
        """
        try:
            self.logger.debug(f"执行查询: {query}")
            self.logger.debug(f"参数: {parameters}")
            
            results = self.graph.run(query, **parameters).data()
            
            self.logger.debug(f"查询返回{len(results)}条结果")
            return results
            
        except Exception as e:
            self.logger.error(f"查询执行失败: {e}")
            self.logger.error(f"查询语句: {query}")
            self.logger.error(f"参数: {parameters}")
            raise Exception(f"数据库查询失败: {e}")
    
    def _filter_by_confidence(self, results: List[Dict[str, Any]], 
                            confidence_threshold: float) -> List[Dict[str, Any]]:
        """根据置信度过滤结果
        
        Args:
            results: 查询结果
            confidence_threshold: 置信度阈值
            
        Returns:
            过滤后的结果
        """
        valid_results = []
        for r in results:
            confidence = r.get('confidence')
            if confidence is not None and confidence >= (confidence_threshold - self.FLOAT_PRECISION):
                valid_results.append(r)
        
        return valid_results

    def find_entity_relations(self, entities: List[str], 
                            confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD) -> List[Dict[str, Any]]:
        """接口1: 接收实体列表，查找所有相关的关系和实体
        
        Args:
            entities: 实体列表
            confidence_threshold: 置信度阈值，默认0.8
            
        Returns:
            包含关系信息的列表，每个元素包含source、relation、target、confidence、source_sentence
            
        Raises:
            ValueError: 输入验证失败
            TypeError: 类型错误
            Exception: 查询执行失败
        """
        # 输入验证
        clean_entities = self._validate_entities(entities)
        confidence_threshold = self._validate_confidence_threshold(confidence_threshold)
        
        # 使用参数化查询防止注入
        query = """
        MATCH (src)-[r]->(dst)
        WHERE src.name IN $entities OR dst.name IN $entities
        RETURN 
          src.name AS source, 
          type(r) AS relation, 
          dst.name AS target,
          r.confidence AS confidence,
          r.source_sentence AS source_sentence
        ORDER BY r.confidence DESC
        LIMIT $limit
        """
        
        parameters = {
            'entities': clean_entities,
            'limit': self.QUERY_RESULT_LIMIT
        }
        
        results = self._execute_query(query, parameters)
        valid_results = self._filter_by_confidence(results, confidence_threshold)
        
        return valid_results
    
    def find_entities_by_relation(self, entities: List[str], relation: str, 
                                confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD) -> List[Dict[str, Any]]:
        """接口2: 接收实体和关系，找到有这个关系的其他实体
        
        Args:
            entities: 实体列表
            relation: 关系类型
            confidence_threshold: 置信度阈值，默认0.8
            
        Returns:
            包含关系信息的列表
            
        Raises:
            ValueError: 输入验证失败
            TypeError: 类型错误
            Exception: 查询执行失败
        """
        # 输入验证
        clean_entities = self._validate_entities(entities)
        confidence_threshold = self._validate_confidence_threshold(confidence_threshold)
        
        if not relation or not isinstance(relation, str):
            raise ValueError("关系类型不能为空且必须是字符串")
        
        relation = relation.strip()
        if not relation:
            raise ValueError("关系类型不能为空")
        
        if self._contains_suspicious_patterns(relation):
            raise ValueError(f"关系类型包含可疑字符: {relation}")
        
        # 使用参数化查询
        query = """
        MATCH (src)-[r]->(dst)
        WHERE (src.name IN $entities OR dst.name IN $entities) AND type(r) = $relation
        RETURN 
          src.name AS source, 
          type(r) AS relation, 
          dst.name AS target,
          r.confidence AS confidence,
          r.source_sentence AS source_sentence
        ORDER BY r.confidence DESC
        LIMIT $limit
        """
        
        parameters = {
            'entities': clean_entities,
            'relation': relation,
            'limit': self.QUERY_RESULT_LIMIT
        }
        
        results = self._execute_query(query, parameters)
        valid_results = self._filter_by_confidence(results, confidence_threshold)
        
        return valid_results

    def find_relation_by_entities(self, entities: List[str], 
                                confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD, 
                                bidirectional: bool = True,
                                debug: bool = False) -> List[Dict[str, Any]]:
        """接口3: 接收两个实体，找到这两个实体之间的关系
        
        Args:
            entities: 包含两个实体的列表
            confidence_threshold: 置信度阈值，默认0.8
            bidirectional: 是否查找双向关系，默认True
            debug: 是否启用调试模式，默认False
            
        Returns:
            包含关系信息的列表，每个元素包含source、relation、target、confidence、source_sentence、direction
            
        Raises:
            ValueError: 输入验证失败
            TypeError: 类型错误
            Exception: 查询执行失败
        """
        # 输入验证
        clean_entities = self._validate_entities(entities)
        confidence_threshold = self._validate_confidence_threshold(confidence_threshold)
        
        if len(clean_entities) != 2:
            raise ValueError("实体列表必须包含两个实体")
        
        entity1, entity2 = clean_entities[0], clean_entities[1]
        
        # 调试模式：检查实体是否存在
        if debug:
            entity_check = self.check_entities_exist([entity1, entity2])
            print(f"实体存在性检查:")
            print(f"  '{entity1}': {'✅存在' if entity_check.get(entity1, False) else '❌不存在'}")
            print(f"  '{entity2}': {'✅存在' if entity_check.get(entity2, False) else '❌不存在'}")
            
            # 如果实体不存在，提供建议
            for entity in [entity1, entity2]:
                if not entity_check.get(entity, False):
                    similar_entities = self.get_entities_containing(entity)
                    if similar_entities:
                        print(f"  建议：'{entity}'不存在，但找到包含该词的实体: {similar_entities[:5]}")
                    else:
                        print(f"  建议：'{entity}'不存在，且没有找到相似实体")
        
        if bidirectional:
            # 查找双向关系：A->B 和 B->A
            query = """
            MATCH (src)-[r]->(dst)
            WHERE (src.name = $entity1 AND dst.name = $entity2) 
               OR (src.name = $entity2 AND dst.name = $entity1)
            RETURN 
              src.name AS source, 
              type(r) AS relation, 
              dst.name AS target,
              r.confidence AS confidence,
              r.source_sentence AS source_sentence,
              CASE 
                WHEN src.name = $entity1 AND dst.name = $entity2 THEN 'forward'
                ELSE 'reverse'
              END AS direction
            ORDER BY r.confidence DESC
            LIMIT $limit
            """
        else:
            # 只查找顺向关系：A->B
            query = """
            MATCH (src)-[r]->(dst)
            WHERE src.name = $entity1 AND dst.name = $entity2
            RETURN 
              src.name AS source, 
              type(r) AS relation, 
              dst.name AS target,
              r.confidence AS confidence,
              r.source_sentence AS source_sentence,
              'forward' AS direction
            ORDER BY r.confidence DESC
            LIMIT $limit
            """
        
        parameters = {
            'entity1': entity1,
            'entity2': entity2,
            'limit': self.QUERY_RESULT_LIMIT
        }
        
        results = self._execute_query(query, parameters)
        valid_results = self._filter_by_confidence(results, confidence_threshold)
        
        return valid_results

    def query_graph(self, question: str, entities) -> Dict[str, Any]:
        """保持向后兼容的核心查询流程
        
        Args:
            question: 问题文本
            entities: 实体信息（列表或字典）
            
        Returns:
            格式化的查询结果
            
        Raises:
            ValueError: 输入验证失败
            Exception: 查询执行失败
        """
        if not question or not isinstance(question, str):
            raise ValueError("问题不能为空且必须是字符串")
        
        # 兼容原有接口
        try:
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
            
        except Exception as e:
            self.logger.error(f"查询失败: {e}")
            return {
                "question": question,
                "answer": f"查询失败: {e}",
                "knowledge_trace": [],
                "error": str(e)
            }

    def _format_results(self, question: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成带溯源信息的回答
        
        Args:
            question: 问题文本
            results: 查询结果
            
        Returns:
            格式化的结果
        """
        if not results:
            return {
                "question": question,
                "answer": "暂无可靠知识支持",
                "knowledge_trace": []
            }

        # 生成核心答案
        main_answer = f"{results[0]['source']} → {results[0]['relation']} → {results[0]['target']}"

        # 构造溯源信息
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
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 获取节点数量
            node_count_query = "MATCH (n) RETURN count(n) as node_count"
            node_result = self._execute_query(node_count_query, {})
            node_count = node_result[0]['node_count'] if node_result else 0
            
            # 获取关系数量
            rel_count_query = "MATCH ()-[r]->() RETURN count(r) as rel_count"
            rel_result = self._execute_query(rel_count_query, {})
            rel_count = rel_result[0]['rel_count'] if rel_result else 0
            
            # 获取关系类型统计
            rel_type_query = "MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count ORDER BY count DESC"
            rel_type_result = self._execute_query(rel_type_query, {})
            
            return {
                "node_count": node_count,
                "relationship_count": rel_count,
                "relationship_types": rel_type_result,
                "supported_relations": self.relation_types
            }
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {
                "error": f"获取统计信息失败: {e}"
            }
    
    def check_entities_exist(self, entities: List[str]) -> Dict[str, bool]:
        """检查实体是否在数据库中存在
        
        Args:
            entities: 要检查的实体列表
            
        Returns:
            字典，键为实体名，值为是否存在
        """
        if not entities:
            return {}
        
        try:
            query = """
            UNWIND $entities AS entity_name
            OPTIONAL MATCH (n) WHERE n.name = entity_name
            RETURN entity_name, n IS NOT NULL AS exists
            """
            
            parameters = {'entities': entities}
            results = self._execute_query(query, parameters)
            return {r['entity_name']: r['exists'] for r in results}
            
        except Exception as e:
            self.logger.error(f"检查实体存在性失败: {e}")
            return {entity: False for entity in entities}
    
    def get_entities_containing(self, keyword: str) -> List[str]:
        """获取包含指定关键词的实体列表
        
        Args:
            keyword: 关键词
            
        Returns:
            包含该关键词的实体名称列表
        """
        if not keyword or not isinstance(keyword, str):
            return []
        
        keyword = keyword.strip()
        if not keyword:
            return []
        
        try:
            query = """
            MATCH (n) 
            WHERE n.name CONTAINS $keyword
            RETURN n.name AS name
            ORDER BY n.name
            LIMIT 20
            """
            
            parameters = {'keyword': keyword}
            results = self._execute_query(query, parameters)
            return [r['name'] for r in results]
            
        except Exception as e:
            self.logger.error(f"搜索包含关键词的实体失败: {e}")
            return []

# 为了向后兼容，保留原类名的别名
DSAGraphQA = DSAGraphQAFixed