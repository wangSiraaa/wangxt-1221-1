<template>
  <div class="disposal-detail">
    <el-page-header @back="$router.back()" content="返回列表" style="margin-bottom: 16px;" />

    <el-card v-loading="loading" v-if="record">
      <template #header>
        <h3 class="page-title">处置记录详情 #{{ record.id }}</h3>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="关联指令">
          <span v-if="record.instruction">
            {{ record.instruction.instruction_no }} - {{ record.instruction.title }}
          </span>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="关联异常">
          <span v-if="record.anomaly_id">#{{ record.anomaly_id }}</span>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="动作类型">{{ record.action_type }}</el-descriptions-item>
        <el-descriptions-item label="处理人">{{ record.handler?.real_name }}</el-descriptions-item>
        <el-descriptions-item label="处置内容" :span="2">
          <div style="white-space: pre-wrap;">{{ record.action_content }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="处置结果" :span="2">
          <div style="white-space: pre-wrap;">{{ record.result || '-' }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="快照开始时间">{{ formatTime(record.snapshot_start_time) }}</el-descriptions-item>
        <el-descriptions-item label="快照结束时间">{{ formatTime(record.snapshot_end_time) }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(record.created_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="page-header">
          <h3 class="page-title" style="font-size: 16px;">当时数据曲线快照（处置时留存）</h3>
          <el-tag type="info">数据已固化，可回看分析</el-tag>
        </div>
      </template>

      <v-chart v-if="snapshotData" :option="chartOption" style="height: 450px;" autoresize />
      <el-empty v-else description="暂无快照数据" />
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span class="card-title">快照数据明细</span>
      </template>
      <el-table :data="tableData" size="small" max-height="400">
        <el-table-column label="时间" width="180" prop="time" />
        <el-table-column prop="point_code" label="监测点编号" width="140" />
        <el-table-column prop="point_name" label="监测点名称" />
        <el-table-column label="值" width="140">
          <template #default="{ row }">{{ row.value }} {{ row.unit }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.danger" type="danger" size="small">超危险值</el-tag>
            <el-tag v-else-if="row.warning" type="warning" size="small">超预警值</el-tag>
            <el-tag v-else type="success" size="small">正常</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent, MarkLineComponent } from 'echarts/components'
import dayjs from 'dayjs'
import { getDisposalSnapshotData } from '@/api/disposal'

use([CanvasRenderer, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, MarkLineComponent])

const route = useRoute()

const loading = ref(false)
const record = ref(null)
const snapshotData = ref(null)
const tableData = ref([])

const chartOption = reactive({
  tooltip: { trigger: 'axis' },
  legend: { data: [] },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', boundaryGap: false, data: [] },
  yAxis: { type: 'value' },
  series: []
})

function formatTime(t) {
  return t ? dayjs(t).format('YYYY-MM-DD HH:mm:ss') : '-'
}

async function loadData() {
  loading.value = true
  try {
    const id = parseInt(route.params.id)
    const res = await getDisposalSnapshotData(id)
    record.value = res.record
    snapshotData.value = res

    const dataMap = res.snapshot_data || {}
    const pointsInfo = res.points_info || {}

    const allTimes = new Set()
    Object.values(dataMap).forEach(arr => {
      arr.forEach(d => allTimes.add(dayjs(d.time).format('YYYY-MM-DD HH:mm:ss')))
    })
    const times = Array.from(allTimes).sort()

    chartOption.xAxis.data = times
    const series = []
    const legends = []
    const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#8E44AD']

    let colorIdx = 0
    for (const [pidStr, dataArr] of Object.entries(dataMap)) {
      const pid = parseInt(pidStr)
      const info = pointsInfo[pid]
      if (!info) continue

      const values = times.map(t => {
        const item = dataArr.find(d => dayjs(d.time).format('YYYY-MM-DD HH:mm:ss') === t)
        return item ? item.value : null
      })

      const color = colors[colorIdx % colors.length]
      colorIdx++

      const seriesItem = {
        name: `${info.point_name} (${info.point_code})`,
        type: 'line',
        smooth: true,
        data: values,
        itemStyle: { color },
        lineStyle: { color },
        markLine: { data: [] }
      }

      if (info.warning_threshold) {
        seriesItem.markLine.data.push({
          yAxis: info.warning_threshold,
          lineStyle: { color: '#E6A23C', type: 'dashed' },
          label: { formatter: `预警: ${info.warning_threshold}` }
        })
      }
      if (info.danger_threshold) {
        seriesItem.markLine.data.push({
          yAxis: info.danger_threshold,
          lineStyle: { color: '#F56C6C', type: 'dashed' },
          label: { formatter: `危险: ${info.danger_threshold}` }
        })
      }

      series.push(seriesItem)
      legends.push(seriesItem.name)

      dataArr.forEach(d => {
        tableData.value.push({
          time: dayjs(d.time).format('YYYY-MM-DD HH:mm:ss'),
          point_code: info.point_code,
          point_name: info.point_name,
          value: d.value,
          unit: '',
          warning: info.warning_threshold && d.value >= info.warning_threshold,
          danger: info.danger_threshold && d.value >= info.danger_threshold
        })
      })
    }

    chartOption.legend.data = legends
    chartOption.series = series
    tableData.value.sort((a, b) => dayjs(b.time) - dayjs(a.time))
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-size: 16px; font-weight: 600; }
</style>
