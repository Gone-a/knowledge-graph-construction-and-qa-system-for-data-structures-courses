"""
知识图谱可视化模块
整合局部知识图谱查询和可视化功能
"""

import json
import os
from typing import List, Dict, Any, Optional

try:
    from .knowledge_graph import KnowledgeGraphQuery
except ImportError:
    # 当作为独立脚本运行时使用绝对导入
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from modules.knowledge_graph import KnowledgeGraphQuery

class KnowledgeGraphVisualizer:
    """知识图谱可视化器"""
    
    def __init__(self, kg_query: Optional[KnowledgeGraphQuery] = None):
        """
        初始化可视化器
        
        Args:
            kg_query: 知识图谱查询器实例
        """
        self.kg_query = kg_query
        
    def visualize_knowledge_graph(self, query_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        可视化知识图谱查询结果
        
        Args:
            query_result: 知识图谱查询结果
            output_format: 输出格式 ('json', 'html')
            
        Returns:
            Dict: 可视化数据
        """
        # 提取节点和边
        nodes = []
        edges = []
        
        # 处理实体节点
        entities = query_result.get('entities', [])
        for entity in entities:
            nodes.append({
                'id': entity,
                'label': entity,
                'type': 'entity',
                'size': 20
            })
        
        # 处理关系边
        relations = query_result.get('relations', [])
        for relation in relations:
            entity1 = relation.get('entity1')
            entity2 = relation.get('entity2')
            relation_name = relation.get('relation_name', relation.get('relation_type', ''))
            confidence = relation.get('confidence', 1.0)
            
            # 确保节点存在
            for entity in [entity1, entity2]:
                if entity and not any(node['id'] == entity for node in nodes):
                    nodes.append({
                        'id': entity,
                        'label': entity,
                        'type': 'entity',
                        'size': 20
                    })
            
            # 添加边
            if entity1 and entity2:
                edges.append({
                    'source': entity1,
                    'target': entity2,
                    'label': relation_name,
                    'confidence': confidence,
                    'type': 'relation'
                })
        
        visualization_data = {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'question': query_result.get('question', ''),
                'answer': query_result.get('answer', ''),
                'confidence': query_result.get('confidence', 0.0),
                'node_count': len(nodes),
                'edge_count': len(edges)
            }
        }
        
        
        return visualization_data
    
    def query_and_visualize(self, question: str, entities: List[str] = None) -> Dict[str, Any]:
        """
        查询并可视化知识图谱
        
        Args:
            question: 查询问题
            entities: 相关实体列表
            
        Returns:
            Dict: 可视化结果
        """
        if not self.kg_query:
            return {
                'success': False,
                'message': '知识图谱查询器未初始化',
                'visualization': None
            }
        
        try:
            # 执行知识图谱查询
            query_result = self.kg_query.query_graph(question, entities)
            
            # 生成可视化
            visualization = self.visualize_knowledge_graph(query_result)
            
            return {
                'success': True,
                'message': '查询成功',
                'query_result': query_result,
                'visualization': visualization
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'查询失败: {str(e)}',
                'visualization': None
            }
    


def create_visualizer_with_kg(kg_query: Optional[KnowledgeGraphQuery] = None) -> KnowledgeGraphVisualizer:
    """
    创建带知识图谱查询功能的可视化器
    
    Args:
        kg_query: 知识图谱查询器实例
        
    Returns:
        KnowledgeGraphVisualizer: 可视化器实例
    """
    return KnowledgeGraphVisualizer(kg_query)


# 示例用法
if __name__ == "__main__":
    # 创建示例数据
    sample_query_result = {
        'question': '快速排序的相关概念',
        'entities': ['快速排序', '分治', '递归'],
        'relations': [
            {
                'entity1': '快速排序',
                'entity2': '分治',
                'relation_name': '使用',
                'confidence': 0.9
            },
            {
                'entity1': '快速排序',
                'entity2': '递归',
                'relation_name': '实现方式',
                'confidence': 0.8
            }
        ],
        'answer': '快速排序是一种使用分治策略的递归排序算法',
        'confidence': 0.85
    }
    
    # 创建可视化器
    visualizer = KnowledgeGraphVisualizer()
    
    # 生成可视化
    viz_data = visualizer.visualize_knowledge_graph(sample_query_result)
    print("可视化数据生成成功:")
    print(f"节点数: {len(viz_data['nodes'])}")
    print(f"边数: {len(viz_data['edges'])}")
    