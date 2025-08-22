from py2neo import Graph
from transformers import pipeline
import os

class DSAGraphQA:
    def __init__(self,neo4j_uri,username,password):
        """初始化图数据库连接和NLP模型"""
        #1.连接Neo4j数据库
        self.graph=Graph(neo4j_uri, auth=(username, password))
        # 数据库中实际的关系类型（中文）
        self.relation_types = ["依赖", "属性", "相对", "被包含", "被依赖"]
        
        # 保持向后兼容的映射字典
        self.relation_dict={
            "rely":"依赖",
            "b-rely":"被依赖",
            "belg":"包含",
            "b-belg":"属于",
            "syno":"同义",
            "relative":"相对",
            "attr":"拥有",
            "b-attr":"属性",
            "none":"无",
            # 直接支持中文关系类型
            "依赖":"依赖",
            "被依赖":"被依赖",
            "被包含":"被包含",
            "相对":"相对",
            "属性":"属性"
        }

    def find_entity_relations(self, entities, confidence_threshold=0.7):
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
        
        print(f"执行查询: {query}")
        results = self.graph.run(query).data()
        valid_results = [r for r in results if r['confidence'] > confidence_threshold]
        
        # 将关系类型转换为中文
        for r in valid_results:
            r['relation'] = self.relation_dict.get(r['relation'], "未知")
        
        return valid_results
    
    def find_entities_by_relation(self, entities, relation, confidence_threshold=0.7):
        """接口2: 接收实体和关系，找到有这个关系的其他实体"""
        if not entities:
            raise ValueError("实体列表不能为空")
        if not relation:
            raise ValueError("关系类型不能为空")
        if relation not in self.relation_dict:
            raise ValueError(f"关系类型不合法，支持的关系类型: {list(self.relation_dict.keys())}")
        
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
        
        print(f"执行查询: {query}")
        results = self.graph.run(query).data()
        valid_results = [r for r in results if r['confidence'] > confidence_threshold]
        
        # 将关系类型转换为中文
        for r in valid_results:
            r['relation'] = self.relation_dict.get(r['relation'], "未知")
        
        return valid_results

    def query_graph(self, question, entities):
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



    def _format_results(self, question, results):
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


def test_entity_relations(qa_system):
    """测试接口1: 查找实体的所有相关关系"""
    print("\n===== 测试接口1: 查找实体相关关系 =====")
    entities = ["二叉树", "完全二叉树"]
    results = qa_system.find_entity_relations(entities)
    
    print(f"查询实体: {entities}")
    print(f"找到 {len(results)} 条相关关系:")
    for i, result in enumerate(results[:5]):  # 只显示前5条
        print(f"{i+1}. {result['source']} → {result['relation']} → {result['target']}")
        print(f"   置信度: {result['confidence']:.0%}")
        print(f"   来源: 『{result['source_sentence'][:50]}...』")

def test_entities_by_relation(qa_system):
    """测试接口2: 根据关系查找相关实体"""
    print("\n===== 测试接口2: 根据关系查找实体 =====")
    
    # 使用数据库中实际存在的关系类型
    entities = ["二叉树"]
    relations_to_try = ["依赖", "属性", "相对", "被包含", "被依赖"]
    
    for relation in relations_to_try:
        print(f"\n尝试关系类型: {relation}")
        results = qa_system.find_entities_by_relation(entities, relation)
        
        if results:
            print(f"查询实体: {entities}")
            print(f"找到 {len(results)} 条相关实体:")
            for i, result in enumerate(results[:3]):  # 只显示前3条
                print(f"{i+1}. {result['source']} → {result['relation']} → {result['target']}")
                print(f"   置信度: {result['confidence']:.0%}")
                print(f"   来源: 『{result['source_sentence'][:50]}...』")
            break
        else:
            print(f"未找到 {relation} 关系的相关实体")
    
    if not any(qa_system.find_entities_by_relation(entities, rel) for rel in relations_to_try):
        print("所有关系类型都未找到相关实体，可能需要检查数据库中的关系标签。")

def test_backward_compatibility(qa_system):
    """测试向后兼容性"""
    print("\n===== 测试向后兼容性 =====")
    question = "二叉树和完全二叉树有什么关系？"
    
    # 测试使用英文关系映射
    dict_input1 = {"entities":["二叉树", "完全二叉树"], "relation":"rely"}
    result1 = qa_system.query_graph(question, dict_input1)
    
    print("使用英文关系映射 (rely -> 依赖):")
    print(f"问题：{result1['question']}")
    print(f"答案：{result1['answer']}")
    if result1['knowledge_trace']:
        print("溯源信息：")
        for i, trace in enumerate(result1['knowledge_trace'][:2]):  # 只显示前2条
            print(f"{i+1}. {trace['path']} (置信度: {trace['confidence']:.0%})")
            print(f"   来源：『{trace['source_sentence'][:50]}...』")
    
    # 测试直接使用中文关系
    dict_input2 = {"entities":["二叉树", "完全二叉树"], "relation":"依赖"}
    result2 = qa_system.query_graph(question, dict_input2)
    
    print("\n使用中文关系类型 (依赖):")
    print(f"答案：{result2['answer']}")
    if result2['knowledge_trace']:
        print("溯源信息：")
        for i, trace in enumerate(result2['knowledge_trace'][:2]):  # 只显示前2条
            print(f"{i+1}. {trace['path']} (置信度: {trace['confidence']:.0%})")
            print(f"   来源：『{trace['source_sentence'][:50]}...』")


def inspect_database(qa_system):
    """检查数据库中的关系类型"""
    print("\n===== 数据库结构检查 =====")
    
    # 查询所有关系类型
    query = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
    try:
        results = qa_system.graph.run(query).data()
        print("数据库中的关系类型:")
        for i, result in enumerate(results):
            print(f"{i+1}. {result['relationshipType']}")
    except Exception as e:
        print(f"查询关系类型失败: {e}")
    
    # 查询一些示例关系
    query = """
    MATCH (src)-[r]->(dst) 
    WHERE src.name CONTAINS '二叉树' OR dst.name CONTAINS '二叉树'
    RETURN type(r) as relation_type, count(*) as count
    ORDER BY count DESC
    LIMIT 10
    """
    try:
        results = qa_system.graph.run(query).data()
        print("\n与'二叉树'相关的关系类型统计:")
        for result in results:
            print(f"- {result['relation_type']}: {result['count']} 条")
    except Exception as e:
        print(f"查询关系统计失败: {e}")

def main():
    """主函数：演示两个接口的使用"""
    qa_system = DSAGraphQA(
        neo4j_uri="bolt://localhost:7687",
        username="neo4j",
        password=os.getenv("NEO4J_KEY")
    )
    

    print("DSA知识图谱问答系统 - 双接口演示")
    
    try:
        # 首先检查数据库结构
        inspect_database(qa_system)
        
        # 测试接口1：查找实体的所有相关关系
        test_entity_relations(qa_system)
        
        # 测试接口2：根据关系查找相关实体
        test_entities_by_relation(qa_system)
        
        # 测试向后兼容性
        test_backward_compatibility(qa_system)
        
        print("\n=" * 60)
        print("所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
    

if __name__=="__main__":
    main()