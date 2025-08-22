# 知识图谱构建优化版本

## 主要改进

### 1. 置信度信息保留
- **问题**: 原版本在构建知识图谱时丢失了关系的置信度信息
- **解决方案**: 
  - 在CSV生成阶段保留完整的置信度信息
  - 在知识图谱构建时保留置信度、实体类型等元信息
  - 按置信度排序关系，优先展示高质量关系
  - 添加置信度分布统计

### 2. 迭代构建优化
- **问题**: 原版本迭代逻辑过于简单，只是复制数据而没有真正扩展
- **解决方案**:
  - 实现真正的知识图谱扩展逻辑
  - 基于现有实体发现新的关系
  - 多重收敛条件判断
  - 智能停止机制

### 3. 质量评估与统计
- 添加详细的质量统计信息
- 实时监控扩展效果
- 置信度分布分析
- 迭代收敛分析

## 新增功能

### 1. 智能收敛判断
```python
# 多重收敛条件:
# 1. 扩展比例低于阈值
# 2. 新增关系数为0
# 3. 连续多次低增长
```

### 2. 置信度管理
```python
# 置信度分布统计
confidence_stats = {
    'high': len([x for x in data if x.confidence >= 0.8]),
    'medium': len([x for x in data if 0.6 <= x.confidence < 0.8]),
    'low': len([x for x in data if x.confidence < 0.6])
}
```

### 3. 强制重新生成选项
```bash
# 强制重新生成CSV文件
python process_text_stream.py --force_regenerate
```

## 使用方法

### 基本使用
```bash
python process_text_stream.py \
    --text_file /path/to/your/text_file.txt \
    --project your_project_name \
    --confidence_threshold 0.7 \
    --max_iterations 5 \
    --convergence_threshold 0.1
```

### 参数说明
- `--text_file`: 输入的文本流文件路径
- `--project`: 项目名称，用于创建输出目录
- `--enable_ner`: 启用NER实体提取（默认启用）
- `--confidence_threshold`: 关系预测置信度阈值（默认0.7）
- `--max_iterations`: 最大迭代次数（默认5）
- `--convergence_threshold`: 迭代收敛阈值（默认0.1）
- `--force_regenerate`: 强制重新生成CSV文件
- `--gpu`: GPU设备号（默认0）

### 高级使用
```bash
# 高质量模式（高置信度阈值）
python process_text_stream.py \
    --confidence_threshold 0.8 \
    --convergence_threshold 0.05 \
    --max_iterations 10

# 快速模式（低置信度阈值，少迭代）
python process_text_stream.py \
    --confidence_threshold 0.6 \
    --max_iterations 3
```

## 输出文件结构

```
data/your_project/
├── predictions.csv              # 原始预测结果
├── predictions_enhanced.csv     # NER增强后的预测结果
├── base.json                   # 基础知识图谱
├── base_refined.json           # 精炼后的基础知识图谱
├── iteration_version_0.json    # 第1次迭代结果
├── iteration_version_1.json    # 第2次迭代结果
├── ...
├── final_state.json           # 最终状态保存
└── history/                   # 历史状态保存
    ├── 20240101-120000_iter_v1
    └── ...
```

## 质量指标

### 1. 置信度分布
- 高置信度关系（≥0.8）
- 中等置信度关系（0.6-0.8）
- 低置信度关系（<0.6）

### 2. 扩展效果
- 扩展比例：新增关系数 / 原有关系数
- 总体扩展率：总新增关系数 / 原始关系数
- 平均置信度变化

### 3. 收敛分析
- 连续低增长检测
- 自动停止条件
- 迭代效果评估

## 性能优化

1. **内存优化**: 流式处理大文件，避免一次性加载
2. **计算优化**: 智能跳过已存在的实体对
3. **存储优化**: 增量保存，避免重复计算
4. **并行优化**: 支持GPU加速的NER和关系预测

## 故障排除

### 常见问题

1. **CSV文件为空**
   - 检查置信度阈值是否过高
   - 确认NER模型是否正常加载
   - 验证输入文本格式

2. **迭代不收敛**
   - 降低收敛阈值
   - 增加最大迭代次数
   - 检查模型质量

3. **内存不足**
   - 减少批处理大小
   - 使用CPU模式
   - 分批处理大文件

### 调试模式
```bash
# 启用详细日志
export PYTHONPATH=/root/KG/DeepKE:$PYTHONPATH
python -u process_text_stream.py --project debug_test 2>&1 | tee debug.log
```

## 版本历史

- **v1.0**: 基础版本
- **v2.0**: 优化版本
  - 添加置信度保留
  - 改进迭代逻辑
  - 增强质量评估
  - 添加智能收敛