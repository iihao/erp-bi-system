<template>
  <div ref="chartRef" class="bar-chart" :style="{ height: height }"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  categoryKey: {
    type: String,
    default: 'category'
  },
  valueKey: {
    type: String,
    default: 'value'
  },
  nameKey: {
    type: String,
    default: 'name'
  },
  horizontal: {
    type: Boolean,
    default: false
  },
  height: {
    type: String,
    default: '350px'
  },
  title: {
    type: String,
    default: ''
  },
  color: {
    type: String,
    default: '#409EFF'
  },
  showLabel: {
    type: Boolean,
    default: true
  },
  labelFormatter: {
    type: Function,
    default: null
  }
})

const chartRef = ref(null)
let chart = null

const initChart = () => {
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = () => {
  if (!chart) return

  const categories = props.data.map(item => item[props.nameKey] || item[props.categoryKey])
  const values = props.data.map(item => item[props.valueKey])

  const reversedCategories = props.horizontal ? [...categories].reverse() : categories
  const reversedValues = props.horizontal ? [...values].reverse() : values

  // 商务配色方案 - 深蓝色渐变
  const primaryColor = props.color || '#2c5282'
  let gradientColor = primaryColor

  if (typeof props.color === 'string' && props.color.startsWith('#')) {
    gradientColor = new echarts.graphic.LinearGradient(
      props.horizontal ? 0 : 0,
      props.horizontal ? 0 : 0,
      props.horizontal ? 1 : 0,
      props.horizontal ? 0 : 1,
      [
        { offset: 0, color: primaryColor },
        { offset: 1, color: lightenColor(primaryColor, 20) }
      ]
    )
  }

  const option = {
    title: props.title ? {
      text: props.title,
      left: 'center',
      textStyle: {
        color: '#1a202c',
        fontSize: 14,
        fontWeight: 600
      }
    } : null,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: {
        color: '#1a202c'
      }
    },
    grid: {
      left: '3%',
      right: props.horizontal ? '15%' : '4%',
      bottom: '3%',
      top: props.title ? '20%' : '10%',
      containLabel: true
    },
    xAxis: props.horizontal ? {
      type: 'value',
      axisLabel: {
        formatter: props.labelFormatter,
        color: '#4a5568'
      },
      splitLine: {
        lineStyle: {
          color: '#f7fafc',
          type: 'dashed'
        }
      },
      axisLine: {
        lineStyle: {
          color: '#e2e8f0'
        }
      }
    } : {
      type: 'category',
      data: categories,
      axisLabel: {
        rotate: 45,
        color: '#4a5568'
      },
      axisLine: {
        lineStyle: {
          color: '#e2e8f0'
        }
      }
    },
    yAxis: props.horizontal ? {
      type: 'category',
      data: reversedCategories,
      axisLabel: {
        interval: 0,
        fontSize: 12,
        color: '#4a5568'
      },
      axisLine: {
        lineStyle: {
          color: '#e2e8f0'
        }
      }
    } : {
      type: 'value',
      axisLabel: {
        formatter: props.labelFormatter,
        color: '#4a5568'
      },
      splitLine: {
        lineStyle: {
          color: '#f7fafc',
          type: 'dashed'
        }
      },
      axisLine: {
        lineStyle: {
          color: '#e2e8f0'
        }
      }
    },
    series: [{
      name: '数值',
      type: 'bar',
      data: props.horizontal ? reversedValues : values,
      barWidth: '60%',
      itemStyle: {
        color: gradientColor,
        borderRadius: props.horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]
      },
      label: {
        show: props.showLabel,
        position: props.horizontal ? 'right' : 'top',
        formatter: props.labelFormatter,
        fontSize: 12,
        color: '#4a5568'
      }
    }]
  }

  chart.setOption(option)
}

// 颜色变亮辅助函数
const lightenColor = (color, percent) => {
  const num = parseInt(color.replace('#', ''), 16)
  const amt = Math.round(2.55 * percent)
  const R = Math.min(255, (num >> 16) + amt)
  const G = Math.min(255, ((num >> 8) & 0x00FF) + amt)
  const B = Math.min(255, (num & 0x0000FF) + amt)
  return `#${(0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1)}`
}

const resize = () => {
  chart?.resize()
}

const dispose = () => {
  chart?.dispose()
  chart = null
}

defineExpose({ resize, dispose, updateChart })

watch(() => props.data, () => {
  updateChart()
}, { deep: true })

onMounted(() => {
  initChart()
})

onBeforeUnmount(() => {
  dispose()
})
</script>

<style scoped>
.bar-chart {
  width: 100%;
}
</style>
