<template>
  <div ref="chartRef" class="line-chart" :style="{ height: height }"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  xKey: {
    type: String,
    default: 'month'
  },
  series: {
    type: Array,
    default: () => []
  },
  height: {
    type: String,
    default: '350px'
  },
  title: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
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

  const xAxisData = props.data.map(item => item[props.xKey])

  // 商务配色方案
  const businessColors = {
    primary: '#2c5282',
    primaryLight: '#4299e1',
    success: '#38a169',
    warning: '#d69e2e',
    accent: '#3182ce'
  }

  const seriesOption = props.series.map((s, index) => {
    const color = s.color || Object.values(businessColors)[index % Object.values(businessColors).length]
    return {
      name: s.name,
      type: s.type || 'line',
      smooth: s.smooth !== undefined ? s.smooth : true,
      data: props.data.map(item => item[s.dataKey]),
      itemStyle: { color },
      lineStyle: { width: s.lineWidth || 3 },
      areaStyle: s.areaStyle ? {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: color + '66' },
          { offset: 1, color: color + '0d' }
        ])
      } : null
    }
  })

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
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: {
        color: '#1a202c'
      }
    },
    legend: {
      data: props.series.map(s => s.name),
      top: props.title ? '10%' : '0',
      textStyle: {
        color: '#4a5568'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: props.title ? '20%' : '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
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
    yAxis: props.series.map((s, index) => ({
      type: 'value',
      name: s.name,
      axisLabel: s.axisLabelFormatter || {
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
    })),
    series: seriesOption
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

watch(() => props.series, () => {
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
.line-chart {
  width: 100%;
}
</style>
