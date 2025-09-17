<template>
  <div class="nav-container">
    <!-- 导航栏主体 -->
    <nav class="navbar">
      <!-- 导航标题（可选，增加品牌感） -->
      <div class="nav-title">
        <span class="title-text">KG</span>
      </div>

      <!-- 导航链接区域 -->
      <div class="nav-links">
        <!-- 首页导航（活跃状态有蓝色下划线） -->
        <router-link
          to="/"
          class="nav-link"
          :class="{ 'active': $route.path === '/' }"
          exact
        >
          <i class="icon-home"></i>
          <span class="link-text">首页</span>
        </router-link>

        <!-- 图页面导航 -->
        <router-link
          to="/graph"
          class="nav-link"
          :class="{ 'active': $route.path === '/graph' }"
          exact
        >
          <i class="icon-graph"></i>
          <span class="link-text">图</span>
        </router-link>

        <router-link
          to="/api"
          class="nav-link"
          :class="{ 'active': $route.path === '/api' }"
          exact
        >
          <i class="icon-api"></i>
          <span class="link-text">设置</span>
        </router-link>
      </div>
    </nav>

    <!-- 路由内容显示区域（增加过渡动画） -->
    <transition name="page-fade">
      <router-view class="content-container"></router-view>
    </transition>
  </div>
</template>

<style scoped>
/* 全局容器样式 */
.nav-container {
  width: 100%;
  min-height: 100vh;
  background-color: #f8fafc; /* 淡蓝色背景，与导航栏呼应 */
}

/* 导航栏样式：渐变蓝色背景 + 阴影 */
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2rem;
  height: 60px;
  background: linear-gradient(135deg, #1e40af, #3b82f6); /* 蓝色渐变 */
  box-shadow: 0 2px 8px rgba(30, 64, 175, 0.15); /* 淡蓝色阴影 */
  color: white;
  position: sticky;
  top: 0;
  z-index: 100; /* 确保导航栏在最上层 */
}

/* 导航标题样式 */
.nav-title {
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.title-text {
  background: linear-gradient(120deg, #bfdbfe, #f0f9ff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

/* 导航链接容器 */
.nav-links {
  display: flex;
  gap: 2rem; /* 链接之间的间距 */
}

/* 导航链接基础样式 */
.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem; /* 图标与文字间距 */
  padding: 0.5rem 0;
  color: #e0e7ff; /* 淡蓝色文字（未活跃） */
  font-size: 0.95rem;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.3s ease;
  position: relative;
}

/* 导航链接hover效果 */
.nav-link:hover {
  color: white;
  transform: translateY(-2px); /* 轻微上移，增加交互感 */
}

/* 活跃链接样式（下划线 + 文字变白） */
.nav-link.active {
  color: white;
}

.nav-link.active::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #bfdbfe; /* 淡蓝色下划线 */
  border-radius: 1px;
}

/* 图标样式（使用CSS模拟简单图标，也可替换为Font Awesome） */
.icon-home::before {
  content: "🏠";
  font-size: 1.1rem;
}

.icon-graph::before {
  content: "📊";
  font-size: 1.1rem;
}

.icon-api::before {
  content: "ℹ️";
  font-size: 1.1rem;
}

/* 内容区域样式 */
.content-container {
  width: 100%;
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 1rem;
}

/* 页面切换过渡动画 */
.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.page-fade-enter-active,
.page-fade-leave-active {
  transition: all 0.3s ease;
}

/* 响应式适配：小屏幕下导航链接居中 */
@media (max-width: 768px) {
  .navbar {
    flex-direction: column;
    height: auto;
    padding: 1rem;
  }

  .nav-links {
    margin-top: 1rem;
    gap: 1.5rem;
  }
}
</style>