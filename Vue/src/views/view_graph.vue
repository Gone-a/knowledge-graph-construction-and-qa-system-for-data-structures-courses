<template>
  <div class="graph-container">
    <div ref="chartRef" class="chart-wrapper"></div>
    <div v-if="loading" class="loading">加载数据中...</div>
    <div v-if="error" class="error">错误: {{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import * as echarts from 'echarts';
import graphData from '@/data/graph.json';

const chartRef = ref(null);
const chart = ref(null);
const loading = ref(true);
const error = ref('');

const initChart = () => {
  try {
    if (!chartRef.value) {
      throw new Error("图表容器DOM不存在");
    }
    if (!graphData || !graphData.nodes || !graphData.links) {
      throw new Error("JSON数据格式错误，缺少nodes或links数组");
    }

    if (chart.value) {
      chart.value.dispose();
    }

    chart.value = echarts.init(chartRef.value);

    // 为节点添加默认样式，同时保留数据中的自定义样式
    const processedNodes = graphData.nodes.map(node => ({
      ...node,
      symbol: node.symbol || 'circle',
      itemStyle: {
        ...{
          color: '#42b983',
          borderWidth: 2,
          borderColor: '#fff',
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.3)'
        },
        ...node.itemStyle
      },
      emphasis: {
        scale: true,
        itemStyle: {
          shadowBlur: 20,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }));

    // 为连线添加默认样式，同时保留数据中的自定义样式
    const processedLinks = graphData.links.map(link => ({
      ...link,
      lineStyle: {
        ...{
          width: 2,
          curveness: 0.2,
          color: '#999',
          type: 'solid'
        },
        ...link.lineStyle
      },
      label: {
        ...{
          show: true,
          fontSize: 12,
          color: '#333',
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          padding: [3, 6],
          borderRadius: 3
        },
        ...link.label
      },
      emphasis: {
        lineStyle: {
          width: 4,
          color: '#333'
        }
      }
    }));

    const option = {
      backgroundColor: '#f5f7fa',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        borderColor: '#ddd',
        borderWidth: 1,
        padding: 10,
        formatter: (params) => {
          if (params.dataType === 'node') {
            return `<div style="font-weight: bold; color: #333;">${params.name}</div>`;
          } else if (params.dataType === 'edge') {
            return `<div style="color: #666;">${params.sourceName} → ${params.targetName}</div>
                    <div style="color: #333;">${params.data.label?.formatter || '关联'}</div>`;
          }
          return '';
        }
      },
      series: [
        {
          type: 'graph',
          layout: 'force',
          roam: true,
          // 开启缩放和平移动画
          scaleLimit: {
            min: 0.5,
            max: 3
          },
          // 节点文字样式
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
            color: '#fff',
            shadowBlur: 2,
            shadowColor: '#000',
            position: 'inside'
          },
          // 节点数据
          data: processedNodes,
          // 连线数据
          links: processedLinks,
          // 力导向布局参数优化
          force: {
            repulsion: 2000,      // 节点之间的排斥力
            edgeLength: 500,     // 连线长度
            gravity: 0.05,       // 重力，影响整体布局向中心聚集的程度
            layoutAnimation: true, // 布局动画
            edgeSymbol: ['none', 'arrow'], // 连线两端的标记
            edgeSymbolSize: [4, 10] // 连线两端标记的大小
          },
          // 动画效果
          animationDuration: 1500,
          animationEasingUpdate: 'quinticInOut',
          // 鼠标悬停交互
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 5
            }
          }
        }
      ]
    };

    chart.value.setOption(option);
    loading.value = false;

    const handleResize = () => {
      chart.value?.resize();
    };
    window.addEventListener('resize', handleResize);
    onUnmounted(() => {
      window.removeEventListener('resize', handleResize);
    });
  } catch (err) {
    error.value = err.message;
    loading.value = false;
    console.error("图表初始化失败：", err);
  }
};

// 监听窗口大小变化，优化响应式
watch(
  () => [window.innerWidth, window.innerHeight],
  () => {
    chart.value?.resize();
  },
  { immediate: false, deep: true }
);

onMounted(() => {
  // 确保DOM渲染完成后初始化图表
  setTimeout(initChart, 0);
});

onUnmounted(() => {
  if (chart.value) {
    chart.value.dispose();
    chart.value = null;
  }
});
</script>

<style scoped>
.graph-container {
  position: relative;
  width: 100%;
  height: 80vh;
  padding: 20px;
  box-sizing: border-box;
}

.chart-wrapper {
  width: 100%;
  height: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  background-color: #f5f7fa;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.loading, .error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
  z-index: 10;
  transition: all 0.3s ease;
}

.loading {
  background-color: rgba(255, 255, 255, 0.95);
  color: #1976d2;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}

.error {
  background-color: rgba(244, 67, 54, 0.95);
  color: #fff;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}
</style>