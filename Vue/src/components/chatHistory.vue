<template>
  <div class="chat-history-container">
    <div class="history-header">
      <h3>对话历史</h3>
      <button class="new-chat-btn" @click="createNewChat">
        <i class="fas fa-plus"></i> 新建对话
      </button>
    </div>
    
    <div class="history-list">
      <div 
        v-for="(chat, index) in chatHistories" 
        :key="index"
        :class="['history-item', { 'active': currentChatIndex === index }]"
        @click="switchChat(index)"
      >
        <div class="history-preview">
          {{ chat.messages.length > 0 ? chat.messages[0].text.substring(0, 20) + '...' : '新对话' }}
        </div>
        <button class="delete-btn" @click.stop="deleteChat(index)">
          <i class="fas fa-trash"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, defineEmits } from 'vue';

// 定义事件
const emit = defineEmits(['chatSwitched', 'newChatCreated']);

// 初始化对话历史
const chatHistories = ref([
  {
    id: Date.now(),
    messages: []
  }
]);
const currentChatIndex = ref(0);

// 创建新对话
const createNewChat = () => {
  chatHistories.value.push({
    id: Date.now(),
    messages: []
  });
  currentChatIndex.value = chatHistories.value.length - 1;
  emit('newChatCreated', chatHistories.value[currentChatIndex.value].messages);
};

// 切换对话
const switchChat = (index) => {
  currentChatIndex.value = index;
  emit('chatSwitched', chatHistories.value[index].messages);
};

// 删除对话
const deleteChat = (index) => {
  if (chatHistories.value.length <= 1) {
    // 至少保留一个对话
    chatHistories.value[index].messages = [];
    emit('chatSwitched', []);
    return;
  }
  
  chatHistories.value.splice(index, 1);
  
  // 如果删除的是当前对话，切换到第一个对话
  if (currentChatIndex.value === index) {
    currentChatIndex.value = 0;
    emit('chatSwitched', chatHistories.value[0].messages);
  } else if (currentChatIndex.value > index) {
    // 如果删除的是当前对话之前的对话，调整索引
    currentChatIndex.value--;
  }
};

// 监听当前对话消息变化
watch(
  () => chatHistories.value[currentChatIndex.value].messages,
  () => {
    // 可以在这里添加本地存储逻辑，如果需要的话
  },
  { deep: true }
);

// 提供添加消息到当前对话的方法
const addMessageToCurrentChat = (message) => {
  chatHistories.value[currentChatIndex.value].messages.push(message);
};

// 暴露方法给父组件
/* global defineExpose */
defineExpose({
  addMessageToCurrentChat
});
</script>

<style scoped>
.chat-history-container {
  width: 280px;
  border-right: 1px solid #eee;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.history-header {
  padding: 16px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.new-chat-btn {
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 6px 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 14px;
}

.new-chat-btn:hover {
  background-color: #66b1ff;
}

.history-list {
  flex: 1;
  overflow-y: auto;
}

.history-item {
  padding: 12px 16px;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background-color 0.2s;
}

.history-item:hover {
  background-color: #f9f9f9;
}

.history-item.active {
  background-color: #e6f7ff;
  border-left: 3px solid #409eff;
}

.history-preview {
  font-size: 14px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  margin-right: 10px;
}

.delete-btn {
  background: transparent;
  border: none;
  color: #999;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;
}

.history-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: #f56c6c;
}
</style>