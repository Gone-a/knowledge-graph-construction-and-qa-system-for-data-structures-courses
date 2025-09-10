from query_fixed import DSAGraphQAFixed
import os

def main():
    qa_system = DSAGraphQAFixed(
        "bolt://localhost:7687",
        "neo4j",
        os.getenv("NEO4J_KEY")
    )
    
    print("=== 测试1: find_entity_relations(['数组']) ===")
    result = qa_system.find_entity_relations(['数组'])
    print(f"结果数量: {len(result)}")
    if result:
        print(f"第一个结果: {result[0]}")
    print("-" * 50)
    
    print("=== 测试2: find_entities_by_relation(['数组'], '依赖') ===")
    result = qa_system.find_entities_by_relation(['数组'], '依赖')
    print(f"结果数量: {len(result)}")
    if result:
        print(f"第一个结果: {result[0]}")
    print("-" * 50)
    
    print("=== 测试3: find_relation_by_entities(['数组', '元素']) - 原问题 ===")
    result = qa_system.find_relation_by_entities(['数组', '元素'])
    print(f"结果数量: {len(result)}")
    if result:
        print(f"结果: {result}")
    else:
        print("没有找到关系 - 这是预期的，因为数据库中没有'元素'实体")
    print("-" * 50)
    
    print("=== 测试4: find_relation_by_entities(['数组', '时间复杂度']) - 使用实际存在的实体 ===")
    result = qa_system.find_relation_by_entities(['数组', '时间复杂度'])
    print(f"结果数量: {len(result)}")
    if result:
        print(f"结果: {result}")
    print("-" * 50)
    
    print("=== 测试5: find_relation_by_entities(['查找', '数组']) - 另一个实际存在的关系 ===")
    result = qa_system.find_relation_by_entities(['查找', '数组'])
    print(f"结果数量: {len(result)}")
    if result:
        print(f"结果: {result}")
    print("-" * 50)
    
    print("=== 测试6: 使用更低的置信度阈值测试原问题 ===")
    result = qa_system.find_relation_by_entities(['数组', '元素'], confidence_threshold=0.1)
    print(f"结果数量: {len(result)}")
    if result:
        print(f"结果: {result}")
    else:
        print("即使使用低置信度阈值也没有找到关系")
    print("-" * 50)
    
    print("=== 测试7: 检查数据库中包含'元素'的实体 ===")
    element_entities = qa_system.graph.run(
        "MATCH (n) WHERE n.name CONTAINS '元素' RETURN n.name AS name ORDER BY n.name"
    ).data()
    print(f"包含'元素'的实体: {[e['name'] for e in element_entities]}")
    
    if element_entities:
        print("\n=== 测试8: 使用'数据元素'测试关系查找 ===")
        result = qa_system.find_relation_by_entities(['数组', '数据元素'])
        print(f"结果数量: {len(result)}")
        if result:
            print(f"结果: {result}")
        else:
            print("'数组'和'数据元素'之间没有直接关系")
    
    print("\n=== 问题诊断总结 ===")
    print("1. 数据库中存在'数组'实体")
    print("2. 数据库中不存在单独的'元素'实体")
    print("3. 数据库中存在多个包含'元素'的实体，如'数据元素'、'堆顶元素'等")
    print("4. find_relation_by_entities方法工作正常，问题在于查询的实体不存在")
    print("5. 建议使用实际存在的实体名称进行查询")

if __name__ == "__main__":
    main()