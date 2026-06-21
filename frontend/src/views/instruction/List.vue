<template>
  <div class="instruction-list">
    <el-card>
      <template #header>
        <div class="page-header">
          <h3 class="page-title">处置指令列表</h3>
          <el-button
            v-if="userStore.hasRole('SAFETY_HEAD')"
            type="primary"
            @click="$router.push('/instruction/create')"
          >
            <el-icon><Plus /></el-icon>签发指令
          </el-button>
        </div>
      </template>

      <div class="search-bar">
        <el-form inline>
          <el-form-item label="类型">
            <el-select v-model="filter.instruction_type" placeholder="全部" clearable style="width: 160px;">
              <el-option label="降级指令" value="DOWNGRADE" />
              <el-option label="停排指令" value="STOP_DISCHARGE" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="filter.status" placeholder="全部" clearable style="width: 140px;">
              <el-option label="草稿" value="DRAFT" />
              <el-option label="已签发" value="ISSUED" />
              <el-option label="执行中" value="EXECUTING" />
              <el-option label="已解除" value="LIFTED" />
              <el-option label="已取消" value="CANCELLED" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadData">查询</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-alert
        v-if="activeStopInstructions.length > 0"
        type="error"
        show-icon
        :closable="false"
        style="margin-bottom: 16px;"
      >
        <template #title>
          <strong>
            注意：当前存在 {{ activeStopInstructions.length }} 条生效中的停排指令，在此期间禁止新增/审批排放计划！
            指令编号：{{ activeStopInstructions.map(i => i.instruction_no).join(', ') }}
          </strong>
        </template>
      </el-alert>

      <el-table :data="list" v-loading="loading">
        <el-table-column prop="instruction_no" label="指令编号" width="160" />
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.instruction_type === 'STOP_DISCHARGE' ? 'danger' : 'warning'" size="small" effect="dark">
              {{ row.instruction_type === 'STOP_DISCHARGE' ? '停排指令' : '降级指令' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="有效期" width="320">
          <template #default="{ row }">
            {{ formatTime(row.effective_from) }} ~ {{ row.effective_to ? formatTime(row.effective_to) : '长期' }}
          </template>
        </el-table-column>
        <el-table-column prop="issuer.real_name" label="签发人" width="100" />
        <el-table-column label="签发时间" width="180">
          <template #default="{ row }">{{ row.issued_at ? formatTime(row.issued_at) : '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button type="primary" link size="small" @click="viewDetail(row)">查看</el-button>
              <el-button
                v-if="row.status === 'DRAFT' && userStore.hasRole('SAFETY_HEAD')"
                type="success" link size="small"
                @click="handleIssue(row)"
              >签发</el-button>
              <el-button
                v-if="row.status === 'ISSUED' && userStore.hasRole('SAFETY_HEAD')"
                type="warning" link size="small"
                @click="openLift(row)"
              >解除</el-button>
              <el-button
                v-if="row.status === 'DRAFT' && userStore.hasRole('SAFETY_HEAD')"
                type="danger" link size="small"
                @click="handleCancel(row)"
              >取消</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="detailVisible" title="指令详情" width="640px">
      <el-descriptions :column="2" border v-if="current">
        <el-descriptions-item label="指令编号">{{ current.instruction_no }}</el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-tag :type="current.instruction_type === 'STOP_DISCHARGE' ? 'danger' : 'warning'">
            {{ current.instruction_type === 'STOP_DISCHARGE' ? '停排指令' : '降级指令' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="标题" :span="2">{{ current.title }}</el-descriptions-item>
        <el-descriptions-item label="内容" :span="2">
          <div style="white-space: pre-wrap;">{{ current.content }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="生效时间">{{ formatTime(current.effective_from) }}</el-descriptions-item>
        <el-descriptions-item label="失效时间">{{ current.effective_to ? formatTime(current.effective_to) : '长期' }}</el-descriptions-item>
        <el-descriptions-item label="签发人">{{ current.issuer?.real_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="签发时间">{{ current.issued_at ? formatTime(current.issued_at) : '-' }}</el-descriptions-item>
        <el-descriptions-item label="解除人">{{ current.lifter?.real_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="解除时间">{{ current.lifted_at ? formatTime(current.lifted_at) : '-' }}</el-descriptions-item>
        <el-descriptions-item v-if="current.lift_reason" label="解除原因" :span="2">{{ current.lift_reason }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="liftVisible" title="解除指令" width="480px">
      <el-form label-width="100px">
        <el-form-item label="解除原因" required>
          <el-input v-model="liftReason" type="textarea" :rows="4" placeholder="请输入解除原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="liftVisible = false">取消</el-button>
        <el-button type="primary" :loading="liftLoading" @click="handleLift">确认解除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { useUserStore } from '@/stores/user'
import { getInstructions, issueInstruction, liftInstruction, cancelInstruction } from '@/api/instruction'

const userStore = useUserStore()

const loading = ref(false)
const list = ref([])
const filter = reactive({ instruction_type: null, status: null })

const detailVisible = ref(false)
const current = ref(null)

const liftVisible = ref(false)
const liftLoading = ref(false)
const liftReason = ref('')

const activeStopInstructions = computed(() => {
  const now = dayjs()
  return list.value.filter(i =>
    i.instruction_type === 'STOP_DISCHARGE'
    && i.status === 'ISSUED'
    && dayjs(i.effective_from).isBefore(now)
    && (!i.effective_to || dayjs(i.effective_to).isAfter(now))
  )
})

function getStatusText(status) {
  const map = { DRAFT: '草稿', ISSUED: '已签发', EXECUTING: '执行中', LIFTED: '已解除', CANCELLED: '已取消' }
  return map[status] || status
}

function getStatusType(status) {
  const map = { DRAFT: 'info', ISSUED: 'success', EXECUTING: 'warning', LIFTED: '', CANCELLED: 'danger' }
  return map[status] || 'info'
}

function formatTime(t) {
  return t ? dayjs(t).format('YYYY-MM-DD HH:mm:ss') : '-'
}

async function loadData() {
  loading.value = true
  try {
    const params = {}
    if (filter.instruction_type) params.instruction_type = filter.instruction_type
    if (filter.status) params.status = filter.status
    const res = await getInstructions(params)
    list.value = res
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function viewDetail(row) {
  current.value = row
  detailVisible.value = true
}

async function handleIssue(row) {
  try {
    await ElMessageBox.confirm('确认签发该指令？', '提示', { type: 'warning' })
    await issueInstruction(row.id)
    ElMessage.success('指令已签发')
    await loadData()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

function openLift(row) {
  current.value = row
  liftReason.value = ''
  liftVisible.value = true
}

async function handleLift() {
  if (!liftReason.value.trim()) {
    ElMessage.warning('请输入解除原因')
    return
  }
  liftLoading.value = true
  try {
    await liftInstruction(current.value.id, { lift_reason: liftReason.value })
    ElMessage.success('指令已解除')
    liftVisible.value = false
    await loadData()
  } catch (e) {
    console.error(e)
  } finally {
    liftLoading.value = false
  }
}

async function handleCancel(row) {
  try {
    await ElMessageBox.confirm('确认取消该指令？', '提示', { type: 'warning' })
    await cancelInstruction(row.id)
    ElMessage.success('指令已取消')
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
