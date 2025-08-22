# 知识图谱问答系统 - 双接口说明

本系统提供了两个主要的查询接口，用于从知识图谱中检索信息。

## 接口概述

### 接口1: `find_entity_relations`
**功能**: 接收实体列表，查找所有相关的关系和实体

**参数**:
- `entities`: 实体名称列表 (必需)
- `confidence_threshold`: 置信度阈值，默认0.7 (可选)

**返回**: 包含关系信息的列表，每个元素包含:
- `source`: 源实体
- `relation`: 关系类型
- `target`: 目标实体
- `confidence`: 置信度
- `source_sentence`: 来源句子

**使用示例**:
```python
# 查找"二叉树"相关的所有关系
results = qa_system.find_entity_relations(["二叉树"], confidence_threshold=0.8)
for result in results:
    print(f"{result['source']} → {result['relation']} → {result['target']}")
```

### 接口2: `find_entities_by_relation`
**功能**: 接收实体和关系，找到有这个关系的其他实体

**参数**:
- `entities`: 实体名称列表 (必需)
- `relation`: 关系类型 (必需)
- `confidence_threshold`: 置信度阈值，默认0.7 (可选)

**返回**: 与接口1相同的数据结构

**使用示例**:
```python
# 查找与"二叉树"有"依赖"关系的实体
results = qa_system.find_entities_by_relation(["二叉树"], "依赖")
for result in results:
    print(f"{result['source']} → {result['relation']} → {result['target']}")
```

## 支持的关系类型

数据库中当前支持的关系类型:
- `依赖`: 表示依赖关系
- `属性`: 表示属性关系
- `相对`: 表示相对关系
- `被包含`: 表示包含关系
- `被依赖`: 表示被依赖关系

## 向后兼容性

系统保持了对原有`query_graph`接口的兼容性，支持英文关系映射:

```python
# 使用英文关系映射
dict_input = {"entities": ["二叉树"], "relation": "rely"}  # rely映射为"依赖"
result = qa_system.query_graph("问题", dict_input)

# 直接使用中文关系
dict_input = {"entities": ["二叉树"], "relation": "依赖"}
result = qa_system.query_graph("问题", dict_input)
```

## 英文-中文关系映射表

| 英文关系 | 中文关系 |
|---------|----------|
| rely    | 依赖     |
| b-rely  | 被依赖   |
| belg    | 被包含   |
| attr    | 属性     |
| relative| 相对     |

## 使用建议

1. **接口1** 适用于探索性查询，当你想了解某个实体的所有相关信息时
2. **接口2** 适用于精确查询，当你明确知道要查找特定关系时
3. 建议设置合适的`confidence_threshold`来过滤低质量结果
4. 可以通过调整置信度阈值来平衡结果的数量和质量

## 完整示例

参见 `interface_usage_example.py` 文件获取完整的使用示例。

## 错误处理

系统会对输入参数进行验证:
- 空的实体列表会抛出 `ValueError`
- 不支持的关系类型会抛出 `ValueError`
- 数据库连接问题会抛出相应的连接异常