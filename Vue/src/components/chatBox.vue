<template>
  <div class="chat-page-wrapper">
    <!-- 聊天容器：居中显示 -->
    <div class="ai-chat-container">
      <!-- 页面标题区域 -->
      <header class="chat-header">
        <div class="logo">
          <i class="fas fa-robot"></i>
          <h1>Chat-kg</h1>
        </div>
      </header>

      <!-- 消息列表（使用 props 传入的 messages） -->
      <main class="chat-messages">
        <div v-if="messages.length === 0" class="welcome-message">
          <p>👋 你好！有什么可以帮助你的吗？</p>
        </div>
        <div 
          v-for="(message, index) in messages" 
          :key="index" 
          :class="['message', message.sender]"
        >
          <div class="message-avatar">
            <i v-if="message.sender === 'ai'" class="fas fa-robot"></i>
            <i v-if="message.sender === 'user'" class="fas fa-user"></i>
          </div>
          <div class="message-content">
            <pre>{{ message.text }}</pre>
            <span class="message-time">{{ message.timestamp }}</span>
          </div>
        </div>

        <!-- 加载状态指示器 -->
        <div v-if="isLoading" class="message ai">
          <div class="message-avatar">
            <i class="fas fa-robot"></i>
          </div>
          <div class="message-content typing-indicator">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>
      </main>

      <!-- 输入区域 -->
      <footer class="chat-input-area">
        <form @submit.prevent="sendMessage" class="input-form">
          <textarea
            v-model="userInput"
            placeholder="输入你的消息..."
            class="message-input"
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.enter.shift="handleShiftEnter"
            :disabled="isLoading"
          ></textarea>
          <button 
            type="submit" 
            class="send-btn"
            :disabled="!userInput.trim() || isLoading"
          >
            <i class="fas fa-paper-plane"></i>
          </button>
        </form>
        <p class="input-hint">按 Enter 发送消息，Shift+Enter 换行</p>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, defineEmits, defineProps} from 'vue';
import axios from 'axios';

// 接收父组件传入的当前对话消息列表
const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  }
});
const emit = defineEmits(['messageAdded', 'clearChat']);
const userInput = ref('');
const messages = ref([...props.messages]);
const isLoading = ref(false);

// 发送消息函数
const sendMessage = () => {
  const messageText = userInput.value.trim();
  
  if (!messageText) return;
  
  // 用户消息添加到列表
  const userMessage = {
    sender: 'user',
    text: messageText,
    timestamp: getCurrentTime()
  };
  emit('messageAdded', userMessage);
  userInput.value = '';

  // 请求AI接口
  isLoading.value = true; // 新增：加载状态显示
  const userString = { message: userMessage.text }; // 无需reactive，普通对象即可

  axios.post("http://localhost:5000/reply", userString)
    .then(response => {
      const aiMessage = {
        sender: 'ai',
        text: response.data.message,
        timestamp: getCurrentTime()
      };
      // 触发消息添加事件
      emit('messageAdded', aiMessage);
      //发送 graph 数据
      
    })
    .catch(error => {
      console.error("请求出错：", error);
      const errorMessage = {
        sender: 'system',
        text: '请求AI回复失败，请稍后再试',
        timestamp: getCurrentTime()
      };
      // 触发消息添加事件
      emit('messageAdded', errorMessage);
    })
    .finally(() => {
      isLoading.value = false; // 新增：无论成功失败，关闭加载状态
    });
};

// 处理Shift+Enter换行（原有逻辑不变）
const handleShiftEnter = () => {
  userInput.value += "\n";
};

// 获取当前时间（格式化，原有逻辑不变）
const getCurrentTime = () => {
  const now = new Date();
  return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

// 监听消息变化，自动滚动到底部（原有逻辑不变）
watch(messages, () => {
  scrollToBottom();
});

watch(
  () => props.messages,
  (newMessages) => {
    messages.value = [...newMessages];
  },
  { deep: true } // 监听数组内部变化
);
// 滚动到最新消息（原有逻辑不变）
const scrollToBottom = () => {
  setTimeout(() => {
    const chatContainer = document.querySelector('.chat-messages');
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }, 0);
};
</script>

<style scoped>
.chat-page-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  background-color: #f8fafc;
  padding: 20px;
  box-sizing: border-box;
}

.ai-chat-container {
  width: 100%;
  max-width: 800px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

/* 头部样式 */
.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid #1248f9;
  background-color: #498ef0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo i {
  color: #f7f8f9;
  font-size: 20px;
}

.logo h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #f9f9f9;
}

/* 消息列表样式 */
.chat-messages {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome-message {
  margin: auto;
  text-align: center;
  color: #64748b;
  font-size: 16px;
  padding: 20px;
}

/* 消息项样式 */
.message {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.ai {
  align-self: flex-start;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message.ai .message-avatar {
  background-color: #eff6ff;
  color: #3b82f6;
}

.message.user .message-avatar {
  background-color: #f1f5f9;
  color: #64748b;
}

.message-content {
  padding: 12px 16px;
  border-radius: 16px;
  position: relative;
}

.message.ai .message-content {
  background-color: #f1f5f9;
  color: #1e293b;
  border-top-left-radius: 4px;
}

.message.user .message-content {
  background-color: #3b82f6;
  color: white;
  border-top-right-radius: 4px;
}

.message-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
}

.message-time {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  opacity: 0.7;
  text-align: right;
}

/* 加载状态指示器 */
.typing-indicator {
  display: flex;
  gap: 6px;
  padding: 10px 16px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #94a3b8;
  animation: typing 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0% {
    transform: scale(0);
  }
  50% {
    transform: scale(1);
  }
  100% {
    transform: scale(0);
  }
}

/* 输入区域样式 */
.chat-input-area {
  padding: 16px 24px;
  border-top: 1px solid #e2e8f0;
  background-color: #f8fafc;
}

.input-form {
  display: flex;
  gap: 12px;
}

.message-input {
  flex: 1;
  min-height: 60px;
  max-height: 180px;
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  resize: vertical;
  font-size: 14px;
  line-height: 1.5;
  outline: none;
  transition: border-color 0.2s;
}

.message-input:focus {
  border-color: #3b82f6;
}

.send-btn {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background-color: #3b82f6;
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.2s;
  flex-shrink: 0;
}

.send-btn:hover {
  background-color: #2563eb;
}

.send-btn:disabled {
  background-color: #94a3b8;
  cursor: not-allowed;
}

.input-hint {
  margin: 8px 0 0 0;
  font-size: 12px;
  color: #94a3b8;
  text-align: left;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .chat-page-wrapper {
    padding: 10px;
  }

  .ai-chat-container {
    border-radius: 8px;
  }

  .chat-messages {
    padding: 16px;
  }

  .message {
    max-width: 90%;
  }

  .chat-input-area {
    padding: 12px 16px;
  }
}
</style>