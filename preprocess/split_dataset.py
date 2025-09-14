#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的数据集划分脚本
"""

import pandas as pd
import os

def split_dataset(input_file, output_dir, train_ratio=0.7, test_ratio=0.2, valid_ratio=0.1, random_state=42):
    """
    将CSV文件划分为训练集、测试集、验证集
    """
    # 读取数据
    df = pd.read_csv(input_file)
    
    required_columns = ['sentence', 'head', 'tail', 'head_offset', 'tail_offset', 'head_type', 'tail_type']
    df = df[required_columns]
    
    # 打乱数据
    df = df.sample(frac=1, random_state=random_state).reset_index(drop=True)
    
    # 计算划分点
    total_size = len(df)
    train_size = int(total_size * train_ratio)
    test_size = int(total_size * test_ratio)
    
    # 划分数据
    train_df = df[:train_size]
    test_df = df[train_size:train_size + test_size]
    valid_df = df[train_size + test_size:]
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存文件
    train_file = os.path.join(output_dir, 'train.csv')
    test_file = os.path.join(output_dir, 'test.csv')
    valid_file = os.path.join(output_dir, 'valid.csv')
    
    train_df.to_csv(train_file, index=False, encoding='utf-8')
    test_df.to_csv(test_file, index=False, encoding='utf-8')
    valid_df.to_csv(valid_file, index=False, encoding='utf-8')

def main():
    # 配置参数
    input_file = '/root/KG/data/w2ner_relations.csv'
    output_dir = '/root/KG/DeepKE/example/re/standard/data/origin'
    
    # 执行数据集划分
    split_dataset(
        input_file=input_file,
        output_dir=output_dir,
        train_ratio=0.7,
        test_ratio=0.2, 
        valid_ratio=0.1,
        random_state=42
    )

if __name__ == '__main__':
    main()