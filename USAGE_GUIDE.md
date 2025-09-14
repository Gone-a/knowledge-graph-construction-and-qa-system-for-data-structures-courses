# 智能知识图谱问答系统 v2.0 使用指南

## 系统概述

本系统是一个基于知识图谱的智能问答系统，采用模块化架构设计，提供高性能的自然语言理解和知识检索功能。

## 系统架构

```
KG_inde/
├── main.py                 # 主程序入口
├── modules/                 # 核心模块
│   ├── intent_recognition.py    # 意图识别模块
│   ├── knowledge_graph.py       # 知识图谱查询模块
│   ├── backend_api.py          # 后端API模块
│   └── config_manager.py       # 配置管理模块
├── frontend/               # 前端界面
│   ├── src/
│   │   ├── App.vue             # 主应用组件
│   │   ├── components/         # Vue组件
│   │   └── main.js             # 前端入口
│   ├── package.json            # 前端依赖
│   └── vite.config.js          # 构建配置
├── my_intent_model/        # NLU模型文件
├── requirements.txt        # Python依赖
└── README.md              # 项目说明
```

## 快速启动

### 1. 环境准备

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
```

### 2. 配置数据库

确保Neo4j数据库运行在 `bolt://localhost:7687`，并设置环境变量：

```bash
export NEO4J_KEY="your_neo4j_password"
```

### 3. 启动系统

```bash
# 启动后端服务
python main.py

# 启动前端服务（新终端）
cd frontend
npm run dev
```

### 4. 访问系统

前端服务：http://localhost:8080/
后端API：http://localhost:5000/
- API文档: http://localhost:5000/api/health

## API接口说明

### 健康检查
```
GET /api/health
```

### 问答接口
```
POST /api/chat
Content-Type: application/json

{
  "message": "用户问题",
  "history": []
}
```

响应格式：
```json
{
  "response": "系统回答",
  "intent": "识别的意图",
  "entities": ["提取的实体"],
  "confidence": 0.95,
  "timestamp": "2025-01-11T13:48:41"
}
```

## 核心模块说明

### 1. 意图识别模块 (intent_recognition.py)

- **功能**: 使用BERT模型进行意图分类和实体提取
- **模型路径**: `./my_intent_model/`
- **支持意图**: 查询、比较、定义等

### 2. 知识图谱查询模块 (knowledge_graph.py)

- **功能**: 基于Neo4j的知识检索
- **主要方法**:
  - `find_entity_relations()`: 查找实体关系
  - `find_entities_by_relation()`: 根据关系查找实体
  - `find_relation_by_entities()`: 查找实体间关系

### 3. 后端API模块 (backend_api.py)

- **功能**: 提供RESTful API接口
- **特性**: CORS支持、错误处理、日志记录

### 4. 配置管理模块 (config_manager.py)

- **功能**: 统一管理系统配置
- **配置项**: 数据库连接、模型路径、API设置

## 前端组件说明

### 主要组件

- **App.vue**: 主应用组件，包含聊天界面和侧边栏
- **OptimizedChatBox**: 优化的聊天组件，支持实时对话

### 主要特性

- 响应式设计，支持移动端
- 实时消息传输
- 图片和文件上传支持
- 全屏查看模式
- 加载动画和错误处理

## 性能优化

### 后端优化

- 连接池管理
- 缓存机制
- 异步处理
- 错误重试

### 前端优化

- 组件懒加载
- 虚拟滚动
- 图片压缩
- 代码分割

## 开发指南

### 添加新意图

1. 在 `intent_recognition.py` 中添加意图处理逻辑
2. 更新模型标签映射
3. 在 `knowledge_graph.py` 中添加对应查询方法

### 扩展API接口

1. 在 `backend_api.py` 中添加新路由
2. 实现对应的处理函数
3. 更新前端调用逻辑

### 自定义前端组件

1. 在 `frontend/src/components/` 中创建新组件
2. 在 `App.vue` 中引入和使用
3. 更新样式和交互逻辑

## 故障排除

### 常见问题

1. **Neo4j连接失败**
   - 检查数据库是否启动
   - 验证连接参数和密码

2. **模型加载失败**
   - 确认模型文件完整性
   - 检查路径配置

3. **前端启动失败**
   - 检查Node.js版本 (>=16.0.0)
   - 重新安装依赖: `rm -rf node_modules && npm install`

### 日志查看

- 后端日志: 控制台输出
- 前端日志: 浏览器开发者工具
- 系统状态: http://localhost:5000/api/health

## 部署说明

### 生产环境部署

1. 使用生产级WSGI服务器 (如Gunicorn)
2. 配置反向代理 (如Nginx)
3. 设置环境变量和安全配置
4. 构建前端生产版本: `npm run build`

### Docker部署

```dockerfile
# 后端Dockerfile示例
FROM python:3.8-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "main.py"]
```

## 技术栈

- **后端**: Python, Flask, Neo4j, Transformers
- **前端**: Vue.js 3, Vite, Axios
- **数据库**: Neo4j图数据库
- **机器学习**: BERT, PyTorch

## 版本信息

- 当前版本: v2.0
- 更新日期: 2025-01-11
- 兼容性: Python 3.8+, Node.js 16+

---

如有问题，请查看项目README.md或联系开发团队。