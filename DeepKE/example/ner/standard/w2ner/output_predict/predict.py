import os
import csv
import time
import json
import threading
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
    "rely", "b-rely",  # 依赖/被依赖
    "belg", "b-belg",  # 包含/属于
    "syno", "relative",  # 同义/相对（取代anto）
    "attr", "b-attr",  # 拥有/属性
    "none"             # 无关系
]

# 依赖关系关键词（用于后处理修正）
DEPENDENCY_KEYWORDS = {"依赖", "取决于", "需要", "基于", "利用", "要求"}

# 用户提供的详细规则描述（优化后的提示词）
RULES_DESCRIPTION = """
请严格遵循以下规则分析关系类型：
1. **依赖关系 (rely)**: 实体存在明显的逻辑顺序关系，head的学习或功能依赖于tail 
   - 示例: "哈希查找的效率依赖于哈希函数" → (哈希查找效率, 哈希函数)=rely
2. **被依赖关系 (b-rely)**: 实体存在明显的逻辑顺序关系，head被tail依赖 
   - 示例: "栈是实现函数调用的基础" → (函数调用, 栈)=b-rely
3. **包含关系 (belg)**: tail作为概念范畴包含head (整体-部分关系)
   - 示例: "二叉树由根节点组成" → (二叉树, 根节点)=belg
4. **属于关系 (b-belg)**: head属于tail的概念范畴 (is-a关系)
   - 示例: "AVL树是一种自平衡二叉搜索树" → (AVL树, 二叉搜索树)=b-belg
5. **同义关系 (syno)**: head和tail在不同叫法下指向相同概念
   - 示例: "哈希表也叫散列表" → (哈希表, 散列表)=syno
6. **相对关系 (relative)**: head和tail在功能上形成互补对立
   - 示例: "深度优先搜索与广度优先搜索是图遍历的两种基本方法" → (深度优先搜索, 广度优先搜索)=relative
7. **拥有关系 (attr)**: tail是描述head的属性实体
   - 示例: "数组具有固定长度特性" → (数组, 固定长度)=attr
8. **属性关系 (b-attr)**: head是描述tail的属性实体
   - 示例: "时间复杂度是分析算法效率的重要指标" → (时间复杂度, 算法效率)=b-attr
9. **无关系 (none)**: head和tail不存在直接语义关联
   - 示例: "红黑树和快速排序都是常用算法" → (红黑树, 快速排序)=none

严格注意事项：
- 只能使用以上9种关系类型
- 覆盖数据结构与算法全领域：线性结构、树结构、图结构、算法设计等
- 重点分析三种核心关系：
  a) 数据结构组件间关系（如节点-边）
  b) 算法与实现技术关系（如排序-分治）
  c) 性能指标关联（时间复杂度-空间复杂度）
"""

# 缓存实现（减少重复API调用）
class RelationCache:
    def __init__(self):
        self.cache = {}
        self.lock = threading.Lock()
    
    def get(self, key):
        """获取缓存结果"""
        with self.lock:
            return self.cache.get(key)
    
    def set(self, key, value):
        """设置缓存结果"""
        with self.lock:
            self.cache[key] = value

# 初始化OpenAI客户端
def create_client():
    return OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=os.environ.get("ARK_API_KEY"),
        timeout=60  # 60秒超时
    )

# 优化后的提示词生成（增加示例和格式约束）
def generate_relation_prompt(item):
    """生成基于规则和示例的提示词"""
    return f"""
# 关系分析任务
{RULES_DESCRIPTION}

## 输出要求
- 只输出关系类型名称（如：rely）
- 禁止添加解释或标点符号
- 输出必须严格使用以下名称：{", ".join(RELATION_TYPES)}

## 示例分析
1. 句子: "栈和队列都是线性数据结构"
   实体: ("栈", "队列") → 关系: none
2. 句子: "二叉树由根节点和子节点组成"
   实体: ("二叉树", "根节点") → 关系: belg
3. 句子: "哈希表的查找效率取决于哈希函数的质量"
   实体: ("查找效率", "哈希函数") → 关系: rely
4. 句子: "队列是先进先出的数据结构"
   实体: ("队列", "先进先出") → 关系: attr
5. 句子: "深度优先搜索和广度优先搜索是图遍历的两种方法"
   实体: ("深度优先搜索", "广度优先搜索") → 关系: relative

## 待分析内容
句子: "{item['sentence']}"
实体对: ("{item['head']}", "{item['tail']}")
关系类型:
"""

# 解析API响应并验证关系类型
def parse_and_validate_relation(response_content):
    """解析并验证API返回的关系类型"""
    # 提取响应中的关系类型
    response_content = response_content.strip()
    
    if not response_content:
        return "none"
    
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
    return "none"

# 结果后处理优化
def postprocess_relation(item, predicted_relation):
    """基于规则修正预测结果"""
    head = item['head'].lower()
    tail = item['tail'].lower()
    sentence = item['sentence'].lower()
    
    # 规则1: 同类实体默认无关系
    if predicted_relation == "belg" and head.split()[-1] == tail.split()[-1]:
        return "none"
    
    # 规则2: 同词根默认为同义
    if predicted_relation == "none" and head.split('_')[0] == tail.split('_')[0]:
        return "syno"
    
    # 规则3: 修正方向性错误
    if predicted_relation == "rely":
        # 检查句子中是否包含依赖关键词
        for kw in DEPENDENCY_KEYWORDS:
            if kw in sentence:
                # 检查实体位置关系
                head_pos = sentence.find(head)
                tail_pos = sentence.find(tail)
                if head_pos != -1 and tail_pos != -1 and tail_pos < head_pos:
                    return "b-rely"
    
    return predicted_relation

# 调用火山引擎API分析关系（带缓存和后处理）
def analyze_relation_with_retry(item, client, cache, max_retries=2):
    """带缓存和重试机制的关系分析API调用"""
    # 生成缓存键（使用句子和实体对）
    cache_key = f"{item['sentence']}||{item['head']}||{item['tail']}"
    
    # 检查缓存
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # 生成提示词
    prompt = generate_relation_prompt(item)
    attempts = 0
    
    while attempts < max_retries:
        try:
            # 调用API
            response = client.chat.completions.create(
                model="doubao-1-5-pro-32k-250115",
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
            relation = parse_and_validate_relation(response_content)
            
            # 后处理修正
            relation = postprocess_relation(item, relation)
            
            # 缓存结果
            cache.set(cache_key, relation)
            return relation
            
        except Exception as e:
            logging.error(f"API调用失败: {str(e)} - 重试 {attempts+1}/{max_retries}")
            attempts += 1
            time.sleep(1.5 ** attempts)  # 指数退避（降低等待时间）
    
    logging.error(f"关系分析失败: {item}")
    return "none"  # 重试失败后返回默认值

# 数据预处理优化
def preprocess_data(data):
    """过滤无效实体对，减少不必要的API调用"""
    valid_data = []
    skipped_count = 0
    
    for item in data:
        # 跳过空实体
        if not item['head'].strip() or not item['tail'].strip():
            skipped_count += 1
            continue
            
        # 跳过相同实体
        if item['head'].lower() == item['tail'].lower():
            skipped_count += 1
            continue
            
        # 跳过明显无关联的实体（距离超过100字符）
        try:
            head_offset = int(item['head_offset'])
            tail_offset = int(item['tail_offset'])
            head_end = head_offset + len(item['head'])
            
            if abs(tail_offset - head_end) > 100:
                # 直接标记为无关系，不调用API
                item['predicted_relation'] = "none"
                valid_data.append(item)
                skipped_count += 1
                continue
        except ValueError:
            pass  # 如果位置无效，继续处理
        
        valid_data.append(item)
    
    logging.info(f"数据预处理: 原始数据 {len(data)} 条, 过滤 {skipped_count} 条, 剩余 {len(valid_data)} 条")
    return valid_data

# 处理单个条目
def process_item(item, client, cache):
    """处理单个条目，生成符合图片格式的输出行"""
    # 如果预处理已添加关系，直接使用
    if 'predicted_relation' in item:
        relation = item['predicted_relation']
    else:
        # 调用API分析关系（带缓存）
        relation = analyze_relation_with_retry(item, client, cache)
    
    # 按照图片中的格式返回CSV行
    return [
        item["sentence"],
        relation,
        item["head"],
        item["tail"],
        str(item["head_offset"]),
        str(item["tail_offset"])
    ]

# 批量处理JSON文件并输出CSV
def process_json_file(input_file, output_file, concurrency=3):  # 降低并发数减少成本
    """
    处理JSON文件，输出符合图片格式的CSV
    :param input_file: 输入JSON文件路径
    :param output_file: 输出CSV文件路径
    :param concurrency: 并发数（降低以减少API压力）
    """
    # 验证API密钥
    if not os.environ.get("ARK_API_KEY"):
        print("❌❌ 错误: 请先设置环境变量 ARK_API_KEY")
        return
    
    # 读取输入文件
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌❌ 读取文件失败: {str(e)}")
        return
    
    print(f"✅ 已加载 {len(data)} 条记录")
    
    # 数据预处理
    data = preprocess_data(data)
    print(f"⚡ 预处理后保留 {len(data)} 条记录")
    
    client = create_client()
    cache = RelationCache()  # 创建缓存实例
    processed_rows = []
    
    # 添加CSV标题行（与图片一致）
    header = ["sentence", "relation", "head", "tail", "head_offset", "tail_offset"]
    processed_rows.append(header)
    
    # 使用线程池并发处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        # 准备任务
        futures = {
            executor.submit(process_item, item, client, cache): item
            for item in data
        }
        
        # 处理结果带进度条
        completed = tqdm(
            concurrent.futures.as_completed(futures),
            total=len(data),
            desc="分析语义关系",
            dynamic_ncols=True
        )
        
        for future in completed:
            try:
                result = future.result()
                processed_rows.append(result)
            except Exception as e:
                logging.error(f"处理失败: {str(e)}")
                # 添加默认值作为回退
                processed_rows.append([
                    item.get("sentence", "处理失败"), 
                    "none", 
                    item.get("head", "N/A"), 
                    item.get("tail", "N/A"), 
                    str(item.get("head_offset", 0)), 
                    str(item.get("tail_offset", 0))
                ])
    
    # 保存为CSV文件
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
        
        print("\n📊 关系类型分布统计:")
        for rel in RELATION_TYPES:
            count = relation_counts[rel]
            percent = count / total_rows * 100 if total_rows > 0 else 0
            print(f"- {rel}: {count} 条 ({percent:.1f}%)")
        
        # 计算缓存命中率
        if hasattr(cache, 'cache'):
            cache_size = len(cache.cache)
            hit_rate = (cache_size / total_rows) * 100 if total_rows > 0 else 0
            print(f"\n💾 缓存效果: 缓存了 {cache_size} 个结果, 缓存命中率 {hit_rate:.1f}%")
            
    except Exception as e:
        print(f"❌❌ 保存文件失败: {str(e)}")

if __name__ == "__main__":
    # 配置输入输出文件路径
    input_file = "train_predict.json"      # 替换为您的输入文件路径
    output_file = "optimized_relations.csv"  # 输出CSV文件
    
    # 执行处理（降低并发数减少API压力）
    process_json_file(input_file, output_file, concurrency=3)