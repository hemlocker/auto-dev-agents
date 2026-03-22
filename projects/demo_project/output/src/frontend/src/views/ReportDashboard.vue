<template>
  <div class="report-dashboard-container">
    <div class="header">
      <h1>统计报表</h1>
      <div>
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-dropdown @command="handleExport">
          <el-button type="primary">
            <el-icon><Download /></el-icon>
            导出
            <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="excel">导出 Excel</el-dropdown-item>
              <el-dropdown-item command="pdf">导出 PDF</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 筛选条件 -->
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="统计维度">
          <el-select v-model="dimension" @change="handleDimensionChange">
            <el-option label="按设备状态" value="status" />
            <el-option label="按使用部门" value="department" />
            <el-option label="按设备类型" value="type" />
            <el-option label="按购买时间" value="time" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadStatistics">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计摘要 -->
    <el-row :gutter="20" class="summary-cards">
      <el-col :span="6">
        <el-statistic title="设备总数" :value="totalDevices" />
      </el-col>
      <el-col :span="6" v-if="dimension === 'status'">
        <el-statistic title="在用设备" :value="inUseDevices" value-style="color: #67C23A" />
      </el-col>
      <el-col :span="6" v-if="dimension === 'status'">
        <el-statistic title="闲置设备" :value="idleDevices" value-style="color: #E6A23C" />
      </el-col>
      <el-col :span="6" v-if="dimension === 'status'">
        <el-statistic title="报废设备" :value="scrappedDevices" value-style="color: #F56C6C" />
      </el-col>
    </el-row>

    <!-- 图表展示 -->
    <el-card class="chart-card">
      <div ref="chartRef" class="chart-container"></div>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <template #header>
        <span>详细数据</span>
      </template>
      <el-table :data="tableData" border stripe>
        <el-table-column 
          v-if="dimension === 'status'" 
          prop="status" 
          label="设备状态" 
          width="120"
        />
        <el-table-column 
          v-if="dimension === 'department'" 
          prop="department" 
          label="使用部门" 
          width="150"
        />
        <el-table-column 
          v-if="dimension === 'type'" 
          prop="device_type" 
          label="设备类型" 
          width="150"
        />
        <el-table-column 
          v-if="dimension === 'time'" 
          prop="period" 
          label="时间段" 
          width="120"
        />
        <el-table-column prop="count" label="数量" width="100" sortable />
        <el-table-column prop="percentage" label="占比" width="100">
          <template #default="{ row }">
            <span v-if="row.percentage !== undefined">{{ row.percentage }}%</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Download, ArrowDown } from '@element-plus/icons-vue'
import { getStatistics } from '@/api/report'
import * as echarts from 'echarts'

const dimension = ref('status')
const dateRange = ref([])
const loading = ref(false)
const chartRef = ref(null)
let chartInstance = null

const totalDevices = ref(0)
const inUseDevices = ref(0)
const idleDevices = ref(0)
const scrappedDevices = ref(0)
const tableData = ref([])

onMounted(() => {
  loadStatistics()
  window.addEventListener('resize', handleResize)
})

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return
  
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  chartInstance = echarts.init(chartRef.value)
  
  const option = {
    title: {
      text: '设备统计分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    }
  }
  
  chartInstance.setOption(option)
}

// 更新图表数据
const updateChart = (data, dimensionType) => {
  if (!chartInstance) return
  
  let option = {}
  
  if (dimensionType === 'status' || dimensionType === 'type') {
    // 饼图
    const pieData = data.map(item => ({
      name: item.status || item.device_type,
      value: item.count
    }))
    
    option = {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: [
        {
          name: '设备数量',
          type: 'pie',
          radius: '60%',
          data: pieData,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }
  } else if (dimensionType === 'department') {
    // 柱状图
    const barData = data.map(item => ({
      name: item.department,
      value: item.count
    }))
    
    option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      xAxis: {
        type: 'category',
        data: data.map(item => item.department),
        axisLabel: {
          interval: 0,
          rotate: 30
        }
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '设备数量',
          type: 'bar',
          data: data.map(item => item.count),
          itemStyle: {
            color: '#409EFF'
          }
        }
      ]
    }
  } else if (dimensionType === 'time') {
    // 折线图
    option = {
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: data.map(item => item.period)
      },
      yAxis: {
        type: 'value',
        name: '设备数量'
      },
      series: [
        {
          name: '采购趋势',
          type: 'line',
          data: data.map(item => item.count),
          smooth: true,
          itemStyle: {
            color: '#67C23A'
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
              { offset: 1, color: 'rgba(103, 194, 58, 0.01)' }
            ])
          }
        }
      ]
    }
  }
  
  chartInstance.setOption(option)
}

// 处理窗口大小变化
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 加载统计数据
const loadStatistics = async () => {
  loading.value = true
  try {
    const params = {
      dimension: dimension.value
    }
    
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    
    const res = await getStatistics(params)
    const data = res.data
    
    // 更新摘要
    totalDevices.value = data.summary.total || 0
    if (data.summary.in_use !== undefined) {
      inUseDevices.value = data.summary.in_use
      idleDevices.value = data.summary.idle
      scrappedDevices.value = data.summary.scrapped
    }
    
    // 更新表格数据
    tableData.value = data.details || []
    
    // 更新图表
    await nextTick()
    initChart()
    updateChart(data.details, dimension.value)
    
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

// 维度变化
const handleDimensionChange = () => {
  loadStatistics()
}

// 刷新数据
const refreshData = () => {
  loadStatistics()
}

// 导出
const handleExport = (command) => {
  ElMessage.info(`导出${command.toUpperCase()}功能开发中`)
  // TODO: 实现导出功能
}

// 页面卸载
import { onBeforeUnmount } from 'vue'
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
  }
})
</script>

<style scoped>
.report-dashboard-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h1 {
  font-size: 24px;
  color: #303133;
}

.filter-card {
  margin-bottom: 20px;
}

.summary-cards {
  margin-bottom: 20px;
}

.summary-cards .el-statistic {
  padding: 20px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.chart-card {
  margin-bottom: 20px;
  min-height: 400px;
}

.chart-container {
  height: 400px;
  width: 100%;
}

.table-card {
  margin-bottom: 20px;
}
</style>
