import pandas as pd
from collections import Counter
import torch

def calc_class_weights(csv_path = '/root/KG/DeepKE/example/re/standard/data/origin/train.csv',relation_map_path = '/root/KG/DeepKE/example/re/standard/data/origin/relation.csv'):
    
    # 读取训练数据
    
    df = pd.read_csv(csv_path)

    # 用 relation.csv 的 index 作为标签编码
    
    relation_df = pd.read_csv(relation_map_path)
    relation2idx = dict(zip(relation_df['relation'], relation_df['index']))

    labels = df['relation'].map(relation2idx).tolist()
    label_count = Counter(labels)
    num_classes = len(relation2idx)
    total_count = len(labels)

    epsilon = 1e-6  # 极小值，避免除零
    weights = [total_count / (label_count[i] + epsilon) if label_count[i] != 0 else 1.0 for i in range(num_classes)]
    class_weights = torch.tensor(weights, dtype=torch.float)
    print('类别权重:', class_weights)
    print('类别顺序:', [relation for relation, idx in sorted(relation2idx.items(), key=lambda x: x[1])])
    return class_weights

if __name__ == '__main__':
    calc_class_weights()