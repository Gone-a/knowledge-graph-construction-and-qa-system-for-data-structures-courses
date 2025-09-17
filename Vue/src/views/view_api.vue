<template>
  <div class="api-setting-page">
    <div class="api-setting-card">
      <h2 class="api-setting-title">API 设置</h2>
      <div class="setting-group">
        <div class="form-item">
          <label class="form-label">模型</label>
          <input
            type="text"
            v-model="apiSettings.model"
            placeholder="请输入模型名称"
            class="api-input"
          />
        </div>
        <div class="form-item">
          <label class="form-label">API Key</label>
          <input
            type="text"
            v-model="apiSettings.apiKey"
            placeholder="请输入API Key"
            class="api-input"
          />
        </div>
        <div class="form-item">
          <label class="form-label">Base URL</label>
          <input
            type="text"
            v-model="apiSettings.baseUrl"
            placeholder="请输入Base URL"
            class="api-input"
          />
        </div>
        <button
          @click="saveApiSettings"
          :disabled="!isApiSettingsValid"
          class="submit-btn"
        >
          保存API设置
        </button>
      </div>

      <h2 class="api-setting-title" style="margin-top: 30px;">数据库设置</h2>
      <div class="setting-group">
        <div class="form-item">
          <label class="form-label">Bolt URL</label>
          <input
            type="text"
            v-model="dbSettings.boltUrl"
            placeholder="请输入Bolt URL"
            class="api-input"
          />
        </div>
        <div class="form-item">
          <label class="form-label">用户名</label>
          <input
            type="text"
            v-model="dbSettings.username"
            placeholder="请输入用户名"
            class="api-input"
          />
        </div>
        <div class="form-item">
          <label class="form-label">密码</label>
          <input
            type="password"
            v-model="dbSettings.password"
            placeholder="请输入密码"
            class="api-input"
          />
        </div>
        <div class="form-item">
          <label class="form-label">Neo4j浏览器</label>
          <input
            type="text"
            v-model="dbSettings.browserUrl"
            placeholder="请输入Neo4j浏览器地址"
            class="api-input"
          />
        </div>
        <button
          @click="saveDbSettings"
          :disabled="!isDbSettingsValid"
          class="submit-btn"
        >
          保存数据库设置
        </button>
      </div>

      <p v-if="feedbackMsg" class="feedback-msg">{{ feedbackMsg }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import axios from 'axios';

// API设置数据
const apiSettings = ref({
  model: '',
  apiKey: '',
  baseUrl: ''
});

// 数据库设置数据
const dbSettings = ref({
  boltUrl: '',
  username: '',
  password: '',
  browserUrl: ''
});

const feedbackMsg = ref('');

// 验证API设置是否有效
const isApiSettingsValid = computed(() => {
  return apiSettings.value.model.trim() && 
         apiSettings.value.apiKey.trim() && 
         apiSettings.value.baseUrl.trim();
});

// 验证数据库设置是否有效
const isDbSettingsValid = computed(() => {
  return dbSettings.value.boltUrl.trim() && 
         dbSettings.value.username.trim() && 
         dbSettings.value.browserUrl.trim();
});

// 保存API设置
const saveApiSettings = async () => {
  feedbackMsg.value = '正在保存API设置...';
  console.log(apiSettings);

  try {
    const response = await axios.post('http://localhost:5000/set_api', {
      apiSettings: apiSettings.value
    });
    feedbackMsg.value = response.data || 'API设置保存成功';
  } catch (error) {
    feedbackMsg.value = 'API设置保存失败，请检查地址或网络';
    console.error('保存API设置失败：', error);
  }
};

// 保存数据库设置
const saveDbSettings = async () => {
  feedbackMsg.value = '正在保存数据库设置...';
  console.log(dbSettings);
  
  try {
    const response = await axios.post('http://localhost:5000/set_database', {
      dbSettings: dbSettings.value
    });
    feedbackMsg.value = response.data || '数据库设置保存成功';
  } catch (error) {
    feedbackMsg.value = '数据库设置保存失败，请检查地址或网络';
    console.error('保存数据库设置失败：', error);
  }
};
</script>

<style scoped>
.api-setting-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20px;
}

.api-setting-card {
  width: 500px;
  padding: 24px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.api-setting-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #333;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

.setting-group {
  margin-bottom: 20px;
}

.form-item {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  color: #606266;
}

.api-input {
  width: 100%;
  padding: 10px;
  margin-bottom: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
  font-size: 14px;
}

.submit-btn {
  width: 100%;
  padding: 10px;
  background-color: #409eff;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
  margin-top: 10px;
}

.submit-btn:hover {
  background-color: #66b1ff;
}

.submit-btn:disabled {
  background-color: #c0c4cc;
  cursor: not-allowed;
}

.feedback-msg {
  margin-top: 12px;
  font-size: 14px;
  color: #606266;
  text-align: center;
}
</style>