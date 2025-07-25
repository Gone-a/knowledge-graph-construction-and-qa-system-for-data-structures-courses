import pandas as pd
from collections import Counter
import torch

# 读取训练数据
csv_path = '/root/KG/DeepKE/example/re/standard/data/origin/train.csv'
df = pd.read_csv(csv_path)

# 用 relation.csv 的 index 作为标签编码
relation_map_path = '/root/KG/DeepKE/example/re/standard/data/origin/relation.csv'
relation_df = pd.read_csv(relation_map_path)
relation2idx = dict(zip(relation_df['relation'], relation_df['index']))

labels = df['relation'].map(relation2idx).tolist()
label_count = Counter(labels)
num_classes = len(relation2idx)
total_count = len(labels)

weights = [total_count / label_count[i] for i in range(num_classes)]
class_weights = torch.tensor(weights, dtype=torch.float)
print('类别权重:', class_weights)
print('类别顺序:', [relation for relation, idx in sorted(relation2idx.items(), key=lambda x: x[1])])
