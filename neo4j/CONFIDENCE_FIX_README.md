# 知识图谱置信度信息修复说明

## 问题描述

在构建知识图谱时，所有关系的置信度都显示为默认值1.0，而原始数据文件 `/root/KG/relation_extend/data/stream_project/iteration_version_0.json` 中包含了真实的置信度信息。

## 问题原因

在 `product.py` 文件的 `load_json_data` 方法中，第177行硬编码设置了 `'confidence': 1.0`，没有从JSON数据中提取真实的置信度值。

```python
# 修复前的问题代码
'confidence': 1.0  # JSON数据默认置信度为1.0
```

## 修复方案

修改了 `load_json_data` 方法，正确提取JSON数据中的置信度信息：

```python
# 修复后的代码
# 从JSON数据中提取置信度信息
confidence = relation.get('confidence', 1.0)

relations_data.append({
    'sentence': sentence,
    'head': head_entity,
    'tail': tail_entity,
    'relation': relation_type,
    'head_clean': head_clean,
    'tail_clean': tail_clean,
    'confidence': confidence  # 使用实际的置信度值
})
```

## 修复验证

### 修复前
- 所有关系置信度都是 1.0
- 无法区分关系质量

### 修复后
- 置信度范围: 0.7001 ~ 0.9534
- 平均置信度: 0.7826
- 总关系数: 3716
- 置信度分布:
  - 极高 (≥0.9): 53 (1.4%)
  - 高 (0.8-0.9): 1303 (35.1%)
  - 中 (0.7-0.8): 2360 (63.5%)
  - 低 (<0.7): 0 (0.0%)

## 使用方法

### 1. 重新构建知识图谱

```bash
cd /root/KG/neo4j
python product.py --json /root/KG/relation_extend/data/stream_project/iteration_version_0.json
```

### 2. 验证置信度信息

```bash
cd /root/KG/neo4j
python verify_confidence.py
```

### 3. 查询示例

#### 查询高置信度关系 (≥0.8)
```cypher
MATCH (a)-[r]->(b) 
WHERE r.confidence >= 0.8 
RETURN a.name, type(r), b.name, r.confidence 
ORDER BY r.confidence DESC
```

#### 查询置信度最高的关系
```cypher
MATCH (a)-[r]->(b) 
RETURN a.name, type(r), b.name, r.confidence 
ORDER BY r.confidence DESC 
LIMIT 10
```

#### 统计置信度分布
```cypher
MATCH ()-[r]->()
RETURN 
    min(r.confidence) as min_conf,
    max(r.confidence) as max_conf,
    avg(r.confidence) as avg_conf,
    count(r) as total_relations
```

## 优化建议

### 1. 质量筛选
- 可以根据置信度阈值筛选高质量关系
- 建议使用 ≥0.8 的置信度作为高质量关系标准

### 2. 可视化优化
- 在图可视化时，可以用置信度调整边的粗细
- 高置信度关系用粗线，低置信度关系用细线

### 3. 查询优化
- 在复杂查询中优先考虑高置信度关系
- 可以设置置信度权重进行关系排序

## 文件说明

- `product.py`: 主要的知识图谱构建脚本（已修复）
- `verify_confidence.py`: 置信度验证脚本
- `CONFIDENCE_FIX_README.md`: 本说明文档

## 注意事项

1. 确保Neo4j数据库正在运行
2. 确保环境变量 `NEO4J_KEY` 设置正确，或使用默认密码 "123456"
3. 重新构建知识图谱会清空现有数据
4. 建议在重新构建前备份重要数据

## 技术细节

### 修改的文件
- `/root/KG/neo4j/product.py` (第169-178行)

### 新增的文件
- `/root/KG/neo4j/verify_confidence.py`
- `/root/KG/neo4j/CONFIDENCE_FIX_README.md`

### 数据源
- 原始数据: `/root/KG/relation_extend/data/stream_project/iteration_version_0.json`
- 包含9323个关系，置信度范围0.7000-0.9534

修复完成后，知识图谱现在能够正确保存和使用置信度信息，为后续的质量评估和关系筛选提供了重要依据。