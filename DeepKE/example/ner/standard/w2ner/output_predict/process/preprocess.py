#将predict.json中的数据转换为my_test.csv格式
import json
import csv
import os

def load_entity_types(entity_file_path):
    """
    从实体集CSV文件加载词汇及其类型，构建词汇->类型映射字典
    格式：每行包含中文词汇和类型标识（如"抽象数据类型,CON"）
    """
    entity_type_map = {}
    
    try:
        with open(entity_file_path, 'r', encoding='utf-8') as f:
            # 跳过可能的标题行（根据实体集文件实际内容调整）
            lines = f.readlines()
            start_line = 0
            if lines[0].strip() == 'vocabulary':
                start_line = 1
            
            for line in lines[start_line:]:
                line = line.strip()
                # 检查有效行：包含逗号分隔的词汇和类型
                if line and ',' in line:
                    parts = line.split(',', 1)  # 按第一个逗号分割
                    if len(parts) == 2:
                        word = parts[0].strip()
                        # 处理带有序号的情况 (如 "1 抽象数据类型" -> "抽象数据类型")
                        if ' ' in word:
                            word = word.split(' ', 1)[1].strip()
                        entity_type = parts[1].strip()
                        entity_type_map[word] = entity_type
    
        print(f"成功加载实体类型: 共 {len(entity_type_map)} 个词汇")
        return entity_type_map
    
    except FileNotFoundError:
        print(f"错误: 实体集文件未找到 - {entity_file_path}")
        return {}
    except Exception as e:
        print(f"加载实体集时出错: {str(e)}")
        return {}

# 设置文件路径（请根据实际情况修改）
entity_file_path = '/root/KG/DeepKE/example/ner/prepare-data/vocab_dict.csv'
input_json_file = '/root/KG/DeepKE/example/ner/standard/w2ner/output_predict/data/predict.json'
output_csv_file = '/root/KG/DeepKE/example/re/standard/data/my_origin/test.csv'

# 加载实体类型映射
entity_type_map = load_entity_types(entity_file_path)

# 如果实体映射为空则退出
if not entity_type_map:
    print("错误: 无法加载实体类型映射，请检查实体集文件路径和格式")
    exit(1)

try:
    # 读取JSON文件
    with open(input_json_file, 'r', encoding='utf-8') as json_file:
        json_data = json.load(json_file)
    
    # 准备CSV数据
    csv_data = []
    fieldnames = ['sentence', 'head', 'tail', 'head_type', 'tail_type']
    
    # 统计类型匹配情况
    matched_head = 0
    matched_tail = 0
    
    # 遍历JSON数据
    for item in json_data:
        sentence = item.get('sentence', '')
        head = item.get('head', '')
        tail = item.get('tail', '')
        
        # 从实体映射中获取类型
        head_type = entity_type_map.get(head, '')
        tail_type = entity_type_map.get(tail, '')
        
        # 更新匹配统计
        if head_type: matched_head += 1
        if tail_type: matched_tail += 1
        
        csv_data.append({
            'sentence': sentence,
            'head': head,
            'tail': tail,
            'head_type': head_type,
            'tail_type': tail_type
        })
    
    # 写入CSV文件
    os.makedirs(os.path.dirname(output_csv_file), exist_ok=True)
    with open(output_csv_file, 'w', encoding='utf-8', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)
    
    # 输出结果统计
    print(f"\n转换成功! 已处理 {len(csv_data)} 条数据")
    print(f"头实体类型匹配率: {matched_head}/{len(csv_data)} ({matched_head/len(csv_data)*100:.1f}%)")
    print(f"尾实体类型匹配率: {matched_tail}/{len(csv_data)} ({matched_tail/len(csv_data)*100:.1f}%)")
    print(f"CSV文件已保存至: {output_csv_file}")

except FileNotFoundError:
    print(f"错误: 文件未找到 - {input_json_file} 或 {output_csv_file}")
except json.JSONDecodeError:
    print(f"错误: JSON文件格式无效 - {input_json_file}")
except Exception as e:
    print(f"错误: {str(e)}")