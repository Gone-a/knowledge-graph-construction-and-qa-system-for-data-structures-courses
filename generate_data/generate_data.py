#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱数据生成器 - 优化版
生成高质量的知识图谱构建训练数据
"""

import os
import time
import concurrent.futures
from openai import OpenAI
from tqdm import tqdm
import random
import logging
import re
import json
from collections import Counter

# 禁用HTTP请求日志
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

# ============================= 配置 =============================
class Config:
    API_KEY = os.environ.get("ARK_API_KEY")
    BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
    MODEL = "doubao-1-5-lite-32k-250115"
    NUM_RECORDS = 3000
    CONCURRENCY = 30  # 进一步增加并发数提高吞吐量
    OUTPUT_FILE = "/root/KG/generate_data/data_backups/knowledge_graph_sentences.txt"
    TIMEOUT = 30      # 减少超时时间提高效率
    RETRY_COUNT = 2   # 减少重试次数降低延迟
    DELAY_BETWEEN_REQUESTS = 0  # 移除延迟提高速度

# ========================= 知识库 =============================
KNOWLEDGE_GRAPH_BASE = {
    "数据结构": [
        "数组", "链表", "栈", "队列", "哈希表", "树", "图", "堆", "集合", "映射",
        "双向链表", "循环链表", "二叉树", "二叉搜索树", "AVL树", "红黑树",
        "B树", "B+树", "字典树", "线段树", "并查集", "优先队列", "双端队列"
    ],
    "算法": [
        "冒泡排序", "插入排序", "选择排序", "归并排序", "快速排序", "堆排序",
        "计数排序", "基数排序", "桶排序", "深度优先搜索", "广度优先搜索",
        "二分查找", "线性查找", "哈希查找", "Dijkstra算法", "Floyd算法",
        "Kruskal算法", "Prim算法", "拓扑排序", "动态规划", "贪心算法", "分治算法"
    ],
    "算法特性": [
        "时间复杂度", "空间复杂度", "稳定性", "原地排序", "比较排序", "非比较排序",
        "递归", "迭代", "分治", "贪心", "动态规划", "回溯", "剪枝", "优化"
    ],
    "数据结构特性": [
        "线性结构", "非线性结构", "顺序存储", "链式存储", "随机访问", "顺序访问",
        "LIFO", "FIFO", "平衡", "完全", "满", "有序", "无序", "连通", "强连通"
    ],
    "操作类型": [
        "插入", "删除", "查找", "遍历", "排序", "合并", "分割", "旋转",
        "平衡", "压缩", "扩容", "缩容", "初始化", "销毁", "复制", "移动"
    ],
    "应用场景": [
        "数据库索引", "编译器", "操作系统", "网络路由", "图像处理", "机器学习",
        "搜索引擎", "缓存系统", "文件系统", "内存管理", "任务调度", "负载均衡"
    ]
}

# ========================= 核心函数 =============================
def create_client():
    return OpenAI(base_url=Config.BASE_URL, api_key=Config.API_KEY, timeout=Config.TIMEOUT)

def generate_kg_optimized_prompts(num_records):
    """生成针对知识图谱构建优化的提示词"""
    
    # 关系型提示模板 (40%)
    relation_templates = [
        "请用一句话描述{entity1}和{entity2}之间的关系",
        "简述{entity1}如何与{entity2}相关联",
        "解释{entity1}对{entity2}的作用或影响",
        "说明{entity1}和{entity2}的区别或联系",
        "描述{entity1}在{entity2}中的应用",
        "比较{entity1}与{entity2}的性能特点",
        "分析{entity1}和{entity2}的适用场景差异",
        "阐述{entity1}相对于{entity2}的优势",
        "说明{entity1}与{entity2}的实现复杂度对比"
    ]
    
    # 实体描述型模板 (30%)
    entity_templates = [
        "请描述{entity}的主要特征和应用场景",
        "简述{entity}的工作原理和优缺点",
        "解释{entity}的定义、特点和使用条件",
        "说明{entity}的结构组成和操作方法",
        "描述{entity}的时间复杂度和空间复杂度特性",
        "分析{entity}的核心算法思想",
        "介绍{entity}的典型实现方式",
        "阐述{entity}在实际项目中的价值"
    ]
    
    # 操作型模板 (20%)
    operation_templates = [
        "描述在{entity}中进行{operation}操作的具体步骤",
        "说明{entity}进行{operation}时需要注意的问题",
        "解释{entity}的{operation}操作实现机制",
        "分析{entity}中{operation}操作的时间复杂度",
        "介绍{entity}的{operation}过程和优化方法"
    ]
    
    # 应用场景型模板 (10%)
    application_templates = [
        "分析{entity}在{scenario}领域的技术优势",
        "解释{entity}如何解决{scenario}中的关键问题",
        "描述{entity}在{scenario}系统中的核心作用",
        "说明{entity}在{scenario}项目中的实际应用"
    ]
    
    prompts = []
    
    # 计算各类型数量
    relation_count = int(num_records * 0.4)
    entity_count = int(num_records * 0.3)
    operation_count = int(num_records * 0.2)
    remaining_count = num_records - relation_count - entity_count - operation_count
    
    # 生成关系型提示词
    for _ in range(relation_count):
        template = random.choice(relation_templates)
        entities = random.sample([e for entities in KNOWLEDGE_GRAPH_BASE.values() for e in entities], 2)
        prompt = template.format(entity1=entities[0], entity2=entities[1])
        prompts.append(prompt)
    
    # 生成实体描述型提示词
    for _ in range(entity_count):
        template = random.choice(entity_templates)
        entity = random.choice([e for entities in KNOWLEDGE_GRAPH_BASE.values() for e in entities])
        prompt = template.format(entity=entity)
        prompts.append(prompt)
    
    # 生成操作型提示词
    for _ in range(operation_count):
        template = random.choice(operation_templates)
        entity = random.choice([e for entities in KNOWLEDGE_GRAPH_BASE.values() for e in entities])
        operation = random.choice(KNOWLEDGE_GRAPH_BASE["操作类型"])
        prompt = template.format(entity=entity, operation=operation)
        prompts.append(prompt)
    
    # 生成应用场景型提示词
    for _ in range(remaining_count):
        template = random.choice(application_templates)
        entity = random.choice([e for entities in KNOWLEDGE_GRAPH_BASE.values() for e in entities])
        scenario = random.choice(KNOWLEDGE_GRAPH_BASE["应用场景"])
        prompt = template.format(entity=entity, scenario=scenario)
        prompts.append(prompt)
    
    random.shuffle(prompts)
    return prompts

def is_valid_kg_response(text):
    """验证响应是否适合知识图谱构建"""
    if not text or len(text.strip()) < 15:
        return False
    
    # 检查是否包含技术实体
    all_entities = [e for entities in KNOWLEDGE_GRAPH_BASE.values() for e in entities]
    has_entity = any(entity in text for entity in all_entities)
    
    # 检查无效模式
    invalid_patterns = [
        r'我无法|我不能|抱歉|对不起',
        r'作为AI|作为语言模型',
        r'请注意|需要注意的是',
        r'^\s*$',
        r'^[^。！？]*$'
    ]
    
    for pattern in invalid_patterns:
        if re.search(pattern, text):
            return False
    
    return has_entity and 15 <= len(text) <= 250

def call_api_with_retry(prompt):
    """带重试机制的API调用"""
    client = create_client()
    
    for attempt in range(Config.RETRY_COUNT):
        try:
            if Config.DELAY_BETWEEN_REQUESTS > 0:
                time.sleep(Config.DELAY_BETWEEN_REQUESTS)
            
            response = client.chat.completions.create(
                model=Config.MODEL,
                messages=[
                    {"role": "system", "content": "生成准确完整的计算机技术描述。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            
            if is_valid_kg_response(content):
                return content
            else:
                continue
                
        except Exception as e:
            if attempt == Config.RETRY_COUNT - 1:
                logging.warning(f"API调用最终失败: {e}")
                return None
            logging.debug(f"API调用重试 {attempt + 1}/{Config.RETRY_COUNT}: {e}")
            time.sleep(0.5)  # 减少重试延迟
    
    return None

def post_process_sentences(sentences):
    """数据后处理优化"""
    print("\n🔧 正在进行数据后处理优化...")
    
    processed = []
    for sentence in sentences:
        # 清理空格和标点
        cleaned = re.sub(r'\s+', ' ', sentence.strip())
        cleaned = re.sub(r'[，。！？；：""''（）【】《》]+$', '', cleaned)
        
        # 确保以句号结尾
        if not cleaned.endswith(('。', '！', '？')):
            cleaned += '。'
        
        # 长度和质量检查
        if 15 <= len(cleaned) <= 250:
            all_entities = [e for entities in KNOWLEDGE_GRAPH_BASE.values() for e in entities]
            if any(entity in cleaned for entity in all_entities):
                processed.append(cleaned)
    
    print(f"✅ 后处理完成: 保留 {len(processed)} 条，移除 {len(sentences) - len(processed)} 条")
    return processed

def process_large_batch(prompts):
    """批量处理提示词，实时保存数据"""
    print(f"\n🚀 开始批量生成 {len(prompts)} 条数据...")
    
    results = []
    batch_size = 50  # 每50条数据保存一次
    temp_results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=Config.CONCURRENCY) as executor:
        future_to_prompt = {executor.submit(call_api_with_retry, prompt): prompt for prompt in prompts}
        
        with tqdm(total=len(prompts), desc="生成数据", unit="条") as pbar:
            for future in concurrent.futures.as_completed(future_to_prompt):
                result = future.result()
                if result:
                    temp_results.append(result)
                    
                    # 每达到batch_size就保存一次
                    if len(temp_results) >= batch_size:
                        processed_batch = post_process_sentences(temp_results)
                        save_batch_data(processed_batch, Config.OUTPUT_FILE)
                        results.extend(processed_batch)
                        temp_results = []
                        
                pbar.update(1)
    
    # 保存剩余数据
    if temp_results:
        processed_batch = post_process_sentences(temp_results)
        save_batch_data(processed_batch, Config.OUTPUT_FILE)
        results.extend(processed_batch)
    
    # 去重
    unique_results = list(set(results))
    print(f"✅ 批量生成完成: {len(unique_results)} 条有效数据")
    return unique_results

def analyze_data_quality(sentences):
    """分析生成数据的质量"""
    print("\n📊 数据质量分析:")
    
    all_entities = [e for entities in KNOWLEDGE_GRAPH_BASE.values() for e in entities]
    
    # 统计实体覆盖率
    entity_mentions = Counter()
    for sentence in sentences:
        for entity in all_entities:
            if entity in sentence:
                entity_mentions[entity] += 1
    
    covered_entities = len(entity_mentions)
    total_entities = len(all_entities)
    coverage_rate = (covered_entities / total_entities) * 100
    
    print(f"🎯 实体覆盖率: {covered_entities}/{total_entities} ({coverage_rate:.1f}%)")
    
    # 统计关系词出现频率
    relation_words = ['是', '有', '具有', '包含', '属于', '用于', '可以', '能够', '实现', '支持', '采用']
    relation_counts = Counter()
    for sentence in sentences:
        for word in relation_words:
            if word in sentence:
                relation_counts[word] += 1
    
    print(f"🔗 关系词分布: {dict(relation_counts.most_common(5))}")
    
    # 统计句子长度分布
    lengths = [len(sentence) for sentence in sentences]
    print(f"📏 句子长度: 平均{sum(lengths)/len(lengths):.1f}字, 范围{min(lengths)}-{max(lengths)}字")
    
    return {
        'entity_coverage': coverage_rate,
        'covered_entities': covered_entities,
        'relation_distribution': dict(relation_counts),
        'avg_length': sum(lengths)/len(lengths),
        'length_range': (min(lengths), max(lengths))
    }

def save_batch_data(sentences, filename):
    """实时保存批量数据到文件"""
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'a', encoding='utf-8') as f:
            for sentence in sentences:
                f.write(sentence + '\n')
        print(f"💾 已保存 {len(sentences)} 条数据")
    except Exception as e:
        print(f"❌ 保存失败: {e}")

def save_data(sentences, filename):
    """保存数据到文件"""
    try:
        # 如果是最终保存，分析数据质量
        quality_report = analyze_data_quality(sentences)
        return quality_report
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return None

def main():
    """主函数"""
    # 检查API密钥
    if not Config.API_KEY:
        print("❌ 错误: 请先设置环境变量 ARK_API_KEY")
        return
    
    print("🚀 知识图谱数据生成器启动")
    print(f"📋 目标: 生成 {Config.NUM_RECORDS} 条高质量训练数据")
    print(f"⚙️ 配置: 并发数 {Config.CONCURRENCY}, 超时 {Config.TIMEOUT}s")
    start_time = time.time()
    
    try:
        # 生成提示词
        print(f"\n🔧 生成 {Config.NUM_RECORDS} 个优化提示词...")
        prompts = generate_kg_optimized_prompts(Config.NUM_RECORDS)
        
        # 批量生成数据
        sentences = process_large_batch(prompts)
        
        if not sentences:
            print("❌ 未生成任何有效数据")
            return
        
        # 保存数据集
        print(f"\n💾 保存数据集...")
        quality_report = save_data(sentences, Config.OUTPUT_FILE)
        
        # 完成提示
        end_time = time.time()
        print(f"\n🎉 数据生成完成!")
        print(f"📊 最终统计: {len(sentences)} 条高质量数据")
        print(f"🎯 实体覆盖率: {quality_report['entity_coverage']:.1f}%")
        print(f"⏱️ 总耗时: {end_time - start_time:.2f} 秒")
        print(f"⚡ 平均速度: {len(sentences)/(end_time - start_time):.1f} 条/秒")
        print(f"💾 数据已保存到: {Config.OUTPUT_FILE}")
        print(f"💡 建议: 数据可直接用于知识图谱模型训练")
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        logging.error(f"程序异常: {e}")

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('knowledge_generator.log'),
            logging.StreamHandler()
        ]
    )
    
    main()