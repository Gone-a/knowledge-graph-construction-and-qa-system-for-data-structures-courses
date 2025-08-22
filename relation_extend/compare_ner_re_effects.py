#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比启用NER+RE前后的知识图谱拓展效果
"""

import os
import pandas as pd
import json
from collections import Counter

def analyze_csv_file(csv_path, name):
    """
    分析CSV预测结果文件
    """
    if not os.path.exists(csv_path):
        print(f"文件不存在: {csv_path}")
        return None
    
    df = pd.read_csv(csv_path)
    
    print(f"\n=== {name} ===")
    
    # 基本统计
    total_predictions = len(df)
    unique_sentences = df['sentence'].nunique()
    unique_entities = set()
    for _, row in df.iterrows():
        unique_entities.add(row['head'])
        unique_entities.add(row['tail'])
    
    # 关系类型分布
    relation_counts = df['relation'].value_counts()
    
    # 置信度统计
    avg_confidence = None
    high_conf_count = None
    high_conf_ratio = None
    if 'confidence' in df.columns:
        avg_confidence = df['confidence'].mean()
        high_conf_count = len(df[df['confidence'] >= 0.7])
        high_conf_ratio = high_conf_count / len(df) * 100
    
    # 来源统计（如果有source列）
    source_stats = {}
    if 'source' in df.columns:
        source_stats = df['source'].value_counts().to_dict()
    
    print(f"总预测数: {total_predictions}")
    print(f"涉及句子数: {unique_sentences}")
    print(f"唯一实体数: {len(unique_entities)}")
    print(f"平均每句预测数: {total_predictions / unique_sentences:.2f}")
    
    if avg_confidence is not None:
        print(f"平均置信度: {avg_confidence:.4f}")
        print(f"高置信度预测数 (>=0.7): {high_conf_count}")
        print(f"高置信度比例: {high_conf_ratio:.2f}%")
    
    if source_stats:
        print("\n数据来源分布:")
        for source, count in source_stats.items():
            percentage = count / total_predictions * 100
            print(f"  {source}: {count} ({percentage:.2f}%)")
    
    print("\n关系类型分布:")
    for relation, count in relation_counts.items():
        percentage = count / total_predictions * 100
        print(f"  {relation}: {count} ({percentage:.2f}%)")
    
    return {
        'total_predictions': total_predictions,
        'unique_sentences': unique_sentences,
        'unique_entities': len(unique_entities),
        'avg_confidence': avg_confidence,
        'high_conf_count': high_conf_count,
        'relation_counts': relation_counts.to_dict(),
        'source_stats': source_stats
    }

def main():
    """
    主函数：对比启用NER+RE前后的效果
    """
    print("=== 对比启用NER+RE前后的知识图谱拓展效果 ===")
    
    # 分析原始预测结果
    original_file = "data/predictions.csv"
    print("\n1. 分析原始预测结果:")
    original_stats = None
    if os.path.exists(original_file):
        original_stats = analyze_csv_file(original_file, "原始预测结果")
    else:
        print(f"未找到原始预测文件: {original_file}")
    
    # 分析增强预测结果（使用新生成的包含source字段的文件）
    enhanced_file = "data/test_enhanced_with_source.csv"
    print("\n2. 分析增强预测结果:")
    enhanced_stats = None
    if os.path.exists(enhanced_file):
        enhanced_stats = analyze_csv_file(enhanced_file, "增强预测结果")
    else:
        print(f"未找到增强预测文件: {enhanced_file}")
    
    # 对比分析
    if original_stats and enhanced_stats:
        print("\n" + "="*60)
        print("对比分析")
        print("="*60)
        
        # 预测数量变化
        print("\n预测数量变化:")
        original_count = original_stats['total_predictions']
        enhanced_count = enhanced_stats['total_predictions']
        increase = enhanced_count - original_count
        increase_ratio = (increase / original_count) * 100 if original_count > 0 else 0
        print(f"  原始: {original_count}")
        print(f"  增强: {enhanced_count}")
        print(f"  增加: {increase} (+{increase_ratio:.2f}%)")
        
        # 实体数量变化
        print("\n实体数量变化:")
        original_entities = original_stats['unique_entities']
        enhanced_entities = enhanced_stats['unique_entities']
        entity_increase = enhanced_entities - original_entities
        print(f"  原始: {original_entities}")
        print(f"  增强: {enhanced_entities}")
        print(f"  增加: {entity_increase} (+{entity_increase/original_entities*100:.2f}%)")
        
        # 置信度变化
        if original_stats['avg_confidence'] and enhanced_stats['avg_confidence']:
            print("\n置信度变化:")
            orig_conf = original_stats['avg_confidence']
            enh_conf = enhanced_stats['avg_confidence']
            print(f"  原始平均置信度: {orig_conf:.4f}")
            print(f"  增强平均置信度: {enh_conf:.4f}")
            print(f"  变化: {enh_conf - orig_conf:+.4f}")
        
        # 关系类型变化
        print("\n关系类型变化:")
        original_relations = original_stats['relation_counts']
        enhanced_relations = enhanced_stats['relation_counts']
        
        all_relations = set(original_relations.keys()) | set(enhanced_relations.keys())
        for relation in all_relations:
            original_count = original_relations.get(relation, 0)
            enhanced_count = enhanced_relations.get(relation, 0)
            if enhanced_count > original_count:
                increase = enhanced_count - original_count
                print(f"  {relation}: {original_count} -> {enhanced_count} (+{increase})")
        
        # 分析数据来源分布（如果增强文件包含source字段）
        if enhanced_stats.get('source_stats'):
            print("\n数据来源分析:")
            source_stats = enhanced_stats['source_stats']
            for source, count in source_stats.items():
                percentage = count / enhanced_count * 100
                print(f"  {source}: {count} ({percentage:.2f}%)")
    
    # 详细分析NER+RE新增关系
    if enhanced_stats and os.path.exists(enhanced_file):
        print("\n" + "="*60)
        print("新增关系分析")
        print("="*60)
        
        enhanced_df = pd.read_csv(enhanced_file)
        
        # 查看source字段（如果存在）
        if 'source' in enhanced_df.columns:
            # 分析NER+RE新增的关系
            ner_re_predictions = enhanced_df[enhanced_df['source'] == 'ner_re_predicted']
            if len(ner_re_predictions) > 0:
                print(f"\nNER+RE新增关系数: {len(ner_re_predictions)}")
                ner_re_relations = ner_re_predictions['relation'].value_counts()
                print("NER+RE新增关系类型分布:")
                for relation, count in ner_re_relations.items():
                    percentage = count / len(ner_re_predictions) * 100
                    print(f"  {relation}: {count} ({percentage:.2f}%)")
                
                print(f"\nNER+RE新增关系平均置信度: {ner_re_predictions['confidence'].mean():.4f}")
                print(f"NER+RE新增高置信度关系数 (>=0.7): {len(ner_re_predictions[ner_re_predictions['confidence'] >= 0.7])}")
    
    print("\n分析完成！")

if __name__ == "__main__":
    main()