<template>
  <div class="anomaly-detail">
    <el-page-header @back="$router.back()" content="返回列表" style="margin-bottom: 16px;" />

    <el-card v-loading="loading" v-if="anomaly">
      <template #header>
        <div class="page-header">
          <h3 class="page-title">异常详情 #{{ anomaly.id }}</h3>
          <div>
            <el-tag :type="getAlertType(anomaly.alert_level)" size="large" effect="dark">
              {{ getAlertText(anomaly.alert_level) }}
              <span v-if="anomaly.consecutive_count >= 2"> (连续{{ anomaly.consecutive_count }}次超阈值)</span>
            </el-tag>
            <el-tag v-if="anomaly.is_confirmed" type="success" size="large" style="margin-left: 8px;">已确认</el-tag>
            <el-tag v-else type="warning" size="large" style="margin-left: 8px;">待确认</el-tag>
          </div>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="监测点">{{ anomaly.point?.point_code }} - {{ anomaly.point?.point_name }}</el-descriptions-item>
        <el-descriptions-item label="位置">{{ anomaly.point?.location }}</el-descriptions-item>
        <el-descriptions-item label="触发类型">{{ anomaly.trigger_type === 'CONSECUTIVE_THRESHOLD' ? '连续超阈值' : anomaly.trigger_type === 'DANGER_THRESHOLD' ? '超危险阈值' : '超预警阈值' }}</el-descriptions-item>
        <el-descriptions-item label="触发值/阈值">{{ anomaly.trigger_value }} / {{ anomaly.threshold_value }}</el-descriptions-item>
        <el-descriptions-item label="发生时间">{{ formatTime(anomaly.start_time) }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ anomaly.end_time ? formatTime(anomaly.end_time) : '未结束' }}</el-descriptions-item>
        <el-descriptions-item label="确认人">{{ anomaly.confirmer?.real_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="确认时间">{{ anomaly.confirmed_at ? formatTime(anomaly.confirmed_at) : '-' }}</el-descriptions-item>
        <el-descriptions-item label="确认说明" :span="2">{{ anomaly.confirmation_note || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span class="card-title">异常发生前后24小时监测曲线</span>
      </template>
      <v-chart :option="chartOption" style="height: 400px;" autoresize />
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="page-header">
          <span class="card-title">关联处置指令</span>
          <el-button
            v-if="userStore.hasRole('SAFETY_HEAD')"
            type="primary"
            size="small"
            @click="goCreateInstruction"
          >
            签发处置指令
          </el-button>
        </div>
      </template>
      <el-table :data="relatedInstructions" size="small">
        <el-table-column prop="instruction_no" label="指令编号" width="160" />
        <el-table-column prop="title" label="标题" />
        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.instruction_type === 'STOP_DISCHARGE' ? 'danger' : 'warning'" size="small">
              {{ row.instruction_type === 'STOP_DISCHARGE' ? '停排指令' : '降级指令' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">{{ getInstructionStatusText(row.status) }}</template>
        </el-table-column>
        <el-table-column label="签发时间" width="180">
          <template #default="{ row }">{{ row.issued_at ? formatTime(row.issued_at) : '-' }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent, MarkLineComponent } from 'echarts/components'
import dayjs from 'dayjs'
import { useUserStore } from '@/stores/user'
import { getAnomalyRecord } from '@/api/anomaly'
import { queryMonitorData, getMonitorPoints } from '@/api/monitor'
import { getInstructions } from '@/api/instruction'

use([CanvasRenderer, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, MarkLineComponent])

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const anomaly = ref(null)
const relatedInstructions = ref([])
const monitorPoints = ref([])

const chartOption = reactive({
  tooltip: { trigger: 'axis' },
  legend: { data: [] },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', boundaryGap: false, data: [] },
  yAxis: { type: 'value' },
  series: []
})

function getAlertType(level) {
  const map = { WARNING: 'warning', DANGER: 'danger', CRITICAL: 'info', NORMAL: 'success' }
  return map[level] || 'info'
}

function getAlertText(level) {
  const map = { WARNING: '预警', DANGER: '危险', CRITICAL: '严重(连续超阈值)', NORMAL: '正常' }
  return map[level] || '未知'
}

function getInstructionStatusText(status) {
  const map = { DRAFT: '草稿', ISSUED: '已签发', EXECUTING: '执行中', LIFTED: '已解除', CANCELLED: '已取消' }
  return map[status] || status
}

function formatTime(t) {
  return t ? dayjs(t).format('YYYY-MM-DD HH:mm:ss') : '-'
}

function goCreateInstruction() {
  router.push({ path: '/instruction/create', query: { anomaly_id: anomaly.value.id } })
}

async function loadDetail() {
  loading.value = true
  try {
    const anomalyId = parseInt(route.params.id)
    const [anomalyData, points, instructions] = await Promise.all([
      getAnomalyRecord(anomalyId),
      getMonitorPoints(),
      getInstructions()
    ])
    anomaly.value = anomalyData
    monitorPoints.value = points
    relatedInstructions.value = instructions.filter(i =>
      i.related_anomaly_ids && i.related_anomaly_ids.includes(anomalyId)
    )

    if (anomalyData) {
      await loadChartData(anomalyData)
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadChartData(anomalyData) {
  try {
    const point = monitorPoints.value.find(p => p.id === anomalyData.point_id)
    const startTime = dayjs(anomalyData.start_time).subtract(12, 'hour').toISOString()
    const endTime = dayjs(anomalyData.start_time).add(12, 'hour').toISOString()

    const res = await queryMonitorData({
      point_ids: String(anomalyData.point_id),
      start_time: startTime,
      end_time: endTime
    })

    const dataArr = (res.data && res.data[anomalyData.point_id]) || []
    const times = dataArr.map(d => dayjs(d.time).format('MM-DD HH:mm'))
    const values = dataArr.map(d => d.value)

    chartOption.xAxis.data = times
    chartOption.legend.data = [point?.point_name || '监测值']
    chartOption.series = [{
      name: point?.point_name || '监测值',
      type: 'line',
      smooth: true,
      data: values,
      markLine: {
        data: []
      }
    }]

    if (point?.warning_threshold) {
      chartOption.series[0].markLine.data.push({
        yAxis: parseFloat(point.warning_threshold),
        lineStyle: { color: '#E6A23C', type: 'dashed' },
        label: { formatter: `预警阈值: ${point.warning_threshold}` }
      })
    }
    if (point?.danger_threshold) {
      chartOption.series[0].markLine.data.push({
        yAxis: parseFloat(point.danger_threshold),
        lineStyle: { color: '#F56C6C', type: 'dashed' },
        label: { formatter: `危险阈值: ${point.danger_threshold}` }
      })
    }
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  loadDetail()
})
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-size: 16px; font-weight: 600; }
</style>
