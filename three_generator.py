# -*- coding: utf-8 -*-
"""
数据结构与算法知识图谱生成器
生成包含清晰三元组结构的句子，便于构建知识图谱
"""

# 定义知识库
knowledge_base = {
    # 数据结构
    "数组": {
        "定义": "一种在内存中连续存储相同类型元素的线性数据结构",
        "性质": ["支持通过索引进行O(1)时间的随机访问", "大小通常在创建时固定"],
        "作用": "存储有序的元素集合，支持快速查找和修改",
        "关系": {
            "基础": "链表、栈、队列等数据结构的基础",
            "对比": "链表在插入/删除操作上更灵活但随机访问效率低"
        }
    },
    "链表": {
        "定义": "一种通过指针将零散的内存块（节点）连接起来的线性数据结构",
        "性质": ["支持高效的插入和删除操作（O(1)时间）", "不支持高效的随机访问（O(n)时间）"],
        "作用": "需要频繁插入和删除操作的场景",
        "relation": {
            "基础": "栈、队列、树、图等数据结构的基础",
            "对比": "数组在随机访问上效率更高但插入/删除效率低"
        }
    },
    "栈": {
        "定义": "一种遵循后进先出（LIFO）原则的线性数据结构",
        "性质": ["只允许在栈顶进行插入（push）和删除（pop）操作"],
        "作用": "函数调用栈、表达式求值、深度优先搜索（DFS）",
        "relation": {
            "实现": "数组或链表",
            "应用": "DFS算法"
        }
    },
    "队列": {
        "定义": "一种遵循先进先出（FIFO）原则的线性数据结构",
        "性质": ["允许在队尾插入（enqueue），在队头删除（dequeue）"],
        "作用": "任务调度、缓冲区管理、广度优先搜索（BFS）",
        "relation": {
            "实现": "数组（循环队列）或链表",
            "应用": "BFS算法"
        }
    },
    "二叉树": {
        "定义": "一种每个节点最多有两个子节点的树形数据结构",
        "性质": ["具有根节点、叶子节点等概念", "支持前序、中序、后序和层序遍历"],
        "作用": "高效地组织和检索数据，是许多高级数据结构的基础",
        "relation": {
            "特例": "二叉搜索树是二叉树的一种，具有排序性质",
            "应用": "堆是一种特殊的二叉树，用于优先队列"
        }
    },
    "哈希表": {
        "定义": "一种通过哈希函数将键（key）映射到存储位置（bucket）来实现高效查找的数据结构",
        "性质": ["在平均情况下支持O(1)时间的插入、删除和查找操作", "可能发生哈希冲突"],
        "作用": "需要快速查找、插入和删除键值对的场景",
        "relation": {
            "解决冲突": "常用链地址法（哈希桶）或开放寻址法解决哈希冲突",
            "基础": "是字典（dict/map）和集合（set）等抽象数据类型的底层实现"
        }
    },
    "图": {
        "定义": "一种由顶点（vertex/node）集合和连接顶点的边（edge）集合组成的数据结构",
        "性质": ["可以表示对象及其之间的关系", "分为有向图和无向图"],
        "作用": "建模网络、社交关系、路径规划等问题",
        "relation": {
            "遍历": "深度优先搜索（DFS）和广度优先搜索（BFS）是图的基本遍历算法",
            "算法": "Dijkstra算法用于求解单源最短路径问题"
        }
    },
    
    # 算法
    "深度优先搜索": {
        "定义": "一种沿着分支尽可能深入探索，直到无法继续再回溯的图或树遍历算法",
        "性质": ["通常使用递归或显式栈（后进先出）实现"],
        "作用": "图的连通性检测、拓扑排序、寻找路径、解决回溯问题",
        "relation": {
            "数据结构": "栈",
            "对比": "广度优先搜索（BFS）使用队列（先进先出）管理搜索状态"
        }
    },
    "广度优先搜索": {
        "定义": "一种按层次（距离起始点的远近）依次访问节点的图或树遍历算法",
        "性质": ["通常使用队列（先进先出）实现"],
        "作用": "寻找无权图中的最短路径、图的连通性检测",
        "relation": {
            "数据结构": "队列",
            "对比": "深度优先搜索（DFS）使用栈（后进先出）管理搜索状态"
        }
    },
    "快速排序": {
        "定义": "一种基于分治策略的高效排序算法",
        "性质": ["平均时间复杂度为O(n log n)", "最坏时间复杂度为O(n²)", "原地排序（空间复杂度O(log n)递归栈）"],
        "作用": "对大规模数据进行高效排序",
        "relation": {
            "核心操作": "通过选取基准值（pivot）将数组划分为较小和较大两部分（分区操作）",
            "分治": "递归地对划分后的子数组进行排序"
        }
    },
    "归并排序": {
        "定义": "一种基于分治策略的稳定排序算法",
        "性质": ["时间复杂度稳定为O(n log n)", "需要O(n)的额外空间"],
        "作用": "对大规模数据进行高效且稳定的排序",
        "relation": {
            "核心操作": "将数组递归地分成两半，分别排序后再合并（merge）两个有序子数组",
            "分治": "是分治策略的典型应用"
        }
    },
    "二分查找": {
        "定义": "一种在有序数组中查找特定元素的高效搜索算法",
        "性质": ["时间复杂度为O(log n)", "要求数组必须有序"],
        "作用": "在有序集合中快速定位目标元素",
        "relation": {
            "前提": "输入数据必须是有序的",
            "分治": "通过不断将搜索区间减半（分治思想）来缩小范围"
        }
    },
    "动态规划": {
        "定义": "一种通过将复杂问题分解为重叠子问题并存储子问题解来避免重复计算，从而高效求解优化问题的算法策略",
        "性质": ["通常用于求解具有最优子结构的问题"],
        "作用": "求解如最短路径、背包问题、编辑距离等最优化问题",
        "relation": {
            "核心": "利用表格（数组）存储子问题的解",
            "对比": "贪心算法每一步做局部最优选择，可能得不到全局最优解；动态规划保证全局最优"
        }
    },
    "贪心算法": {
        "定义": "一种在每一步选择中都采取在当前状态下最好或最优的选择，从而希望导致结果是全局最好或最优的算法策略",
        "性质": ["通常简单高效", "不保证对所有问题都能得到全局最优解"],
        "作用": "求解如活动选择、霍夫曼编码、最小生成树（Prim/Kruskal）等特定问题",
        "relation": {
            "适用性": "适用于具有贪心选择性质和最优子结构的问题",
            "对比": "动态规划通过存储子问题解保证全局最优，贪心算法依赖局部最优选择"
        }
    }
}

def generate_knowledge_sentences(concept):
    """为指定概念生成知识图谱句子"""
    if concept not in knowledge_base:
        return [f"概念 '{concept}' 未在知识库中找到"]
    
    info = knowledge_base[concept]
    sentences = []
    
    # 生成定义句
    sentences.append(f"{concept} 是 {info['定义']}")
    
    # 生成性质句
    for prop in info.get('性质', []):
        sentences.append(f"{concept} 具有 {prop} 的性质")
    
    # 生成作用句
    if '作用' in info:
        sentences.append(f"{concept} 用于 {info['作用']}")
    
    # 生成关系句
    for rel_type, rel_target in info.get('relation', {}).items():
        # 处理关系目标可能是字符串或列表的情况
        if isinstance(rel_target, list):
            for target in rel_target:
                sentences.append(f"{concept} {rel_type} {target}")
        else:
            sentences.append(f"{concept} {rel_type} {rel_target}")
    
    return sentences

def extract_triples(sentence):
    """从句子中提取三元组（主语，关系，宾语）"""
    # 定义常见关系模式
    patterns = [
        (" 是 ", "是"),
        (" 具有 ", "具有"),
        (" 用于 ", "用于"),
        (" 解决冲突 ", "解决冲突"),
        (" 基础 ", "基础"),
        (" 对比 ", "对比"),
        (" 实现 ", "实现"),
        (" 应用 ", "应用"),
        (" 特例 ", "特例"),
        (" 遍历 ", "遍历"),
        (" 算法 ", "算法"),
        (" 数据结构 ", "数据结构"),
        (" 前提 ", "前提"),
        (" 分治 ", "分治"),
        (" 核心 ", "核心"),
        (" 适用性 ", "适用性"),
        (" 核心操作 ", "核心操作"),
    ]
    
    for pattern, relation in patterns:
        if pattern in sentence:
            parts = sentence.split(pattern, 1)
            if len(parts) == 2:
                return (parts[0].strip(), relation, parts[1].strip())
    
    # 如果未匹配到任何模式，尝试按空格分割
    words = sentence.split()
    if len(words) >= 3:
        # 假设主语是第一个词，关系是第二个词，宾语是剩余部分
        subject = words[0]
        relation = words[1]
        obj = " ".join(words[2:])
        return (subject, relation, obj)
    
    return None

def generate_full_knowledge_document():
    """生成完整的知识文档（文本格式）"""
    document = []
    for concept in knowledge_base.keys():
        document.append(f"=== {concept} ===")
        sentences = generate_knowledge_sentences(concept)
        document.extend(sentences)
        document.append("")  # 添加空行分隔概念
    return document

def generate_markdown_document():
    """生成Markdown格式的知识文档"""
    md = ["# 数据结构与算法知识图谱", ""]
    
    md.append("## 数据结构")
    for concept in ["数组", "链表", "栈", "队列", "二叉树", "哈希表", "图"]:
        if concept in knowledge_base:
            md.append(f"### {concept}")
            sentences = generate_knowledge_sentences(concept)
            for sentence in sentences:
                md.append(f"- {sentence}")
            md.append("")
    
    md.append("## 算法")
    for concept in ["深度优先搜索", "广度优先搜索", "快速排序", "归并排序", 
                   "二分查找", "动态规划", "贪心算法"]:
        if concept in knowledge_base:
            md.append(f"### {concept}")
            sentences = generate_knowledge_sentences(concept)
            for sentence in sentences:
                md.append(f"- {sentence}")
            md.append("")
    
    return md

def generate_json_knowledge():
    """生成JSON格式的知识图谱数据"""
    import json
    knowledge_graph = {}
    
    for concept in knowledge_base.keys():
        sentences = generate_knowledge_sentences(concept)
        triples = []
        
        for sentence in sentences:
            triple = extract_triples(sentence)
            if triple:
                triples.append({
                    "subject": triple[0],
                    "relation": triple[1],
                    "object": triple[2],
                    "sentence": sentence
                })
        
        knowledge_graph[concept] = {
            "sentences": sentences,
            "triples": triples
        }
    
    return json.dumps(knowledge_graph, indent=2, ensure_ascii=False)

def save_to_file(filename, content):
    """将内容保存到文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        if isinstance(content, list):
            f.write("\n".join(content))
        else:
            f.write(content)

def main():
    """主函数：生成并输出知识图谱"""
    print("生成知识图谱文档...")
    
    # 生成文本格式文档
    text_doc = generate_full_knowledge_document()
    save_to_file("knowledge_graph.txt", text_doc)
    print("已保存文本格式文档: knowledge_graph.txt")
    
    # 生成Markdown格式文档
    md_doc = generate_markdown_document()
    save_to_file("knowledge_graph.md", md_doc)
    print("已保存Markdown格式文档: knowledge_graph.md")
    
    # 生成JSON格式数据
    json_data = generate_json_knowledge()
    save_to_file("knowledge_graph.json", json_data)
    print("已保存JSON格式数据: knowledge_graph.json")
    
    # 在控制台输出示例
    print("\n示例输出（栈的概念）:")
    for sentence in generate_knowledge_sentences("栈"):
        print(f"- {sentence}")
    
    print("\n示例三元组提取:")
    for sentence in generate_knowledge_sentences("栈"):
        triple = extract_triples(sentence)
        if triple:
            print(f"句子: '{sentence}'")
            print(f"三元组: ({triple[0]}, {triple[1]}, {triple[2]})")
            print()

if __name__ == "__main__":
    main()