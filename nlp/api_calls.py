import time
import json
import openai
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RAG.query_fixed import DSAGraphQAFixed

# --- 已更改: 从config导入DeepSeek的配置 ---
from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL_NAME, DEEPSEEK_BASE_URL

# 设置OpenAI客户端
client = openai.OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)
# Meta-Prompt: AI 助手核心指令
# 这是一个多行字符串，包含了对AI的详细指示

SYSTEM_PROMPT = """
# 1. 你的身份 (Your Identity)
你是一个世界级的数据结构与算法专家，你的名字叫“代码导师”(Code Mentor)。你非常耐心，善于将复杂、抽象的概念用清晰、易于理解的语言解释给初学者听。你的目标是成为用户最信赖的学习伙伴。

# 2. 你的核心任务 (Your Core Mission)
你的唯一任务是，严格利用下面`### 背景知识`部分提供的信息，来精准地回答`### 当前用户问题`。你就像一个专业的数据库查询员，只依据给定的事实进行阐述和组织，而不是一个自由发挥的创作者。

# 3. 行为准则 (Rules of Engagement)

    a. **绝对优先原则 - 严格基于背景知识**: 
       - 你的回答必须，也只能，基于`### 背景知识`部分提供的数据。
       - 如果背景知识足以回答问题，请用自然流畅的语言组织它，并可以适当举例说明。
       - 如果背景知识显示为“无”、“未找到”或包含错误信息，你必须明确告知用户“根据我现有的知识库，我暂时无法找到关于您问题的确切信息”，然后可以礼貌地建议用户换个问法。
       - **绝对禁止**在背景知识之外编造、猜测或使用你自己内部的知识来回答专业问题。

    b. **处理跑题问题**:
       - 当用户的问题明显与数据结构、算法或计算机科学无关时（例如询问天气、新闻、讲笑话），你必须礼貌地拒绝，并温和地将对话引导回主题。
       - 示例回答: “抱歉，我的专业领域是数据结构与算法。关于天气问题我不太了解。不过，我们可以继续讨论一下例如‘图’或者‘排序算法’，您对哪个感兴趣呢？”

    c. **处理模糊问题**:
       - 如果用户的提问很模糊（例如只说“树”），你应该主动提出澄清性问题来帮助用户明确需求。
       - 示例回答: “当然可以聊‘树’！为了更好地帮助您，您是想了解树的基本定义，还是对二叉树、平衡二叉树等具体类型感兴趣，或者是想知道树的遍历算法呢？”

    d. **语气与风格**:
       - 保持专业、严谨、耐心、友好的语气。
       - 避免使用过于随意或口语化的词汇。
       - 多使用鼓励性的语言。

# 4. 输出格式 (Output Format)
- 对于定义或概念解释，力求简洁明了。
- 当需要列举多个项目时（例如多种排序算法），请使用项目符号列表（Markdown的 `-` 或 `*`）。
- 如果需要展示代码或伪代码，请务必使用Markdown的代码块（```）格式化，以保证清晰可读。
"""
def call_deepseek_api(history: list, prompt_addition: str) -> str:
    """
    真实调用DeepSeek的API。
    history: 对话历史，格式为 [{"role": "user", "content": "..."}, ...]
    prompt_addition: 本轮根据知识库检索到的附加信息
    """
    system_message = {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
    
    messages = [system_message] + history
    last_user_message = messages[-1]["content"]
    prompt_with_knowledge = f"""
### 用户问题:
{last_user_message}

### 背景知识 (来自知识图谱API的查询结果):
{prompt_addition}
"""
    messages[-1]["content"] = prompt_with_knowledge

    print("\n" + "="*20 + " 发送给 DeepSeek 的消息 " + "="*20)
    print(messages)
    print("="*65 + "\n")

    try:
        print("【AI正在生成回答...】")
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL_NAME, # <-- 使用DeepSeek的模型
            messages=messages,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"调用DeepSeek API时出错: {e}")
        return "抱歉，我在连接AI服务时遇到了问题，请稍后再试。"

def call_kg_api_for_segment(point1: str, point2: str,qa_system: DSAGraphQAFixed) -> dict:
    """
    TODO: 替换此处的模拟逻辑为您真实的Neo4j查询。
    """
    print(f"【知识库调用】: 正在查询 {point1} 和 {point2} 之间的线段...")
    time.sleep(0.5)
    result = qa_system.find_relation_by_entities([point1, point2])
    print(f"实体和实体查询:{result}")
    return result


def call_kg_api_for_point(segment: str, point: str,qa_system: DSAGraphQAFixed) -> dict:
    """
    TODO: 替换此处的模拟逻辑为您真实的Neo4j查询。
    """
    print(f"【知识库调用】: 正在查询线段 {segment} 上除 {point} 外的另一个端点...")
    time.sleep(0.5)
    result = qa_system.find_entities_by_relation([segment], point)
    print(f"实体和关系查询:{result}")
    return result