import { createRouter, createWebHistory } from 'vue-router'
// 导入页面组件
import home from '../views/view_home.vue'
import graph from '../views/view_graph.vue'
import api from '../views/view_api.vue'

const routes = [
  {
    path: '/',        // 路由路径
    name: 'home',     // 路由名称（可选）
    component: home   // 对应的页面组件
  },
  {
    path: '/graph',
    name: 'graph',
    component: graph
  },
  {
    path:'/api',
    name:'api',
    component:api
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),  // 使用 HTML5 history 模式（无 # 号）
  routes
})

export default router