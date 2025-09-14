# config.py
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# --- 已更改: 读取DeepSeek API密钥 ---
DEEPSEEK_API_KEY ="sk-fbf0cbed7c3e4a778a6aca7379791de4"
#DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


# --- 已更改: 配置DeepSeek的模型和API地址 ---
DEEPSEEK_MODEL_NAME = "deepseek-chat-light" # DeepSeek的对话模型
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1" # DeepSeek的API服务器地址

# NLU模型的路径保持不变
NLU_MODEL_PATH = "/root/KG/my_intent_model"