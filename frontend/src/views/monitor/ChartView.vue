<template>
  <div class="chart-view">
    <el-card>
      <template #header>
        <div class="page-header">
          <h3 class="page-title">监测曲线查看</h3>
        </div>
      </template>

      <div class="filter-bar">
        <el-form inline label-width="100px">
          <el-form-item label="监测类型">
            <el-select v-model="filter.monitor_type_id" placeholder="全部" @change="onTypeChange" clearable style="width: 180px;">
              <el-option
                v-for="t in monitorTypes"
                :key="t.id"
                :label="t.type_name"
                :value="t.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="监测点">
            <el-select v-model="filter.point_ids" multiple placeholder="请选择监测点" filterable style="width: 400px;">
              <el-option
                v-for="p in filteredPoints"
                :key="p.id"
                :label="`${p.point_code} - ${p.point_name}`"
                :value="p.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="filter.dateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              value-format="YYYY-MM-DD HH:mm:ss"
              style="width: 360px;"
            />
          </el-form-item>
          <el-form-item label="聚合粒度">
            <el-select v-model="filter.bucket" placeholder="原始数据" clearable style="width: 140px;">
              <el-option label="1分钟" value="1m" />
              <el-option label="5分钟" value="5m" />
              <el-option label="15分钟" value="15m" />
              <el-option label="1小时" value="1h" />
              <el-option label="1天" value="1d" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" @click="loadChartData">
              查询
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <div v-if="!filter.point_ids && filter.point_ids.length > 0" style="margin-bottom: 16px;">
        <el-checkbox v-model="showThresholdLines">显示阈值线</el-checkbox>
      </div>

      <v-chart :option="chartOption" style="height: 500px;" autoresize />
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span class="card-title">数据明细</span>
      </template>
      <el-table :data="tableData" size="small" max-height="400">
        <el-table-column label="时间" width="180" prop="time" />
        <el-table-column prop="point_code" label="监测点" />
        <el-table-column label="值" width="120">
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
import { ref, reactive, computed, onMounted } from 'vue'
import * as echarts from 'echarts'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent, MarkLineComponent } from 'echarts/components'
import dayjs from 'dayjs'
import { getMonitorTypes, getMonitorPoints, queryMonitorData } from '@/api/monitor'

use([CanvasRenderer, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, MarkLineComponent])

const loading = ref(false)
const monitorTypes = ref([])
const monitorPoints = ref([])
const showThresholdLines = ref(true)

const filter = reactive({
  monitor_type_id: null,
  point_ids: [],
  dateRange: [
    dayjs().subtract(24, 'hour').format('YYYY-MM-DD HH:mm:ss'),
    dayjs().format('YYYY-MM-DD HH:mm:ss')
  ],
  bucket: null
})

const filteredPoints = computed(() => {
  if (!filter.monitor_type_id) return monitorPoints.value
  return monitorPoints.value.filter(p => p.monitor_type_id === filter.monitor_type_id)
})

const chartOption = reactive({
  tooltip: { trigger: 'axis' },
  legend: { data: [] },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', boundaryGap: false, data: [] },
  yAxis: { type: 'value' },
  series: []
})

const tableData = ref([])

function onTypeChange() {
  filter.point_ids = []
}

function getPointInfo(pointId) {
  return monitorPoints.value.find(p => p.id === pointId)
}

function getUnit(pointId) {
  const p = getPointInfo(pointId)
  return p?.monitor_type?.unit || ''
}

const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#8E44AD', '#16A085']

async function loadChartData() {
  if (!filter.dateRange || filter.dateRange.length !== 2) return
  loading.value = true
  try {
    const params = {
      start_time: filter.dateRange[0],
      end_time: filter.dateRange[1]
    }
    if (filter.point_ids && filter.point_ids.length > 0) {
      params.point_ids = filter.point_ids.join(',')
    }
    if (filter.bucket) {
      params.bucket = filter.bucket
    }

    const res = await queryMonitorData(params)
    const dataMap = res.data || {}

    const times = []
    const startTime = dayjs(filter.dateRange[0])
    const endTime = dayjs(filter.dateRange[1])

    let step = 1
    let unit = 'minute'
    if (filter.bucket) {
      if (filter.bucket === '1h') {
      step = 1; unit = 'hour'
      } else if (filter.bucket === '1d') {
        step = 1; unit = 'day'
      } else if (filter.bucket === '15m') {
        step = 15; unit = 'minute'
      } else if (filter.bucket === '5m') {
        step = 5; unit = 'minute'
      }
    }

    let cur = startTime
    while (cur.isBefore(endTime)) {
      times.push(cur.format('YYYY-MM-DD HH:mm:ss'))
      cur = cur.add(step, unit)
    }

    chartOption.xAxis.data = times

    const series = []
    const legendData = []
    const allTableData = []

    const pointIdsToShow = filter.point_ids && filter.point_ids.length > 0
      ? filter.point_ids
      : Object.keys(dataMap).map(k => parseInt(k))

    let colorIdx = 0
    for (const pid of pointIdsToShow) {
      const point = getPointInfo(pid)
      if (!point) continue
      const dataArr = dataMap[pid] || []
      const values = []
      for (let i = 0; i < times.length; i++) {
        if (dataArr[i]) {
          values.push(dataArr[i].avg_value != null ? dataArr[i].avg_value : dataArr[i].value != null ? dataArr[i].value : null)
        } else {
          values.push(null)
        }
      }
      const color = colors[colorIdx % colors.length]
      colorIdx++

      const seriesItem = {
        name: `${point.point_name} (${point.point_code})`,
        type: 'line',
        smooth: true,
        data: values,
        itemStyle: { color },
        lineStyle: { color },
        markLine: showThresholdLines.value ? {
          silent: true,
          data: []
        } : undefined
      }

      if (showThresholdLines.value && point.warning_threshold) {
        seriesItem.markLine.data.push({
          yAxis: parseFloat(point.warning_threshold),
          name: '预警阈值',
          lineStyle: { color: '#E6A23C', type: 'dashed' },
          label: { formatter: `预警: ${point.warning_threshold}` }
        })
      }
      if (showThresholdLines.value && point.danger_threshold) {
        seriesItem.markLine.data.push({
          yAxis: parseFloat(point.danger_threshold),
          name: '危险阈值',
          lineStyle: { color: '#F56C6C', type: 'dashed' },
          label: { formatter: `危险: ${point.danger_threshold}` }
        })
      }

      series.push(seriesItem)
      legendData.push(seriesItem.name)

      for (let i = 0; i < times.length; i++) {
        if (dataArr[i]) {
          const val = dataArr[i].avg_value != null ? dataArr[i].avg_value : dataArr[i].value
          allTableData.push({
          time: times[i],
          point_code: point.point_code,
          point_name: point.point_name,
          value: val,
          unit: point.monitor_type?.unit,
          warning: point.warning_threshold && val >= point.warning_threshold,
          danger: point.danger_threshold && val >= point.danger_threshold
        })
        }
      }
    }

    chartOption.legend.data = legendData
    chartOption.series = series
    tableData.value = allTableData.sort((a, b) => dayjs(b.time) - dayjs(a.time)).slice(0, 500)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadData() {
  try {
    const [types, points] = await Promise.all([getMonitorTypes(), getMonitorPoints({ is_active: true })])
    monitorTypes.value = types
    monitorPoints.value = points
    if (points.length > 0) {
      filter.point_ids = [points[0].id]
      await loadChartData()
    }
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.card-title { font-size: 16px; font-weight: 600; }
.filter-bar { margin-bottom: 20px; padding: 16px; background: #f5f7fa; border-radius: 4px; }
</style>
