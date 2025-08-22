#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据集划分脚本
将w2ner_relations.csv划分为训练集、测试集、验证集
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import os

def split_dataset(input_file, output_dir, train_ratio=0.7, test_ratio=0.2, valid_ratio=0.1, random_state=42):
    """
    将CSV文件划分为训练集、测试集、验证集
    
    Args:
        input_file: 输入CSV文件路径
        output_dir: 输出目录
        train_ratio: 训练集比例
        test_ratio: 测试集比例
        valid_ratio: 验证集比例
        random_state: 随机种子
    """
    # 确保比例之和为1
    assert abs(train_ratio + test_ratio + valid_ratio - 1.0) < 1e-6, "比例之和必须为1"
    
    # 读取数据
    print(f"正在读取数据文件: {input_file}")
    df = pd.read_csv(input_file)
    print(f"总共读取 {len(df)} 条数据")
    
    
    required_columns = ['sentence', 'head', 'tail', 'head_offset', 'tail_offset', 'head_type', 'tail_type']
    df = df[required_columns]
    
    # 打乱数据
    df = df.sample(frac=1, random_state=random_state).reset_index(drop=True)
    
    # 计算划分点
    total_size = len(df)
    train_size = int(total_size * train_ratio)
    test_size = int(total_size * test_ratio)
    valid_size = total_size - train_size - test_size
    
    print(f"数据划分:")
    print(f"  训练集: {train_size} 条 ({train_ratio:.1%})")
    print(f"  测试集: {test_size} 条 ({test_ratio:.1%})")
    print(f"  验证集: {valid_size} 条 ({valid_size/total_size:.1%})")
    
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
    
    print(f"\n数据集已保存到:")
    print(f"  训练集: {train_file}")
    print(f"  测试集: {test_file}")
    print(f"  验证集: {valid_file}")
    
    # 验证保存的文件
    print(f"\n验证保存结果:")
    for name, file_path in [('训练集', train_file), ('测试集', test_file), ('验证集', valid_file)]:
        if os.path.exists(file_path):
            saved_df = pd.read_csv(file_path)
            print(f"  {name}: {len(saved_df)} 条数据")
        else:
            print(f"  {name}: 文件保存失败")

def main():
    # 配置参数
    input_file = '/root/KG/data/w2ner_relations.csv'
    output_dir = '/root/KG/DeepKE/example/re/standard/data/origin'
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 输入文件不存在 {input_file}")
        return
    
    # 执行数据集划分
    split_dataset(
        input_file=input_file,
        output_dir=output_dir,
        train_ratio=0.7,
        test_ratio=0.2, 
        valid_ratio=0.1,
        random_state=42
    )
    
    print("\n数据集划分完成!")

if __name__ == '__main__':
    main()