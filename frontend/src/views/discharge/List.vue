<template>
  <div class="discharge-list">
    <el-card>
      <template #header>
        <div class="page-header">
          <h3 class="page-title">排放计划列表</h3>
          <el-button
            v-if="userStore.hasRole('DISPATCH', 'SAFETY_HEAD')"
            type="primary"
            :disabled="stopDischargeInfo.has_active_stop"
            @click="$router.push('/discharge/create')"
          >
            <el-icon><Plus /></el-icon>新增计划
          </el-button>
        </div>
      </template>

      <el-alert
        v-if="stopDischargeInfo.has_active_stop"
        :title="`存在未解除的停排指令（${stopDischargeInfo.active_instructions.map(i => i.instruction_no).join(', ')}），禁止新增排放计划！`"
        type="error"
        show-icon
        :closable="false"
        style="margin-bottom: 16px;"
      />

      <div class="search-bar">
        <el-form inline>
          <el-form-item label="状态">
            <el-select v-model="filter.status" placeholder="全部" clearable style="width: 160px;">
              <el-option label="草稿" value="DRAFT" />
              <el-option label="已审批" value="APPROVED" />
              <el-option label="执行中" value="EXECUTING" />
              <el-option label="已完成" value="COMPLETED" />
              <el-option label="已取消" value="CANCELLED" />
              <el-option label="已暂停" value="SUSPENDED" />
            </el-select>
          </el-form-item>
          <el-form-item label="计划日期">
            <el-date-picker
              v-model="filter.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadData">查询</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="list" v-loading="loading">
        <el-table-column prop="plan_no" label="计划编号" width="160" />
        <el-table-column prop="plan_date" label="计划日期" width="120" />
        <el-table-column prop="planned_volume" label="计划量" width="120" />
        <el-table-column prop="actual_volume" label="实际量" width="120">
          <template #default="{ row }">{{ row.actual_volume ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="discharge_location" label="排放地点" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="creator.real_name" label="创建人" width="100" />
        <el-table-column prop="operator.real_name" label="执行人" width="100" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button
                v-if="row.status === 'DRAFT' && userStore.hasRole('SAFETY_HEAD')"
                type="success" link size="small"
                @click="handleApprove(row)"
              >审批</el-button>
              <el-button
                v-if="row.status === 'APPROVED' && userStore.hasRole('DISPATCH')"
                type="primary" link size="small"
                @click="handleExecute(row)"
              >开始执行</el-button>
              <el-button
                v-if="row.status === 'EXECUTING' && userStore.hasRole('DISPATCH', 'SAFETY_HEAD')"
                type="warning" link size="small"
                @click="openComplete(row)"
              >完成</el-button>
              <el-button
                v-if="!['COMPLETED', 'CANCELLED'].includes(row.status) && userStore.hasRole('SAFETY_HEAD')"
                type="danger" link size="small"
                @click="handleCancel(row)"
              >取消</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="completeVisible" title="完成排放" width="420px">
      <el-form label-width="100px">
        <el-form-item label="实际排放量" required>
          <el-input-number v-model="completeVolume" :precision="2" :min="0" :controls="false" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="completeVisible = false">取消</el-button>
        <el-button type="primary" :loading="completeLoading" @click="handleComplete">确认完成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import {
  getDischargePlans, approveDischargePlan, executeDischargePlan,
  completeDischargePlan, cancelDischargePlan
} from '@/api/discharge'
import { checkStopDischarge } from '@/api/instruction'

const userStore = useUserStore()

const loading = ref(false)
const list = ref([])
const stopDischargeInfo = ref({ has_active_stop: false, active_instructions: [] })
const filter = reactive({ status: null, dateRange: null })

const completeVisible = ref(false)
const completeLoading = ref(false)
const completeVolume = ref(0)
const currentPlan = ref(null)

function getStatusText(status) {
  const map = {
    DRAFT: '草稿', APPROVED: '已审批', EXECUTING: '执行中',
    COMPLETED: '已完成', CANCELLED: '已取消', SUSPENDED: '已暂停'
  }
  return map[status] || status
}

function getStatusType(status) {
  const map = {
    DRAFT: 'info', APPROVED: '', EXECUTING: 'warning',
    COMPLETED: 'success', CANCELLED: 'danger', SUSPENDED: 'info'
  }
  return map[status] || 'info'
}

async function loadData() {
  loading.value = true
  try {
    const [plans, stopInfo] = await Promise.all([
      (async () => {
        const params = {}
        if (filter.status) params.status = filter.status
        if (filter.dateRange && filter.dateRange.length === 2) {
          params.plan_date_from = filter.dateRange[0]
          params.plan_date_to = filter.dateRange[1]
        }
        return await getDischargePlans(params)
      })(),
      checkStopDischarge()
    ])
    list.value = plans
    stopDischargeInfo.value = stopInfo
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function handleApprove(row) {
  try {
    await ElMessageBox.confirm('确认审批通过该排放计划？', '提示', { type: 'warning' })
    await approveDischargePlan(row.id, { status: 'APPROVED' })
    ElMessage.success('审批通过')
    await loadData()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

async function handleExecute(row) {
  try {
    await ElMessageBox.confirm('确认开始执行该排放计划？', '提示', { type: 'warning' })
    await executeDischargePlan(row.id)
    ElMessage.success('已开始执行')
    await loadData()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

function openComplete(row) {
  currentPlan.value = row
  completeVolume.value = row.planned_volume
  completeVisible.value = true
}

async function handleComplete() {
  completeLoading.value = true
  try {
    await completeDischargePlan(currentPlan.value.id, completeVolume.value)
    ElMessage.success('排放已完成')
    completeVisible.value = false
    await loadData()
  } catch (e) {
    console.error(e)
  } finally {
    completeLoading.value = false
  }
}

async function handleCancel(row) {
  try {
    await ElMessageBox.confirm('确认取消该排放计划？', '提示', { type: 'warning' })
    await cancelDischargePlan(row.id)
    ElMessage.success('已取消')
    await loadData()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.search-bar { padding: 12px; background: #f5f7fa; border-radius: 4px; margin-bottom: 16px; }
.table-actions { display: flex; gap: 8px; }
</style>
