#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本流处理脚本
将data_stream.txt中的纯文本数据转换为CSV格式，然后使用现有的知识图谱拓展系统进行处理
"""

import os
import csv
import argparse
from typing import List, Dict
from ner_extractor import create_ner_extractor
from relation_predictor import create_relation_predictor
from knowledge_graph_builder import KnowledgeGraphBuilder
from prepare import cprint as ct
from tqdm import tqdm

def process_text_stream_to_csv(text_file_path: str, output_csv_path: str, 
                               ner_extractor=None, relation_predictor=None) -> str:
    """
    将文本流文件转换为CSV格式
    
    Args:
        text_file_path: 输入的文本文件路径
        output_csv_path: 输出的CSV文件路径
        ner_extractor: NER提取器实例
        relation_predictor: 关系预测器实例
    
    Returns:
        生成的CSV文件路径
    """
    print(ct.green(f"开始处理文本流文件: {text_file_path}"))
    
    # 读取文本文件
    with open(text_file_path, 'r', encoding='utf-8') as f:
        sentences = [line.strip() for line in f if line.strip()]
    
    print(ct.blue(f"共读取到 {len(sentences)} 条文本"))
    
    # 准备CSV数据
    csv_data = []
    
    if ner_extractor and relation_predictor:
        print(ct.blue("使用NER+RE模型进行实体和关系提取..."))
        
        for sentence in tqdm(sentences, desc="处理文本"):
            # 提取实体
            entities = ner_extractor.extract_entities_from_text(sentence)
            
            if len(entities) < 2:
                # 如果实体少于2个，跳过该句子
                continue
            
            # 生成所有实体对组合
            for i in range(len(entities)):
                for j in range(i + 1, len(entities)):
                    head_entity = entities[i]
                    tail_entity = entities[j]
                    
                    # 预测关系
                    relation_data = {
                        'sentence': sentence,
                        'head': head_entity['text'],
                        'tail': tail_entity['text'],
                        'head_type': head_entity.get('label', 'UNK'),
                        'tail_type': tail_entity.get('label', 'UNK')
                    }
                    
                    # 使用关系预测器预测关系
                    result = relation_predictor.predict_relation_for_pair(
                        sentence, head_entity['text'], tail_entity['text']
                    )
                    
                    predicted_relation = result.get('relation', 'none')
                    confidence = result.get('confidence', 0.0)
                    
                    # 只保留置信度高于阈值的关系
                    if confidence >= relation_predictor.confidence_threshold and predicted_relation != 'none':
                        csv_data.append({
                            'sentence': sentence,
                            'head': head_entity['text'],
                            'tail': tail_entity['text'],
                            'relation': predicted_relation,
                            'confidence': confidence,
                            'head_type': head_entity.get('label', 'UNK'),
                            'tail_type': tail_entity.get('label', 'UNK')
                        })
    else:
        print(ct.yellow("NER或RE模型未启用，使用简单规则提取..."))
        
        # 简单规则：假设每个句子包含一些基本的实体关系
        for sentence in tqdm(sentences, desc="处理文本"):
            # 这里可以添加简单的规则提取逻辑
            # 目前先跳过，因为没有预训练的实体和关系
            pass
    
    # 保存为CSV文件
    if csv_data:
        # 确保包含所有必要字段，特别是置信度
        fieldnames = ['sentence', 'head', 'tail', 'relation', 'confidence', 'head_type', 'tail_type']
        
        # 对数据按置信度排序，优先保留高置信度的关系
        csv_data.sort(key=lambda x: x.get('confidence', 0.0), reverse=True)
        
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        print(ct.green(f"CSV文件已生成: {output_csv_path}"))
        print(ct.blue(f"共生成 {len(csv_data)} 条关系记录"))
        
        # 统计置信度分布
        confidence_stats = {
            'high': len([x for x in csv_data if x.get('confidence', 0) >= 0.8]),
            'medium': len([x for x in csv_data if 0.6 <= x.get('confidence', 0) < 0.8]),
            'low': len([x for x in csv_data if x.get('confidence', 0) < 0.6])
        }
        print(ct.blue(f"置信度分布 - 高(≥0.8): {confidence_stats['high']}, 中(0.6-0.8): {confidence_stats['medium']}, 低(<0.6): {confidence_stats['low']}"))
    else:
        print(ct.yellow("未生成任何关系记录，创建空CSV文件"))
        
        # 创建空CSV文件以保持格式一致性
        fieldnames = ['sentence', 'head', 'tail', 'relation', 'confidence', 'head_type', 'tail_type']
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
    
    return output_csv_path

def main():
    parser = argparse.ArgumentParser(description='处理文本流数据并构建知识图谱')
    parser.add_argument('--text_file', type=str, default='/root/KG/generate_data/data_backups/knowledge_graph_sentences.txt', 
                       help='输入的文本流文件路径')
    parser.add_argument('--project', type=str, default='stream_project', 
                       help='项目名称')
    parser.add_argument('--enable_ner', action='store_true', default=True, 
                       help='启用NER实体提取')
    parser.add_argument('--confidence_threshold', type=float, default=0.7, 
                       help='关系预测置信度阈值')
    parser.add_argument('--max_iterations', type=int, default=5, 
                       help='最大迭代次数')
    parser.add_argument('--convergence_threshold', type=float, default=0.1, 
                       help='迭代收敛阈值')
    parser.add_argument('--gpu', type=int, default=0, 
                       help='GPU设备号')
    parser.add_argument('--force_regenerate', action='store_true', 
                       help='强制重新生成CSV文件，即使文件已存在')
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.text_file):
        print(ct.red(f"错误: 输入文件不存在 - {args.text_file}"))
        return
    
    # 创建输出目录
    data_dir = os.path.join("data", args.project)
    os.makedirs(data_dir, exist_ok=True)
    
    # 生成CSV文件路径
    csv_output_path = os.path.join(data_dir, "predictions.csv")
    
    # 初始化NER和RE模型（如果启用）
    ner_extractor = None
    relation_predictor = None
    
    if args.enable_ner:
        try:
            print(ct.blue("初始化NER提取器..."))
            ner_extractor = create_ner_extractor()
            
            print(ct.blue("初始化关系预测器..."))
            relation_predictor = create_relation_predictor(
                confidence_threshold=args.confidence_threshold
            )
        except Exception as e:
            print(ct.yellow(f"NER/RE模型初始化失败: {e}"))
            print(ct.yellow("将使用简单规则处理"))
    
    # 处理文本流并生成CSV
    try:
        # 检查是否需要重新生成CSV文件
        if os.path.exists(csv_output_path) and not args.force_regenerate:
            print(ct.blue(f"CSV文件已存在: {csv_output_path}"))
            print(ct.yellow("使用 --force_regenerate 参数可强制重新生成"))
            csv_path = csv_output_path
        else:
            if args.force_regenerate and os.path.exists(csv_output_path):
                print(ct.yellow(f"强制重新生成CSV文件: {csv_output_path}"))
            
            csv_path = process_text_stream_to_csv(
                args.text_file, csv_output_path, ner_extractor, relation_predictor
            )
        
            # 检查生成的CSV文件是否有内容
            import pandas as pd
            df = pd.read_csv(csv_path)
            
            if len(df) == 0:
                print(ct.yellow("警告: 生成的CSV文件为空，无法构建知识图谱"))
                print(ct.blue("建议检查输入文本格式或调整置信度阈值"))
                return
            
            print(ct.green(f"成功生成CSV文件，包含 {len(df)} 条记录"))
        

        # 使用现有的知识图谱构建器处理CSV文件
        print(ct.green("开始构建知识图谱..."))
        
        # 修改args以适配KnowledgeGraphBuilder
        args.csv_path = csv_path
        
        kg_builder = KnowledgeGraphBuilder(args)
        
        # 构建基础知识图谱
        kg_builder.get_base_kg_from_csv()
        
        # 进行迭代构建
        from extend import iterative_build
        """
        result_paths = iterative_build(
            kg_builder, 
            max_iterations=args.max_iterations,
            convergence_threshold=args.convergence_threshold
        )
        """
        print(ct.green("知识图谱构建完成!"))
        print(ct.blue(f"结果保存在: {data_dir}"))
        
        for i, path in enumerate(result_paths):
            print(ct.blue(f"  迭代 {i}: {path}"))
            
    except Exception as e:
        print(ct.red(f"处理过程中出现错误: {e}"))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()