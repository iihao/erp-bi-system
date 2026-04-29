<template>
  <div ref="chartRef" class="pie-chart" :style="{ height: height }"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  nameKey: {
    type: String,
    default: 'name'
  },
  valueKey: {
    type: String,
    default: 'value'
  },
  height: {
    type: String,
    default: '350px'
  },
  title: {
    type: String,
    default: ''
  },
  showLegend: {
    type: Boolean,
    default: true
  },
  legendPosition: {
    type: String,
    default: 'right',
    validator: v => ['right', 'left', 'top', 'bottom'].includes(v)
  },
  radius: {
    type: Array,
    default: () => ['40%', '70%']
  },
  colors: {
    type: Array,
    default: () => [
      '#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399',
      '#A0CFFF', '#B3E19D', '#D3D4D6', '#E6A23C', '#F56C6C'
    ]
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

  const chartData = props.data.map(item => ({
    name: item[props.nameKey],
    value: item[props.valueKey]
  }))

  // 计算总值用于百分比显示
  const total = chartData.reduce((sum, item) => sum + item.value, 0)

  // 商务稳重配色方案
  const businessColors = props.colors || [
    '#2c5282', // 深蓝 - 主色
    '#4299e1', // 亮蓝
    '#38a169', // 绿色
    '#d69e2e', // 金色
    '#3182ce', // 中蓝
    '#68d391', // 浅绿
    '#f6ad55', // 浅橙
    '#a0aec0', // 灰色
    '#48bb78', // 亮绿
    '#ecc94b'  // 亮黄
  ]

  const option = {
    title: props.title ? {
      text: props.title,
      left: 'center',
      top: 10,
      textStyle: {
        color: '#1a202c',
        fontSize: 14,
        fontWeight: 600
      }
    } : null,
    tooltip: {
      trigger: 'item',
      formatter: params => {
        const percent = ((params.value / total) * 100).toFixed(1)
        return `${params.name}<br/>${params.value} (${percent}%)`
      },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: {
        color: '#1a202c'
      }
    },
    legend: props.showLegend ? {
      orient: ['right', 'left'].includes(props.legendPosition) ? 'vertical' : 'horizontal',
      [props.legendPosition]: 10,
      top: 'middle',
      type: 'scroll',
      textStyle: {
        color: '#4a5568'
      }
    } : null,
    color: businessColors,
    series: [
      {
        name: '数据',
        type: 'pie',
        radius: props.radius,
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
            formatter: params => {
              const percent = ((params.value / total) * 100).toFixed(1)
              return `{name|${params.name}}\n{percent|${percent}%}`
            },
            rich: {
              name: {
                fontSize: 14,
                lineHeight: 20,
                color: '#4a5568'
              },
              percent: {
                fontSize: 18,
                fontWeight: 'bold',
                lineHeight: 24,
                color: '#2c5282'
              }
            }
          }
        },
        labelLine: {
          show: false
        },
        data: chartData
      }
    ]
  }

  chart.setOption(option)
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
.pie-chart {
  width: 100%;
}
</style>
