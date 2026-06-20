<template>
  <div class="data-entry">
    <el-card>
      <template #header>
        <div class="page-header">
          <h3 class="page-title">监测数据录入</h3>
        </div>
      </template>

      <el-alert
        v-if="stopDischargeInfo.has_active_stop"
        :title="`当前存在未解除的停排指令：${stopDischargeInfo.active_instructions.map(i => i.instruction_no).join(', ')}`"
        type="warning"
        show-icon
        :closable="false"
        style="margin-bottom: 20px;"
      />

      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="监测点" prop="point_id">
              <el-select v-model="form.point_id" placeholder="请选择监测点" style="width: 100%;" filterable>
                <el-option
                  v-for="p in monitorPoints"
                  :key="p.id"
                  :label="`${p.point_code} - ${p.point_name} (${p.monitor_type?.type_name})`"
                  :value="p.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="监测值" prop="value">
              <el-input-number
                v-model="form.value"
                :precision="4"
                :controls="false"
                placeholder="请输入监测值"
                style="width: 100%;"
              />
              <div v-if="selectedPoint" class="threshold-info">
                <span class="text-muted">单位：{{ selectedPoint.monitor_type?.unit }}</span>
                <span class="text-warning" style="margin-left: 12px;">预警阈值：{{ selectedPoint.warning_threshold }}</span>
                <span class="text-danger" style="margin-left: 12px;">危险阈值：{{ selectedPoint.danger_threshold }}</span>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="采集时间" prop="time">
              <el-date-picker
                v-model="form.time"
                type="datetime"
                placeholder="选择采集时间"
                style="width: 100%;"
                value-format="YYYY-MM-DD HH:mm:ss"
                :default-time="defaultTime"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="请输入备注（可选）" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">提交数据</el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span class="card-title">最近录入记录</span>
      </template>
      <el-table :data="recentRecords" size="small">
        <el-table-column label="时间" width="180">
          <template #default="{ row }">{{ formatTime(row.time) }}</template>
        </el-table-column>
        <el-table-column prop="point_code" label="监测点编号" width="120" />
        <el-table-column prop="point_name" label="监测点名称" />
        <el-table-column prop="type_name" label="类型" width="80" />
        <el-table-column label="值" width="120">
          <template #default="{ row }">{{ row.value }} {{ row.unit }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.anomaly_generated" type="danger" size="small" effect="dark">已触发异常</el-tag>
            <el-tag v-else type="success" size="small">正常</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" show-overflow-tooltip />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { getMonitorPoints, createMonitorData } from '@/api/monitor'
import { checkStopDischarge } from '@/api/instruction'

const formRef = ref(null)
const submitting = ref(false)
const monitorPoints = ref([])
const recentRecords = ref([])
const stopDischargeInfo = ref({ has_active_stop: false, active_instructions: [] })

const defaultTime = new Date()

const form = reactive({
  point_id: null,
  value: null,
  time: dayjs().format('YYYY-MM-DD HH:mm:ss'),
  remark: ''
})

const rules = {
  point_id: [{ required: true, message: '请选择监测点', trigger: 'change' }],
  value: [{ required: true, message: '请输入监测值', trigger: 'blur' }],
  time: [{ required: true, message: '请选择采集时间', trigger: 'change' }]
}

const selectedPoint = computed(() => {
  return monitorPoints.value.find(p => p.id === form.point_id)
})

function formatTime(t) {
  return t ? dayjs(t).format('YYYY-MM-DD HH:mm:ss') : '-'
}

async function loadData() {
  try {
    const [points, stopInfo] = await Promise.all([
      getMonitorPoints({ is_active: true }),
      checkStopDischarge()
    ])
    monitorPoints.value = points
    stopDischargeInfo.value = stopInfo
  } catch (e) {
    console.error(e)
  }
}

async function handleSubmit() {
  try {
    await formRef.value.validate()
    submitting.value = true
    const res = await createMonitorData(form)
    if (res.anomaly_generated) {
      ElMessage.warning('数据录入成功！已触发异常预警，请通知地测工程师确认')
    } else {
      ElMessage.success('数据录入成功')
    }
    const point = selectedPoint.value
    recentRecords.value.unshift({
      time: form.time,
      point_code: point?.point_code,
      point_name: point?.point_name,
      type_name: point?.monitor_type?.type_name,
      value: form.value,
      unit: point?.monitor_type?.unit,
      anomaly_generated: res.anomaly_generated,
      remark: form.remark
    })
    if (recentRecords.value.length > 10) {
      recentRecords.value = recentRecords.value.slice(0, 10)
    }
    resetForm()
  } catch (e) {
    if (e !== false) console.error(e)
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  formRef.value?.resetFields()
  form.value = null
  form.time = dayjs().format('YYYY-MM-DD HH:mm:ss')
  form.remark = ''
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.threshold-info {
  margin-top: 6px;
  font-size: 12px;
}
.text-muted { color: #909399; }
.text-warning { color: #e6a23c; }
.text-danger { color: #f56c6c; }
.card-title { font-size: 16px; font-weight: 600; }
</style>
