<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card warning-card">
          <div class="stat-content">
            <div class="stat-icon"><el-icon><WarningFilled /></el-icon></div>
            <div class="stat-info">
              <div class="stat-label">预警异常</div>
              <div class="stat-value">{{ alertSummary.warning_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card danger-card">
          <div class="stat-content">
            <div class="stat-icon"><el-icon><CircleCloseFilled /></el-icon></div>
            <div class="stat-info">
              <div class="stat-label">危险异常</div>
              <div class="stat-value">{{ alertSummary.danger_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card critical-card">
          <div class="stat-content">
            <div class="stat-icon"><el-icon><CircleCheckFilled /></el-icon></div>
            <div class="stat-info">
              <div class="stat-label">严重异常（连续超阈值）</div>
              <div class="stat-value">{{ alertSummary.critical_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card unconfirmed-card">
          <div class="stat-content">
            <div class="stat-icon"><el-icon><BellFilled /></el-icon></div>
            <div class="stat-info">
              <div class="stat-label">待确认</div>
              <div class="stat-value">{{ alertSummary.unconfirmed_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span class="card-title">实时监测数据</span>
              <el-button type="primary" link @click="$router.push('/monitor/chart')">查看详情</el-button>
            </div>
          </template>
          <el-table :data="latestDataList" style="width: 100%">
            <el-table-column prop="point_code" label="监测点编号" width="120" />
            <el-table-column prop="point_name" label="监测点名称" />
            <el-table-column prop="type_name" label="类型" width="100" />
            <el-table-column prop="location" label="位置" />
            <el-table-column label="当前值" width="140">
              <template #default="{ row }">
                <span :class="getValueClass(row)">
                  {{ row.value }} {{ row.unit }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="warning_threshold" label="预警阈值" width="120" />
            <el-table-column prop="danger_threshold" label="危险阈值" width="120" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row)" size="small" effect="dark">{{ getStatusText(row) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="time" label="采集时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.time) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span class="card-title">各监测类型24小时趋势</span>
          </template>
          <v-chart :option="trendChartOption" style="height: 350px;" autoresize />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span class="card-title">最新异常</span>
              <el-button type="primary" link @click="$router.push('/anomaly/list')">更多</el-button>
            </div>
          </template>
          <el-table :data="recentAnomalies" size="small">
            <el-table-column prop="point_name" label="监测点" />
            <el-table-column label="级别" width="100">
              <template #default="{ row }">
                <el-tag :type="getAlertType(row.alert_level)" size="small" effect="dark">{{ getAlertText(row.alert_level) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="trigger_value" label="触发值" width="100" />
            <el-table-column prop="is_confirmed" label="是否确认" width="100">
              <template #default="{ row }">
                {{ row.is_confirmed ? '是' : '否' }}
              </template>
            </el-table-column>
            <el-table-column prop="start_time" label="发生时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.start_time) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import * as echarts from 'echarts'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, LegendComponent, GridComponent,
  DatasetComponent, TransformComponent
} from 'echarts/components'
import dayjs from 'dayjs'
import {
  WarningFilled, CircleCloseFilled, CircleCheckFilled, BellFilled
} from '@element-plus/icons-vue'
import { getAlertSummary, getLatestMonitorData, getMonitorPoints, queryMonitorData } from '@/api/monitor'
import { getAnomalyRecords } from '@/api/anomaly'

use([
  CanvasRenderer, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, DatasetComponent, TransformComponent
])

const alertSummary = ref({ warning_count: 0, danger_count: 0, critical_count: 0, unconfirmed_count: 0 })
const monitorPoints = ref([])
const latestDataMap = ref({})
const recentAnomalies = ref([])

const latestDataList = computed(() => {
  return monitorPoints.value.map(p => {
    const latest = latestDataMap.value[p.id] || {}
    return {
      ...p,
      ...latest,
      type_name: p.monitor_type?.type_name,
      unit: p.monitor_type?.unit
    }
  })
})

function getStatusType(row) {
  if (row.value != null) {
    if (row.danger_threshold && row.value >= row.danger_threshold) return 'danger'
    if (row.warning_threshold && row.value >= row.warning_threshold) return 'warning'
  }
  return 'success'
}

function getStatusText(row) {
  if (row.value == null) return '暂无数据'
  if (row.danger_threshold && row.value >= row.danger_threshold) return '危险'
  if (row.warning_threshold && row.value >= row.warning_threshold) return '预警'
  return '正常'
}

function getValueClass(row) {
  if (row.value == null) return ''
  if (row.danger_threshold && row.value >= row.danger_threshold) return 'text-danger'
  if (row.warning_threshold && row.value >= row.warning_threshold) return 'text-warning'
  return 'text-normal'
}

function getAlertType(level) {
  const map = { WARNING: 'warning', DANGER: 'danger', CRITICAL: 'info', NORMAL: 'success' }
  return map[level] || 'info'
}

function getAlertText(level) {
  const map = { WARNING: '预警', DANGER: '危险', CRITICAL: '严重', NORMAL: '正常' }
  return map[level] || '未知'
}

function formatTime(t) {
  return t ? dayjs(t).format('YYYY-MM-DD HH:mm:ss') : '-'
}

const trendChartOption = reactive({
  tooltip: { trigger: 'axis' },
  legend: { data: ['渗压', '位移', '降雨'] },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', boundaryGap: false, data: [] },
  yAxis: [
    { type: 'value', name: '渗压/位移' },
    { type: 'value', name: '降雨' }
  ],
  series: [
    { name: '渗压', type: 'line', smooth: true, data: [] },
    { name: '位移', type: 'line', smooth: true, data: [] },
    { name: '降雨', type: 'line', smooth: true, yAxisIndex: 1, data: [] }
  ]
})

async function loadTrendData() {
  try {
    const endTime = dayjs().toDate()
    const startTime = dayjs().subtract(24, 'hour').toDate()

    const seepagePoints = monitorPoints.value.filter(p => p.monitor_type?.type_code === 'SEEPAGE_PRESSURE').map(p => p.id)
    const displacementPoints = monitorPoints.value.filter(p => p.monitor_type?.type_code === 'DISPLACEMENT').map(p => p.id)
    const rainfallPoints = monitorPoints.value.filter(p => p.monitor_type?.type_code === 'RAINFALL').map(p => p.id)

    const [seepageRes, displacementRes, rainfallRes] = await Promise.all([
      seepagePoints.length ? queryMonitorData({ point_ids: seepagePoints.join(','), start_time: startTime.toISOString(), end_time: endTime.toISOString(), bucket: '1h' }) : Promise.resolve({ data: {} }),
      displacementPoints.length ? queryMonitorData({ point_ids: displacementPoints.join(','), start_time: startTime.toISOString(), end_time: endTime.toISOString(), bucket: '1h' }) : Promise.resolve({ data: {} }),
      rainfallPoints.length ? queryMonitorData({ point_ids: rainfallPoints.join(','), start_time: startTime.toISOString(), end_time: endTime.toISOString(), bucket: '1h' }) : Promise.resolve({ data: {} })
    ])

    const times = []
    let cur = dayjs(startTime)
    while (cur.isBefore(endTime)) {
      times.push(cur.format('MM-DD HH:mm'))
      cur = cur.add(1, 'hour')
    }

    trendChartOption.xAxis.data = times

    const avgSeries = (dataMap) => {
      if (!dataMap || Object.keys(dataMap).length === 0) return new Array(times.length).fill(null)
      const result = []
      const pointArrays = Object.values(dataMap)
      for (let i = 0; i < times.length; i++) {
        let sum = 0, count = 0
        pointArrays.forEach(arr => {
          if (arr && arr[i]) {
            sum += arr[i].avg_value || 0
            count++
          }
        })
        result.push(count > 0 ? +(sum / count).toFixed(2) : null)
      }
      return result
    }

    trendChartOption.series[0].data = avgSeries(seepageRes.data || {})
    trendChartOption.series[1].data = avgSeries(displacementRes.data || {})
    trendChartOption.series[2].data = avgSeries(rainfallRes.data || {})
  } catch (e) {
    console.error('加载趋势数据失败:', e)
  }
}

async function loadData() {
  try {
    const [summary, points, latest, anomalies] = await Promise.all([
      getAlertSummary(),
      getMonitorPoints({ is_active: true }),
      getLatestMonitorData(),
      getAnomalyRecords({ limit: 5 })
    ])
    alertSummary.value = summary
    monitorPoints.value = points
    latestDataMap.value = latest.data || {}
    recentAnomalies.value = anomalies.map(a => ({ ...a, point_name: a.point?.point_name || a.point_id }))
    await loadTrendData()
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.stat-card {
  border: none;
}
.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}
.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #fff;
}
.warning-card .stat-icon { background: #e6a23c; }
.danger-card .stat-icon { background: #f56c6c; }
.critical-card .stat-icon { background: #909399; }
.unconfirmed-card .stat-icon { background: #409EFF; }
.stat-label { font-size: 14px; color: #909399; }
.stat-value { font-size: 28px; font-weight: 600; color: #303133; margin-top: 4px; }

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-title {
  font-size: 16px;
  font-weight: 600;
}

.text-danger { color: #f56c6c; font-weight: 600; }
.text-warning { color: #e6a23c; font-weight: 600; }
.text-normal { color: #67c23a; }
</style>
