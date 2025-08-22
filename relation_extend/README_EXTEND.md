# 知识图谱关系拓展功能

本项目提供了基于CSV文件的知识图谱关系拓展功能，能够从预处理的关系抽取结果中构建知识图谱，并支持迭代优化。

## 功能特点

- **CSV数据输入**: 直接从CSV文件读取关系抽取结果
- **NER实体增强**: 集成W2NER模型，从原始文本中提取更多实体，优化知识图谱质量
- **知识图谱构建**: 将关系数据转换为标准知识图谱格式
- **迭代优化**: 支持多轮迭代构建（简化版本）
- **断点续传**: 支持从中断点继续构建，避免重复计算
- **灵活配置**: 支持自定义项目配置和参数
- **智能回退**: 当NER模型不可用时，自动使用简化版实体提取

## 文件结构

```
relation_extend/
├── extend.py                 # 主程序入口
├── knowledge_graph_builder.py # 知识图谱构建器
├── ner_extractor.py          # NER实体提取器（新增）
├── test_extend.py            # 测试脚本
├── README_EXTEND.md          # 说明文档
├── data/                     # 数据目录
│   └── predictions.csv      # 关系抽取结果（输入文件）
└── prepare/                  # 预处理模块
    ├── __init__.py
    ├── cprint.py            # 彩色输出
    ├── filter.py            # 数据过滤
    ├── preprocess.py        # 文本预处理
    ├── process.py           # 处理模块（已简化）
    └── utils.py             # 工具函数
```

## 核心类说明

### CSVRelationExtractor
基于CSV文件的关系抽取器，负责从预处理的CSV文件中读取关系抽取结果。

**主要方法:**
- `extract_relations()`: 从CSV文件读取关系抽取结果

### CSVKnowledgeGraphBuilder
基于CSV文件的知识图谱构建器，负责将CSV数据转换为知识图谱格式。

**主要方法:**
- `build_from_csv()`: 从CSV文件构建知识图谱
- `iterative_build(max_iterations, convergence_threshold)`: 迭代构建知识图谱

### KnowledgeGraphBuilder
底层知识图谱构建器，提供基础的图谱构建功能。

**主要方法:**
- `load_predictions_from_csv()`: 从CSV加载预测结果（支持NER增强）
- `get_base_kg_from_csv()`: 构建基础知识图谱
- `run_iteration()`: 运行单次迭代

### NERExtractor
基于W2NER模型的命名实体识别提取器，用于增强实体提取。

**主要方法:**
- `extract_entities_from_text(text)`: 从文本中提取实体
- `enhance_predictions_with_ner(csv_path, output_path)`: 使用NER增强CSV预测结果

### SimpleNERExtractor
简化版NER提取器，当W2NER模型不可用时的备选方案。

**主要方法:**
- `extract_entities_from_text(text)`: 使用规则方法提取实体
- `enhance_predictions_with_ner(csv_path, output_path)`: 简单增强CSV预测结果

## 使用方法

### 1. 基本使用

```bash
# 确保CSV文件存在并包含正确格式的数据
# CSV文件应包含: sentence, head, tail, relation, confidence 列
ls -la data/predictions.csv

# 运行知识图谱构建
python extend.py --project my_project --csv_path data/predictions.csv
```

### 2. 断点续传

```bash
# 从之前保存的状态继续
python extend.py --resume data/my_project/history/20240101-120000_iter_v2
```

### 3. 使用NER增强功能

```bash
# 启用NER增强功能（使用简化版）
python extend.py --project my_project --enable_ner

# 使用W2NER模型进行增强（需要提供模型文件）
python extend.py --project my_project --enable_ner \
    --ner_model_path /path/to/w2ner_model.bin \
    --ner_config_path /path/to/w2ner_config.json
```

### 4. 参数说明

- `--project`: 项目名称，用于创建数据目录
- `--resume`: 从指定的状态文件继续迭代
- `--gpu`: GPU设备ID（当前版本未使用）
- `--csv_path`: CSV文件路径（默认为data/predictions.csv）
- `--enable_ner`: 启用NER实体提取增强功能
- `--ner_model_path`: W2NER模型文件路径（可选）
- `--ner_config_path`: W2NER模型配置文件路径（可选）

## 工作流程

1. **数据加载**: 从CSV文件读取关系抽取结果
2. **NER增强**（可选）: 
   - 使用W2NER模型或简化规则从原始句子中提取更多实体
   - 生成新的实体对组合，扩充关系候选
   - 保存增强后的预测结果到predictions_enhanced.csv
3. **数据过滤**: 过滤掉关系为'none'的记录
4. **格式转换**: 将CSV数据转换为知识图谱标准格式
5. **基础图谱构建**: 生成base.json和base_refined.json文件
6. **迭代构建**: 
   - 复制当前数据到新的迭代版本
   - 检查收敛条件（简化版本总是收敛）
   - 保存迭代结果
7. **结果保存**: 保存每次迭代的结果和构建状态

## 配置说明

### CSV文件格式

CSV文件应包含以下列：

```csv
sentence,head,tail,relation,confidence
"张三是北京大学的教授","张三","北京大学","工作于",0.95
"李四在清华大学学习","李四","清华大学","就读于",0.88
```

### 数据要求

- CSV文件格式正确
- 包含必要的列：sentence, head, tail, relation, confidence
- 关系不为'none'的记录将被保留

## 测试

运行测试脚本验证功能：

```bash
# 测试所有功能
python test_extend.py --test all

# 只测试CSV关系抽取器
python test_extend.py --test extractor

# 只测试知识图谱构建器
python test_extend.py --test builder
```

## 输出文件

- `data/[project]/base.json`: 基础知识图谱
- `data/[project]/base_refined.json`: 精炼后的基础知识图谱
- `data/[project]/iteration_version_[N].json`: 第N轮迭代的结果
- `data/[project]/history/`: 历史状态文件

## 注意事项

1. **数据格式**: 确保CSV文件格式正确，包含所有必要列
2. **文件路径**: 确保CSV文件路径正确且文件存在
3. **数据质量**: 输入CSV数据质量直接影响知识图谱质量
4. **磁盘空间**: 确保有足够磁盘空间存储输出文件
5. **编码格式**: 确保CSV文件使用UTF-8编码

## 故障排除

### 常见问题

1. **CSV文件读取失败**：检查文件路径是否正确，确认文件格式和编码
2. **数据格式错误**：检查CSV列名是否正确，确认数据类型匹配
3. **输出目录创建失败**：检查磁盘空间，确认写入权限
4. **依赖包缺失**：安装pandas: `pip install pandas`，检查其他依赖包

### 调试建议

1. 使用测试脚本验证各个组件
2. 检查日志输出了解详细错误信息
3. 从小规模数据开始测试
4. 验证CSV文件格式和内容

## 扩展功能

可以根据需要扩展以下功能：

1. **多格式支持**: 支持更多数据输入格式
2. **质量评估**: 添加关系质量评估指标
3. **可视化界面**: 实现知识图谱可视化
4. **增量更新**: 支持增量式的知识图谱更新
5. **统计分析**: 添加数据统计分析功能