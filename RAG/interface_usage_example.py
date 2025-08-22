#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱问答系统 - 双接口使用示例

本文件展示了如何使用两个主要接口：
1. find_entity_relations: 查找实体的所有相关关系
2. find_entities_by_relation: 根据关系查找相关实体
"""

import os
from main import DSAGraphQA

def example_usage():
    """演示两个接口的基本使用方法"""
    
    # 初始化系统
    qa_system = DSAGraphQA(
        neo4j_uri="bolt://localhost:7687",
        username="neo4j",
        password=os.getenv("NEO4J_KEY")
    )
    
    print("=" * 50)
    print("知识图谱问答系统 - 接口使用示例")
    print("=" * 50)
    
    # 示例1: 使用接口1 - 查找实体的所有相关关系
    print("\n【示例1】接口1: find_entity_relations")
    print("-" * 30)
    entities = ["二叉树"]
    results = qa_system.find_entity_relations(entities, confidence_threshold=0.8)
    
    print(f"查询实体: {entities}")
    print(f"找到 {len(results)} 条高置信度关系 (>80%):")
    for i, result in enumerate(results[:3]):
        print(f"{i+1}. {result['source']} → {result['relation']} → {result['target']}")
        print(f"   置信度: {result['confidence']:.0%}")
    
    # 示例2: 使用接口2 - 根据关系查找相关实体
    print("\n【示例2】接口2: find_entities_by_relation")
    print("-" * 30)
    entities = ["二叉树"]
    relation = "依赖"  # 使用数据库中实际存在的关系类型
    results = qa_system.find_entities_by_relation(entities, relation, confidence_threshold=0.8)
    
    print(f"查询实体: {entities}")
    print(f"查询关系: {relation}")
    print(f"找到 {len(results)} 条相关实体:")
    for i, result in enumerate(results[:3]):
        print(f"{i+1}. {result['source']} → {result['relation']} → {result['target']}")
        print(f"   置信度: {result['confidence']:.0%}")
    
    # 示例3: 向后兼容的query_graph接口
    print("\n【示例3】向后兼容接口: query_graph")
    print("-" * 30)
    question = "二叉树有哪些依赖关系？"
    dict_input = {"entities": ["二叉树"], "relation": "依赖"}
    result = qa_system.query_graph(question, dict_input)
    
    print(f"问题: {result['question']}")
    print(f"答案: {result['answer']}")
    print(f"找到 {len(result['knowledge_trace'])} 条溯源信息")
    
    
    print("示例演示完成！")
    

if __name__ == "__main__":
    example_usage()