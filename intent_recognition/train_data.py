# -*- coding: utf-8 -*-

# 严格按照三个意图模式生成的大量、多样化、并可直接使用的训练数据
train_data = [
    # ==============================================================================
    # 意图 1: find_relation_by_two_entities
    # 模式: [实体A] + [实体B] -> 询问二者关系
    # ==============================================================================
    ("数组跟链表有什么关系", "find_relation_by_two_entities"),
    ("BFS和DFS之间有什么关联？", "find_relation_by_two_entities"),
    ("对比一下快速排序和归并排序", "find_relation_by_two_entities"),
    ("哈希表和散列表是同义的吗？", "find_relation_by_two_entities"),
    ("二叉搜索树是属于平衡二叉树的吗？", "find_relation_by_two_entities"),
    ("最小生成树和最短路径问题有何不同？", "find_relation_by_two_entities"),
    ("有向图和无向图的区别是什么？", "find_relation_by_two_entities"),
    ("堆和栈的差异", "find_relation_by_two_entities"),
    ("逻辑结构和物理结构有什么联系？", "find_relation_by_two_entities"),
    ("Prim算法和Kruskal算法都是解决最小生成树的吗？", "find_relation_by_two_entities"),
    ("递归和迭代哪个更好？", "find_relation_by_two_entities"),
    ("时间复杂度和空间复杂度是什么关系？", "find_relation_by_two_entities"),
    ("邻接表与邻接矩阵的比较", "find_relation_by_two_entities"),
    ("满二叉树和完全二叉树的关系", "find_relation_by_two_entities"),
    ("Dijkstra算法和Floyd算法都能求最短路径吗？", "find_relation_by_two_entities"),
    ("冒泡排序和选择排序哪个更稳定？", "find_relation_by_two_entities"),
    ("抽象数据类型和数据类型有什么区别？", "find_relation_by_two_entities"),
    ("大根堆和小根堆正好相反吗？", "find_relation_by_two_entities"),
    ("分治法和动态规划有何关联？", "find_relation_by_two_entities"),
    ("单链表和双向链表的主要差异是什么", "find_relation_by_two_entities"),
    ("比较一下线性结构和非线性结构", "find_relation_by_two_entities"),
    ("回溯法和DFS是什么关系", "find_relation_by_two_entities"),
    ("图的顶点和树的节点是类似的概念吗", "find_relation_by_two_entities"),
    ("队列和栈的操作效率对比", "find_relation_by_two_entities"),
    ("二分查找与二叉搜索树的联系", "find_relation_by_two_entities"),
    ("贪心策略和动态规划的区别", "find_relation_by_two_entities"),
    ("比较排序和基数排序的原理", "find_relation_by_two_entities"),
    ("稀疏图和稠密图的存储方式有何不同", "find_relation_by_two_entities"),
    ("AOV网和AOE网的应用场景差异", "find_relation_by_two_entities"),
    ("指针和引用的区别是什么？", "find_relation_by_two_entities"),
    ("邻接多重表和十字链表分别适用于什么类型的图？", "find_relation_by_two_entities"),
    ("直接插入排序和希尔排序的关系", "find_relation_by_two_entities"),
    ("平衡因子和树的高度有关系吗", "find_relation_by_two_entities"),
    ("连通图和强连通图的定义差异", "find_relation_by_two_entities"),
    ("循环队列和普通队列的对比", "find_relation_by_two_entities"),

    # ==============================================================================
    # 意图 2: find_entity_by_relation_and_entity
    # 模式: [实体A] + [关系] -> 询问相关的另一实体
    # ==============================================================================
    ("树这种结构包含哪些类型的节点？", "find_entity_by_relation_and_entity"),
    ("排序算法都具有哪些属性？", "find_entity_by_relation_and_entity"),
    ("图的组成部分除了顶点还有什么？", "find_entity_by_relation_and_entity"),
    ("和最小生成树问题相关的算法有哪些？", "find_entity_by_relation_and_entity"),
    ("线性结构包含哪些具体的数据结构？", "find_entity_by_relation_and_entity"),
    ("一个树的节点包含哪些部分？", "find_entity_by_relation_and_entity"),
    ("属于交换排序的有哪些具体算法？", "find_entity_by_relation_and_entity"),
    ("解决哈希冲突的方法有哪些？", "find_entity_by_relation_and_entity"),
    ("栈的常见操作有哪些？", "find_entity_by_relation_and_entity"),
    ("图的遍历算法除了BFS还有什么？", "find_entity_by_relation_and_entity"),
    ("时间复杂度这个属性通常有哪些衡量标准？", "find_entity_by_relation_and_entity"),
    ("实现一个队列需要哪些基本操作？", "find_entity_by_relation_and_entity"),
    ("无向图的存储结构除了邻接矩阵还有别的吗？", "find_entity_by_relation_and_entity"),
    ("最短路径算法除了迪杰斯特拉还有哪些", "find_entity_by_relation_and_entity"),
    ("树的遍历方式有几种", "find_entity_by_relation_and_entity"),
    ("常见的非线性结构有哪些例子", "find_entity_by_relation_and_entity"),
    ("一个算法的基本特征包括什么", "find_entity_by_relation_and_entity"),
    ("哈希函数的设计原则有哪些", "find_entity_by_relation_and_entity"),
    ("平衡二叉树的调整操作包括哪些", "find_entity_by_relation_and_entity"),
    ("简单排序都有哪些算法？", "find_entity_by_relation_and_entity"),
    ("图的存储除了邻接表还有啥？", "find_entity_by_relation_and_entity"),
    ("动态规划问题有什么共同特征？", "find_entity_by_relation_and_entity"),
    ("链表的节点由什么组成？", "find_entity_by_relation_and_entity"),
    ("求最小生成树的经典算法有哪些", "find_entity_by_relation_and_entity"),
    ("二叉树有哪些特殊的形态", "find_entity_by_relation_and_entity"),

    # ==============================================================================
    # 意图 3: other
    # 模式: 不符合以上两种模式的所有其他问题（例如：单个实体的查询、闲聊等）
    # ==============================================================================
    ("什么是数组？", "other"),
    ("介绍一下快速排序", "other"),
    ("讲讲DFS的原理", "other"),
    ("请解释一下哈希表", "other"),
    ("什么是时间复杂度？", "other"),
    ("介绍下Dijkstra算法", "other"),
    ("我想了解下图", "other"),
    ("什么是递归？", "other"),
    ("讲一下动态规划的核心思想", "other"),
    ("平衡二叉树是什么", "other"),
    ("什么是并查集？", "other"),
    ("能讲讲拓扑排序吗", "other"),
    ("数据结构难吗？", "other"),
    ("如何学好算法？", "other"),
    ("排序算法哪个最常用？", "other"),
    ("你好", "other"),
    ("台北今天天气怎么样？", "other"),
    ("现在几点了？", "other"),
    ("你是谁？", "other"),
    ("谢谢", "other"),
    ("再见", "other"),
    ("你真厉害", "other"),
    ("有什么可以帮我的吗", "other"),
    ("今天是2025年8月22日吗？", "other"),
    ("这个知识库是谁做的", "other"),
]

# 统计最终各类别的数量
intent_counts = {}
for _, intent in train_data:
    intent_counts[intent] = intent_counts.get(intent, 0) + 1

print("成功生成一份包含 {} 条样本的静态训练数据。".format(len(train_data)))
print("样本分布如下：")
for intent, count in intent_counts.items():
    print(f"- 意图 '{intent.replace('_', ' ')}': {count} 条样本")