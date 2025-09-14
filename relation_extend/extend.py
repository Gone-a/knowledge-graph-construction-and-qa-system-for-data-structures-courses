import os
import json
from typing import List

from knowledge_graph_builder import KnowledgeGraphBuilder

def iterative_build(kg_builder: KnowledgeGraphBuilder, max_iterations: int = 5, convergence_threshold: float = 0.1) -> List[str]:
    """迭代构建知识图谱"""
    if not os.path.exists(kg_builder.refined_kg_path):
        kg_builder.get_base_kg_from_csv()
    
    iteration_paths = []
    
    for i in range(max_iterations):
        new_relations_count = kg_builder.run_iteration()
        current_path = kg_builder.kg_paths[-1]
        iteration_paths.append(current_path)
        
        extend_ratio = kg_builder.extend_ratio()
        if extend_ratio < convergence_threshold or new_relations_count == 0:
            break
    
    return iteration_paths

def main():
    """主函数"""
    # 简化的参数配置
    class Args:
        def __init__(self):
            self.project = 'test_project'
            self.gpu = 0
            self.csv_path = '/root/KG_inde/relation_extend/data/predictions.csv'
            self.enable_ner = False
            self.confidence_threshold = 0.7
    
    args = Args()
    kg_builder = KnowledgeGraphBuilder(args)
    
    # 迭代构建知识图谱
    iteration_paths = iterative_build(kg_builder, max_iterations=5, convergence_threshold=0.1)
    
    return iteration_paths

if __name__ == "__main__":
    main()
