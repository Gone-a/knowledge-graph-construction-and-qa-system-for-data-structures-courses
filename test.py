import os
import time
import concurrent.futures
from openai import OpenAI
from tqdm import tqdm
import random
import logging
import re  # 添加正则表达式模块用于检测无效模式

# ============================= 配置区域 =============================
class Config:
    # 从环境变量获取API Key（确保设置 ARK_API_KEY）
    API_KEY = os.environ.get("ARK_API_KEY")
    
    # 火山引擎API端点
    BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
    
    # 模型配置
    MODEL = "doubao-1-5-lite-32k-250115"
    
    # 运行参数
    NUM_RECORDS = 10000  # 目标3000条数据
    CONCURRENCY = 15    # 适当提高并发数（根据测试结果调整）
    OUTPUT_FILE = "knowledge_3000.txt"
    TIMEOUT = 180       # 增加API超时时间（秒）
    RETRY_COUNT = 5     # 失败请求重试次数
    DELAY_BETWEEN_REQUESTS = 0.05  # 请求延迟（避免速率限制）

# ========================= 高级知识库定义 =============================
# 扩展知识库以支持3000条不同主题
ADVANCED_KNOWLEDGE_BASE = {
    "基本数据结构": [
        "数组", "链表", "栈", "队列", "哈希表", "树", "图", "堆",
        "双向链表", "循环链表", "二叉树", "二叉搜索树",
        "顺序表", "单链表", "线性表", "集合", "映射"
    ],
    
    "基础树结构": [
        "树的定义", "树的节点", "树的度", "树的高度", "树的深度",
        "叶子节点", "父节点", "子节点", "根节点", "二叉树的遍历",
        "满二叉树", "完全二叉树", "平衡二叉树"
    ],
    
    "基础图结构": [
        "图的顶点", "图的边", "有向图", "无向图", "加权图", "邻接矩阵",
        "邻接表", "路径", "回路", "连通图"
    ],
    
    "基础排序算法": [
        "冒泡排序", "插入排序", "选择排序", "归并排序", "快速排序",
        "堆排序", "简单排序", "比较排序", "交换排序"
    ],
    
    "基础搜索算法": [
        "顺序查找", "二分查找", "深度优先搜索", "广度优先搜索",
        "线性查找", "树的查找"
    ],
    
    "算法基础策略": [
        "分治策略", "贪心策略", "动态规划入门", "回溯法基础",
        "穷举法", "迭代法", "递归基础"
    ],
    
    "基本专业概念": [
        "时间复杂度", "空间复杂度", "算法效率", "数据类型", "抽象数据类型",
        "指针", "引用", "线性结构", "非线性结构", "数据的逻辑结构",
        "数据的物理结构", "存储结构", "操作效率", "稳定性"
    ]
}

# ====================== 初始化OpenAI客户端 =======================
def create_client():
    return OpenAI(
        base_url=Config.BASE_URL,
        api_key=Config.API_KEY,
        timeout=Config.TIMEOUT
    )

# ====================== 生成高级提示词 ============================
def generate_advanced_prompts(num_records):
    """生成具有语义多样性的提示词"""
    # 修改后的模板：明确要求完整回答，禁止使用引导语
    prompt_templates = [
        "请用不超过25字的一句话完整解释{concept}的核心概念，不要使用'如下'或'以下'等引导词",
        "作为数据结构专家，请直接用单句描述{concept}的完整定义",
        "用自然语言完整表达{concept}的核心特征，要求直接陈述不要分段",
        "请将{concept}的定义浓缩成一句完整的话，不要使用列表格式",
        "以陈述句形式完整描述{concept}的核心性质，禁止使用引导语"
    ]
    
    # 创建所有概念列表
    all_concepts = []
    for category in ADVANCED_KNOWLEDGE_BASE.values():
        all_concepts.extend(category)
    
    # 确保有足够的唯一概念
    if len(all_concepts) < num_records:
        # 添加概念变体
        concepts_with_variants = [f"{c}的定义" for c in all_concepts] 
        concepts_with_variants += [f"{c}的特点" for c in all_concepts]
        concepts_with_variants += [f"什么是{c}" for c in all_concepts]
        all_concepts = concepts_with_variants
    
    # 生成提示词（确保3000条不重复）
    selected_concepts = random.sample(all_concepts, min(num_records, len(all_concepts)))
    
    prompts = []
    for concept in selected_concepts:
        template = random.choice(prompt_templates)
        prompts.append(template.format(concept=concept))
    
    # 如果还需要更多提示词，补充随机组合
    if len(prompts) < num_records:
        extra_needed = num_records - len(prompts)
        for _ in range(extra_needed):
            random_concept = random.choice(all_concepts)
            random_template = random.choice(prompt_templates)
            prompts.append(random_template.format(concept=random_concept))
    
    return prompts

# ====================== 验证响应有效性 ============================
def is_valid_response(text):
    """验证响应是否符合要求，用于知识图谱构建"""
    if not text or len(text) < 5: 
        return False
    if text.endswith(('：', ':')): 
        return False
    # 检测无效模式
    invalid_patterns = [
        r"如下[:：]", 
        r"以下[^，。]*[:：]",
        r"具有以下.*特点[:：]",
        r"主要[性质|作用].*[:：]",
        r"最显著的.*[:：]",
        r"特点如下",
        r"性质如下",
        r"作用如下"
    ]
    if any(re.search(pattern, text) for pattern in invalid_patterns):
        return False
    return True

# ====================== 强化API调用函数 ==========================
def call_api_with_retry(prompt):
    """带重试机制的API调用，增加有效性检查"""
    client = create_client()
    attempts = 0
    last_error = None
    
    while attempts < Config.RETRY_COUNT:
        try:
            time.sleep(Config.DELAY_BETWEEN_REQUESTS)  # 避免速率限制
            
            response = client.chat.completions.create(
                model=Config.MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "你是严谨的数据结构专家。请直接用完整陈述句回答，禁止使用'如下'、'以下'等引导词，不要分段或列表"
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=40  # 更严格的token限制
            )
            
            content = response.choices[0].message.content.strip()
            # 清理并标准化响应
            content = content.split('\n')[0].replace('"', '').replace('``', '').strip()
            if content.endswith('。'):
                content = content[:-1]
                
            # 验证响应有效性
            if not is_valid_response(content):
                logging.warning(f"无效响应: {content} (来自提示: {prompt})")
                return None  # 标记为无效
                
            return content
            
        except Exception as e:
            last_error = str(e)
            if "Rate limit" in last_error:
                # 遇到限流时增加延迟
                time.sleep(2 ** attempts)  # 指数退避
            attempts += 1
    
    logging.warning(f"API调用失败: {prompt} - {last_error}")
    return f"[错误] 无法获取响应: {last_error}"

# ====================== 高性能批处理函数 ========================
def process_large_batch(prompts):
    """优化的大型批处理函数，处理无效响应"""
    results = []
    failed_count = 0
    invalid_count = 0  # 跟踪无效响应数量
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=Config.CONCURRENCY) as executor:
        # 准备任务
        future_to_prompt = {
            executor.submit(call_api_with_retry, prompt): prompt 
            for prompt in prompts
        }
        
        # 处理结果带进度条
        completed = tqdm(
            concurrent.futures.as_completed(future_to_prompt),
            total=len(prompts),
            desc="生成知识单句"
        )
        
        for future in completed:
            try:
                result = future.result()
                
                # 处理无效响应
                if result is None:
                    invalid_count += 1
                    completed.set_postfix({"无效": invalid_count, "失败": failed_count})
                    continue
                
                # 处理错误响应
                if "[错误]" in result:
                    failed_count += 1
                    completed.set_postfix({"失败": failed_count, "无效": invalid_count})
                    continue
                
                # 有效响应
                results.append(result)
                
            except Exception as e:
                logging.error(f"任务处理异常: {str(e)}")
                failed_count += 1
                completed.set_postfix({"失败": failed_count, "无效": invalid_count})
    
    total_attempts = len(prompts)
    valid_count = len(results)
    error_rate = (failed_count / total_attempts) * 100
    invalid_rate = (invalid_count / total_attempts) * 100
    success_rate = (valid_count / total_attempts) * 100
    
    print(f"\n✅ 完成: {valid_count} 条有效 | {invalid_count} 条无效 | {failed_count} 条失败")
    print(f"📊 成功率: {success_rate:.1f}% | 无效率: {invalid_rate:.1f}% | 错误率: {error_rate:.1f}%")
    return results

# ====================== 文件输出与备份 ==========================
def save_large_dataset(sentences, filename):
    """保存大型数据集并创建备份"""
    # 确保目录存在
    os.makedirs("data_backups", exist_ok=True)
    
    # 主文件
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(sentences))
    
    # 创建时间戳备份
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_file = f"data_backups/{timestamp}_{filename}"
    with open(backup_file, "w", encoding="utf-8") as f:
        f.write("\n".join(sentences))
    
    print(f"✅ 数据已保存到: {filename}")
    print(f"✅ 备份已创建: {backup_file}")
    
    # 生成统计数据
    unique_count = len(set(sentences))
    word_counts = [len(sentence.split()) for sentence in sentences]
    avg_words = sum(word_counts) / len(word_counts) if sentences else 0
    
    print(f"\n数据集统计:")
    print(f"- 总条目: {len(sentences)}")
    print(f"- 唯一条目: {unique_count}")
    print(f"- 平均长度: {avg_words:.1f} 词")
    print(f"- 最短: {min(word_counts) if word_counts else 0} 词 | 最长: {max(word_counts) if word_counts else 0} 词")
    
    return filename

# ====================== 主函数（强化版） ========================
def main():
    # 初始化日志
    logging.basicConfig(
        filename='knowledge_generator.log', 
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print(f"🚀🚀 知识单句生成任务 - 目标: {Config.NUM_RECORDS} 条")
    print("="*60)
    
    # 验证API密钥
    if not Config.API_KEY:
        print("\n❌❌ 错误: 请先设置环境变量 ARK_API_KEY")
        return
    
    # 阶段1: 生成高级提示词
    print("\n🔧🔧 创建高级提示词列表...")
    prompts = generate_advanced_prompts(Config.NUM_RECORDS)
    print(f"✅ 已生成 {len(prompts)} 个多样化的提示词")
    
    # 阶段2: 批量生成知识单句
    print("\n⚡⚡ 启动API批处理（这可能需要30-60分钟）...")
    print(f"- 并发请求: {Config.CONCURRENCY}")
    print(f"- 重试机制: {Config.RETRY_COUNT}次")
    print(f"- 请求延迟: {Config.DELAY_BETWEEN_REQUESTS*1000:.0f}ms")
    print(f"- 响应验证: 已启用严格有效性检查\n")
    
    sentences = process_large_batch(prompts)
    
    # 新增：补充缺失的有效数据
    if len(sentences) < Config.NUM_RECORDS:
        missing_count = Config.NUM_RECORDS - len(sentences)
        print(f"\n⚠️ 需要补充 {missing_count} 条有效数据...")
        
        # 创建新的提示词（避免重复）
        new_prompts = generate_advanced_prompts(missing_count + 10)  # 多生成一些以防无效响应
        new_sentences = process_large_batch(new_prompts)
        
        # 仅添加有效响应
        valid_new_sentences = [s for s in new_sentences if s is not None]
        sentences.extend(valid_new_sentences[:missing_count])
        
        # 确保不超出限制
        sentences = sentences[:Config.NUM_RECORDS]
    
    # 阶段3: 保存结果
    save_large_dataset(sentences, Config.OUTPUT_FILE)
    
    # 完成提示
    print("\n🎉🎉 任务成功完成! 知识单句已保存到文本文件")
    print(f"提示: 您可以使用这些数据进行后续的NLP处理或知识图谱构建")

if __name__ == "__main__":
    main()