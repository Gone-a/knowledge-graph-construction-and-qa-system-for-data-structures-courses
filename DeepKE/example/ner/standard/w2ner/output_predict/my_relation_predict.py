import os
import csv
import time
import json
import concurrent.futures
from tqdm import tqdm
from openai import OpenAI
import logging

# 配置日志
logging.basicConfig(
    filename='relation_processing.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 严格遵循用户提供的7种关系类型
RELATION_TYPES = [
    "rely", "none", "belg", "b-belg", 
    "syno", "b-rely", "anto","attr", "b-attr"
]

# 用户提供的详细规则描述（用于提示词）
RULES_DESCRIPTION = """
请严格遵循以下规则分析关系类型：
1. **依赖关系 (rely)**: 实体存在明显的逻辑顺序关系，head的学习或功能依赖于tail (例如: head的实现/效率需要tail支持)。
2. **被依赖关系 (b-rely)**: 实体存在明显的逻辑顺序关系，head被tail依赖 (tail的学习或功能依赖于head)。
3. **包含关系 (belg)**: 实体存在明显从属关系，tail作为概念范畴包含head (整体-部分关系)。
4. **属于关系 (b-belg)**: 实体存在明显从属关系，head属于tail的概念范畴 (is-a关系)。
5. **同义关系 (syno)**: head和tail在不同叫法下指向相同概念 (同一实体的不同名称)。
6. **反义关系 (anto)**: head和tail在概念叙述上具有相反含义 (语义对立)。
7. **拥有关系 (attr)**: tail是描述head的属性实体 (head具有tail属性)。
8. **属性关系 (b-attr)**: head是描述tail的属性实体 (tail具有head属性)。
9. **无关系 (none)**: head和tail不存在直接语义关联。

严格注意事项：
- 只能使用以上9种关系类型，不要新增或修改
- 关系判断必须基于实体间客观存在的语义关系
- 既考虑表面词语关联，也关注深层概念联系
"""

# 初始化OpenAI客户端
def create_client():
    return OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=os.environ.get("ARK_API_KEY"),
        timeout=60  # 60秒超时
    )

# 生成关系分析提示词（整合详细规则）
def generate_relation_prompt(item):
    """生成基于规则的提示词"""
    return f"""
你是一位严谨的数据结构专家，请基于以下规则分析句子中"{item['head']}"和"{item['tail']}"之间的语义关系：

{RULES_DESCRIPTION}

句子内容：{item['sentence']}
头部实体："{item['head']}" (位置：第{item['head_offset']}个字符)
尾部实体："{item['tail']}" (位置：第{item['tail_offset']}个字符)

分析步骤：
1. 确定两个实体之间是否存在语义关联
2. 如有语义关联，判断符合哪种关系类型的定义
3. 如无直接语义关联，使用"无关系"

请直接输出关系类型名称：
"""

# 解析API响应并验证关系类型
def parse_and_validate_relation(response_content):
    """解析并验证API返回的关系类型"""
    # 提取响应中的关系类型
    response_content = response_content.strip()
    
    if not response_content:
        return "无关系"
    
    # 检查是否匹配有效的类型名称
    for relation in RELATION_TYPES:
        if relation == response_content:
            return relation
    
    # 处理特殊情况
    for relation in RELATION_TYPES:
        # 部分匹配检查
        if response_content.startswith(relation[:2]):
            return relation
    
    logging.warning(f"无效关系类型: {response_content}")
    return "无关系"

# 调用火山引擎API分析关系
def analyze_relation_with_retry(item, client, max_retries=3):
    """带重试机制的关系分析API调用"""
    prompt = generate_relation_prompt(item)
    attempts = 0
    
    while attempts < max_retries:
        try:
            # 调用API
            response = client.chat.completions.create(
                model="doubao-1-5-lite-32k-250115",
                messages=[
                    {
                        "role": "system", 
                        "content": f"你是一位严谨的数据结构专家，严格按照规则分析关系，只使用以下类型: {', '.join(RELATION_TYPES)}"
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.0  # 零随机性确保稳定性
            )
            
            # 解析和验证响应
            response_content = response.choices[0].message.content.strip()
            return parse_and_validate_relation(response_content)
            
        except Exception as e:
            logging.error(f"API调用失败: {str(e)} - 重试 {attempts+1}/{max_retries}")
            attempts += 1
            time.sleep(2 ** attempts)  # 指数退避
    
    logging.error(f"关系分析失败: {item}")
    return "无关系"  # 重试失败后返回默认值

# 处理单个条目
def process_item(item, client):
    """处理单个条目，生成符合图片格式的输出行"""
    # 确保位置信息是字符串
    head_offset = str(item["head_offset"])
    tail_offset = str(item["tail_offset"])
    
    # 调用API分析关系
    relation = analyze_relation_with_retry(item, client)
    
    # 按照图片中的格式返回CSV行
    return [
        item["sentence"],
        relation,
        item["head"],
        item["tail"],
        head_offset,
        tail_offset
    ]

# 批量处理JSON文件并输出CSV
def process_json_file(input_file, output_file, concurrency=5):
    """
    处理JSON文件，输出符合图片格式的CSV
    :param input_file: 输入JSON文件路径
    :param output_file: 输出CSV文件路径
    :param concurrency: 并发数
    """
    # 验证API密钥
    if not os.environ.get("ARK_API_KEY"):
        print("❌ 错误: 请先设置环境变量 ARK_API_KEY")
        return
    
    # 读取输入文件
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 读取文件失败: {str(e)}")
        return
    
    print(f"✅ 已加载 {len(data)} 条记录")
    print(f"⚡ 开始处理，并发数: {concurrency}")
    print(f"📏 使用关系类型: {', '.join(RELATION_TYPES)}")
    
    client = create_client()
    processed_rows = []
    
    # 添加CSV标题行（与图片一致）
    header = ["sentence", "relation", "head", "tail", "head_offset", "tail_offset"]
    processed_rows.append(header)
    
    # 使用线程池并发处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        # 准备任务
        futures = {
            executor.submit(process_item, item, client): item
            for item in data
        }
        
        # 处理结果带进度条
        completed = tqdm(
            concurrent.futures.as_completed(futures),
            total=len(data),
            desc="分析语义关系"
        )
        
        for future in completed:
            try:
                result = future.result()
                processed_rows.append(result)
            except Exception as e:
                logging.error(f"处理失败: {str(e)}")
                # 添加默认值作为回退
                processed_rows.append([
                    "处理失败，请检查日志", 
                    "无关系", 
                    "N/A", 
                    "N/A", 
                    "0", 
                    "0"
                ])
    
    # 保存为CSV文件（与图片格式完全一致）
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(processed_rows)
        print(f"✅ 处理完成! CSV结果已保存到: {output_file}")
        
        # 统计关系分布
        relation_counts = {rel: 0 for rel in RELATION_TYPES}
        total_rows = len(processed_rows) - 1  # 减去标题行
        
        if total_rows > 0:
            for row in processed_rows[1:]:  # 跳过标题行
                relation = row[1]
                if relation in relation_counts:
                    relation_counts[relation] += 1
        
        print("\n📊 关系类型分布:")
        for rel in RELATION_TYPES:
            count = relation_counts[rel]
            percent = count / total_rows * 100 if total_rows > 0 else 0
            print(f"- {rel}: {count} 条 ({percent:.1f}%)")
            
    except Exception as e:
        print(f"❌ 保存文件失败: {str(e)}")

if __name__ == "__main__":
    # 配置输入输出文件路径
    input_file = "train_predict.json"      # 替换为您的输入文件路径
    output_file = "relation_predict.csv"      # 输出CSV文件（与图片一致）
    
    # 执行处理
    process_json_file(input_file, output_file, concurrency=5)