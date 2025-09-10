from query_fixed import DSAGraphQAFixed
import os

def main():
    qa_system = DSAGraphQAFixed(
        "bolt://localhost:7687",
        "neo4j",
        os.getenv("NEO4J_KEY")
    )
    result = qa_system.find_entity_relations(['数组'])
    print(result)
    print("-----------------")
    result = qa_system.find_entities_by_relation(['数组'], '包含')
    print(result)
    print("-----------------")
    # 原问题：查找'数组'和'元素'之间的关系
    # 问题：数据库中不存在'元素'实体，只有'数组'实体
    result = qa_system.find_relation_by_entities(['数组', '元素'])
    print("原问题结果（预期为空）:", result)
    print("-----------------")
    
    # 修复：使用实际存在的实体
    print("使用实际存在的实体测试:")
    result = qa_system.find_relation_by_entities(['数组', '时间复杂度'])
    print("数组 ↔ 时间复杂度:", result)
    print("-----------------")
    result = qa_system.find_relation_by_entities(['查找', '数组'])
    print("查找 ↔ 数组:", result)
    print("-----------------")
    result = qa_system.query_graph('数组的时间复杂度', ['数组', '时间复杂度'])
    print(result)
    print("-----------------")
    

if __name__=="__main__":
    main()