<template>
  <div class="disposal-list">
    <el-card>
      <template #header>
        <div class="page-header">
          <h3 class="page-title">处置记录列表</h3>
          <el-button type="primary" @click="openCreate">
            <el-icon><Plus /></el-icon>新增处置记录
          </el-button>
        </div>
      </template>

      <el-table :data="list" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="关联指令" width="160">
          <template #default="{ row }">
            <span v-if="row.instruction">{{ row.instruction.instruction_no }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="关联异常" width="100">
          <template #default="{ row }">{{ row.anomaly_id || '-' }}</template>
        </el-table-column>
        <el-table-column prop="action_type" label="动作类型" width="140" />
        <el-table-column prop="action_content" label="处置内容" show-overflow-tooltip />
        <el-table-column prop="handler.real_name" label="处理人" width="100" />
        <el-table-column label="数据快照时间范围" width="320">
          <template #default="{ row }">
            {{ formatTime(row.snapshot_start_time) }} ~ {{ formatTime(row.snapshot_end_time) }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="goDetail(row)">
              查看数据快照
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="createVisible" title="新增处置记录" width="640px">
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="120px">
        <el-form-item label="关联指令">
          <el-select v-model="createForm.instruction_id" placeholder="选择处置指令" clearable style="width: 100%;">
            <el-option
              v-for="i in instructions"
              :key="i.id"
              :label="`${i.instruction_no} - ${i.title}`"
              :value="i.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关联异常">
          <el-select v-model="createForm.anomaly_id" placeholder="选择异常记录" clearable style="width: 100%;">
            <el-option
              v-for="a in anomalies"
              :key="a.id"
              :label="`#${a.id} [${a.point?.point_name}] ${a.trigger_value}/${a.threshold_value}`"
              :value="a.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="动作类型" prop="action_type">
          <el-input v-model="createForm.action_type" placeholder="例如：现场处置、数据分析、指令执行等" />
        </el-form-item>
        <el-form-item label="处置内容" prop="action_content">
          <el-input v-model="createForm.action_content" type="textarea" :rows="4" placeholder="请详细描述处置过程和内容" />
        </el-form-item>
        <el-form-item label="关联监测点">
          <el-select v-model="createForm.snapshot_point_ids" multiple filterable placeholder="选择需要留存数据快照的监测点" style="width: 100%;">
            <el-option
              v-for="p in monitorPoints"
              :key="p.id"
              :label="`${p.point_code} - ${p.point_name}`"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="快照时间范围" prop="snapshot_time_range">
          <el-date-picker
            v-model="createForm.snapshot_time_range"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="处置结果">
          <el-input v-model="createForm.result" type="textarea" :rows="3" placeholder="处置结果（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { getDisposalRecords, createDisposalRecord } from '@/api/disposal'
import { getInstructions } from '@/api/instruction'
import { getAnomalyRecords } from '@/api/anomaly'
import { getMonitorPoints } from '@/api/monitor'

const router = useRouter()

const loading = ref(false)
const list = ref([])
const instructions = ref([])
const anomalies = ref([])
const monitorPoints = ref([])

const createVisible = ref(false)
const createLoading = ref(false)
const createFormRef = ref(null)
const createForm = reactive({
  instruction_id: null,
  anomaly_id: null,
  action_type: '',
  action_content: '',
  snapshot_point_ids: [],
  snapshot_time_range: null,
  snapshot_start_time: null,
  snapshot_end_time: null,
  result: ''
})
const createRules = {
  action_type: [{ required: true, message: '请输入动作类型', trigger: 'blur' }],
  action_content: [{ required: true, message: '请输入处置内容', trigger: 'blur' }],
  snapshot_time_range: [{ required: true, message: '请选择快照时间范围', trigger: 'change' }]
}

function formatTime(t) {
  return t ? dayjs(t).format('YYYY-MM-DD HH:mm:ss') : '-'
}

async function loadData() {
  loading.value = true
  try {
    list.value = await getDisposalRecords()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function goDetail(row) {
  router.push(`/disposal/${row.id}`)
}

async function openCreate() {
  try {
    const [inst, anom, points] = await Promise.all([
      getInstructions({ status: 'ISSUED' }),
      getAnomalyRecords(),
      getMonitorPoints({ is_active: true })
    ])
    instructions.value = inst
    anomalies.value = anom
    monitorPoints.value = points
    createVisible.value = true
  } catch (e) {
    console.error(e)
  }
}

async function handleCreate() {
  try {
    await createFormRef.value.validate()
    createLoading.value = true

    const payload = {
      instruction_id: createForm.instruction_id || null,
      anomaly_id: createForm.anomaly_id || null,
      action_type: createForm.action_type,
      action_content: createForm.action_content,
      snapshot_point_ids: createForm.snapshot_point_ids.length > 0 ? createForm.snapshot_point_ids : null,
      snapshot_start_time: createForm.snapshot_time_range[0],
      snapshot_end_time: createForm.snapshot_time_range[1],
      result: createForm.result || null
    }

    await createDisposalRecord(payload)
    ElMessage.success('处置记录已保存，数据快照已留存')
    createVisible.value = false
    await loadData()
  } catch (e) {
    if (e !== false) console.error(e)
  } finally {
    createLoading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
</style>
