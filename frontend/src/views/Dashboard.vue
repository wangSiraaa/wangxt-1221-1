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
      <el-col :span="6">
        <el-card class="stat-card retest-pending-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon"><el-icon><Clock /></el-icon></div>
            <div class="stat-info">
              <div class="stat-label">待复测点位</div>
              <div class="stat-value">{{ retestSummary.pending_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card retest-progress-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon"><el-icon><Loading /></el-icon></div>
            <div class="stat-info">
              <div class="stat-label">复测进行中</div>
              <div class="stat-value">{{ retestSummary.in_progress_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card retest-overdue-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon"><el-icon><Warning /></el-icon></div>
            <div class="stat-info">
              <div class="stat-label">复测已逾期</div>
              <div class="stat-value danger-text">{{ retestSummary.overdue_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card retest-total-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon"><el-icon><DataBoard /></el-icon></div>
            <div class="stat-info">
              <div class="stat-label">复测任务总计</div>
              <div class="stat-value">{{ retestSummary.total_count }}</div>
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
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span class="card-title retest-board-title">
                <el-icon style="vertical-align: -3px; margin-right: 6px; color: #e6a23c;"><Warning /></el-icon>
                复测提醒看板（待复测点位与责任工程师）
              </span>
              <el-button type="primary" link @click="viewAllRetestPlans">查看全部复测计划</el-button>
            </div>
          </template>
          <el-table :data="pendingRetestPlans" size="small" style="width: 100%" empty-text="暂无待复测任务">
            <el-table-column prop="plan_no" label="复测单号" width="150" />
            <el-table-column prop="point_code" label="监测点编号" width="130">
              <template #default="{ row }">{{ row.point?.point_code || '-' }}</template>
            </el-table-column>
            <el-table-column label="监测点名称">
              <template #default="{ row }">{{ row.point?.point_name || row.point_id }}</template>
            </el-table-column>
            <el-table-column prop="type_name" label="监测类型" width="100">
              <template #default="{ row }">{{ row.point?.monitor_type?.type_name || '-' }}</template>
            </el-table-column>
            <el-table-column prop="trigger_value" label="触发值" width="100" />
            <el-table-column prop="threshold_value" label="阈值" width="100" />
            <el-table-column prop="consecutive_count" label="连续超阈值次数" width="130" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.consecutive_count >= 2" type="danger" effect="dark" size="small">{{ row.consecutive_count }} 次</el-tag>
                <el-tag v-else type="warning" size="small">{{ row.consecutive_count }} 次</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="责任工程师" width="130">
              <template #default="{ row }">
                <div class="engineer-info">
                  <el-icon><UserFilled /></el-icon>
                  <span>{{ row.responsible_engineer?.real_name || '未指派' }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="phone" label="联系电话" width="130">
              <template #default="{ row }">{{ row.responsible_engineer?.phone || '-' }}</template>
            </el-table-column>
            <el-table-column label="计划复测时间" width="180">
              <template #default="{ row }">
                <span :class="{ 'text-overdue': isOverdue(row) }">
                  {{ formatTime(row.planned_retest_time) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="110" align="center">
              <template #default="{ row }">
                <el-tag v-if="isOverdue(row)" type="danger" size="small" effect="dark">逾期</el-tag>
                <el-tag v-else :type="getRetestStatusType(row.status)" size="small" effect="dark">
                  {{ getRetestStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="handleStartRetest(row)" :disabled="row.status !== 'PENDING'">
                  开始复测
                </el-button>
                <el-button type="success" link size="small" @click="handleCompleteRetest(row)">
                  完成复测
                </el-button>
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

    <el-dialog v-model="completeDialogVisible" title="完成复测" width="500px">
      <el-form :model="completeForm" label-width="100px">
        <el-form-item label="复测值">
          <el-input-number v-model="completeForm.retest_value" :precision="4" :step="1" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="复测说明">
          <el-input v-model="completeForm.retest_note" type="textarea" :rows="3" placeholder="请输入复测情况说明..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="completeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCompleteRetest">确认提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
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
  WarningFilled, CircleCloseFilled, CircleCheckFilled, BellFilled,
  Clock, Loading, Warning, DataBoard, UserFilled
} from '@element-plus/icons-vue'
import { getAlertSummary, getLatestMonitorData, getMonitorPoints, queryMonitorData } from '@/api/monitor'
import { getAnomalyRecords } from '@/api/anomaly'
import {
  getRetestDashboardSummary, getRetestPlans, startRetest, completeRetest
} from '@/api/retest'

use([
  CanvasRenderer, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, DatasetComponent, TransformComponent
])

const alertSummary = ref({ warning_count: 0, danger_count: 0, critical_count: 0, unconfirmed_count: 0 })
const retestSummary = ref({ pending_count: 0, in_progress_count: 0, overdue_count: 0, total_count: 0 })
const monitorPoints = ref([])
const latestDataMap = ref({})
const recentAnomalies = ref([])
const pendingRetestPlans = ref([])
const completeDialogVisible = ref(false)
const currentRetestPlan = ref(null)
const completeForm = reactive({
  retest_value: 0,
  retest_note: ''
})

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

function getRetestStatusType(status) {
  const map = { PENDING: 'warning', IN_PROGRESS: 'primary', COMPLETED: 'success', CANCELLED: 'info' }
  return map[status] || 'info'
}

function getRetestStatusText(status) {
  const map = { PENDING: '待复测', IN_PROGRESS: '进行中', COMPLETED: '已完成', CANCELLED: '已取消' }
  return map[status] || status
}

function isOverdue(row) {
  if (!row?.planned_retest_time || row.status === 'COMPLETED' || row.status === 'CANCELLED') return false
  return dayjs(row.planned_retest_time).isBefore(dayjs())
}

async function handleStartRetest(row) {
  try {
    await ElMessageBox.confirm(
      `确定要开始对监测点 [${row.point?.point_name || row.point_id}] 的复测吗？`,
      '开始复测确认',
      { type: 'warning', confirmButtonText: '确定开始', cancelButtonText: '取消' }
    )
    await startRetest(row.id)
    ElMessage.success('复测任务已开始')
    await loadRetestData()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

function handleCompleteRetest(row) {
  currentRetestPlan.value = row
  completeForm.retest_value = 0
  completeForm.retest_note = ''
  completeDialogVisible.value = true
}

async function submitCompleteRetest() {
  if (!currentRetestPlan.value) return
  if (completeForm.retest_value == null) {
    ElMessage.warning('请填写复测值')
    return
  }
  try {
    await completeRetest(currentRetestPlan.value.id, {
      retest_value: completeForm.retest_value,
      retest_note: completeForm.retest_note
    })
    ElMessage.success('复测完成，已提交结果')
    completeDialogVisible.value = false
    await loadRetestData()
  } catch (e) {
    console.error(e)
  }
}

function viewAllRetestPlans() {
  ElMessage.info('复测计划列表功能即将上线，当前可在看板中直接处理待复测任务')
}

async function loadRetestData() {
  try {
    const [summaryRes, plansRes] = await Promise.all([
      getRetestDashboardSummary(),
      getRetestPlans({ only_active: true, limit: 50 })
    ])
    retestSummary.value = summaryRes
    pendingRetestPlans.value = plansRes
  } catch (e) {
    console.error('加载复测数据失败:', e)
  }
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
    await Promise.all([
      loadTrendData(),
      loadRetestData()
    ])
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

.retest-pending-card .stat-icon { background: #e6a23c; }
.retest-progress-card .stat-icon { background: #409EFF; }
.retest-overdue-card .stat-icon { background: #f56c6c; }
.retest-total-card .stat-icon { background: #36b368; }

.danger-text { color: #f56c6c !important; }
.text-overdue { color: #f56c6c; font-weight: 600; }

.engineer-info {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.retest-board-title {
  font-size: 16px;
  font-weight: 600;
}
</style>
