# -*- coding: utf-8 -*-
import torch
import json
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np

# --- 配置 ---
# 模型路径，请确保与您的模型文件夹名称一致
MODEL_PATH = "./my_intent_model"

# --- 核心：测试样本 ---
# 这些样本必须与训练样本不同，以检验模型的泛化能力。
# 格式: ("用户可能会说的话", "真实的意图标签")
test_samples = [
    # ==============================================================================
    # 意图 1: find_relation_by_two_entities
    # 模式: [实体A] + [实体B] -> 询问二者关系
    # ==============================================================================
    ("迪杰斯特拉算法和贪心策略是什么关系？", "find_relation_by_two_entities"),
    ("可以说哈希表是映射的一种实现吗？", "find_relation_by_two_entities"),
    ("在处理图的最短路径问题上，BFS和DFS哪个更适合？", "find_relation_by_two_entities"),
    ("邻接表和邻接矩阵在空间占用上的对比", "find_relation_by_two_entities"),
    ("堆和平衡二叉树的查询效率比较", "find_relation_by_two_entities"),
    ("分治法和递归是什么关系？", "find_relation_by_two_entities"),
    ("栈和队列在逻辑结构上都是线性表吗？", "find_relation_by_two_entities"),
    ("快排和堆排序的稳定性有何差异？", "find_relation_by_two_entities"),

    # ==============================================================================
    # 意图 2: find_entity_by_relation_and_entity
    # 模式: [实体A] + [关系] -> 询问相关的另一实体
    # ==============================================================================
    ("一个完整的图结构由哪些基本元素构成？", "find_entity_by_relation_and_entity"),
    ("除了稳定性，评价一个排序算法还有哪些指标？", "find_entity_by_relation_and_entity"),
    ("动态规划问题的求解步骤有哪些？", "find_entity_by_relation_and_entity"),
    ("属于非线性结构的数据结构能举几个例子吗？", "find_entity_by_relation_and_entity"),
    ("二叉树的遍历顺序有几种？", "find_entity_by_relation_and_entity"),
    ("链表的基本操作除了插入和删除还有什么？", "find_entity_by_relation_and_entity"),
    ("常见的用于解决最短路径问题的算法有哪些？", "find_entity_by_relation_and_entity"),

    # ==============================================================================
    # 意图 3: other
    # 模式: 不符合以上两种模式的所有其他问题（特别是边界和模糊情况）
    # ==============================================================================
    ("我想了解关于数组和链表的一切", "other"), # 提及两个实体，但问题模糊，不属于关系查询
    ("什么是图的遍历？", "other"), # 对一个操作的定义查询
    ("Dijkstra", "other"), # 单个关键词
    ("你觉得学习数据结构最快的方法是什么？", "other"), # 主观开放性问题
    ("今天晚上台北天气好吗？", "other"), # 领域外闲聊
    ("现在是晚上11点多了吧？", "other"), # 领域外闲聊
    ("介绍一下排序", "other"), # 对一个大类的模糊查询
    ("谢谢你的帮助", "other"), # 闲聊
]

def load_model_and_tokenizer(model_path):
    """加载模型、分词器和标签映射。"""
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        with open(f"{model_path}/label_map.json", 'r', encoding='utf-8') as f:
            label_map = json.load(f)
            id2label = {int(k): v for k, v in label_map['id2label'].items()}
        print(f"模型从 '{model_path}' 加载成功。")
        return tokenizer, model, id2label
    except Exception as e:
        print(f"加载模型失败，请检查路径 '{model_path}' 是否正确。错误: {e}")
        return None, None, None

def predict(text, tokenizer, model, id2label):
    """对单一句子进行意图预测。"""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        logits = model(**inputs).logits
    predicted_class_id = logits.argmax().item()
    return id2label[predicted_class_id]

def evaluate():
    """执行完整的评估流程。"""
    tokenizer, model, id2label = load_model_and_tokenizer(MODEL_PATH)
    if not model:
        return

    print("\n--- 开始评估 ---")
    
    # 获取所有唯一的标签名称，并确保顺序
    labels = sorted(list(id2label.values()))
    
    y_true = [] # 储存真实标签
    y_pred = [] # 储存预测标签

    for i, (text, true_label) in enumerate(test_samples):
        predicted_label = predict(text, tokenizer, model, id2label)
        y_true.append(true_label)
        y_pred.append(predicted_label)
        print(f"样本 {i+1:02d}: {text}")
        print(f"  -> 真实意图: {true_label}")
        print(f"  -> 预测意图: {predicted_label} {'✅' if true_label == predicted_label else '❌'}")
        print("-" * 20)

    print("\n--- 评估报告 ---")
    
    # 1. 分类报告
    report = classification_report(y_true, y_pred, labels=labels, digits=4)
    print("1. 分类报告 (Classification Report):")
    print(report)
    
    # 2. 混淆矩阵
    print("\n2. 混淆矩阵 (Confusion Matrix):")
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    
    # 为了方便阅读，打印带有标签的混淆矩阵
    header = " " * 20 + " ".join([f"{label[:8]:<8}" for label in labels])
    print(header)
    print("-" * len(header))
    for i, label in enumerate(labels):
        row_str = f"{label:<20}"
        for val in cm[i]:
            row_str += f"{val:<8}"
        print(row_str)
    print("\n(行: 真实标签, 列: 预测标签)")

if __name__ == "__main__":
    evaluate()