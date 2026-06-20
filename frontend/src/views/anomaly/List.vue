<template>
  <div class="anomaly-list">
    <el-card>
      <template #header>
        <div class="page-header">
          <h3 class="page-title">异常预警列表</h3>
        </div>
      </template>

      <div class="search-bar">
        <el-form inline>
          <el-form-item label="状态">
            <el-select v-model="filter.status" placeholder="全部" clearable style="width: 140px;">
              <el-option label="待处理" value="OPEN" />
              <el-option label="已关闭" value="CLOSED" />
            </el-select>
          </el-form-item>
          <el-form-item label="级别">
            <el-select v-model="filter.alert_level" placeholder="全部" clearable style="width: 140px;">
              <el-option label="预警" value="WARNING" />
              <el-option label="危险" value="DANGER" />
              <el-option label="严重(连续超阈值)" value="CRITICAL" />
            </el-select>
          </el-form-item>
          <el-form-item label="是否确认">
            <el-select v-model="filter.is_confirmed" placeholder="全部" clearable style="width: 140px;">
              <el-option label="已确认" :value="true" />
              <el-option label="未确认" :value="false" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadData">查询</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-alert
        v-if="hasCriticalUnconfirmed"
        type="error"
        show-icon
        :closable="false"
        style="margin-bottom: 16px;"
      >
        <template #title>
          <strong>重要：存在连续两次超阈值的严重异常，已升级为严重级别，请立即处理！</strong>
        </template>
      </el-alert>

      <el-table :data="list" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="监测点" min-width="180">
          <template #default="{ row }">
            {{ row.point?.point_code }} - {{ row.point?.point_name }}
          </template>
        </el-table-column>
        <el-table-column label="级别" width="160">
          <template #default="{ row }">
            <el-tag :type="getAlertType(row.alert_level)" size="small" effect="dark">
              {{ getAlertText(row.alert_level) }}
              <el-icon v-if="row.alert_level === 'CRITICAL'"><WarningFilled /></el-icon>
            </el-tag>
            <el-tag v-if="row.consecutive_count >= 2" type="danger" size="small" style="margin-left: 4px;">
              连续{{ row.consecutive_count }}次
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="触发值/阈值" width="140">
          <template #default="{ row }">
            {{ row.trigger_value }} / {{ row.threshold_value }}
          </template>
        </el-table-column>
        <el-table-column label="是否确认" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_confirmed" type="success" size="small">已确认</el-tag>
            <el-tag v-else type="warning" size="small">未确认</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="处理状态" width="100">
          <template #default="{ row }">
            {{ row.status === 'OPEN' ? '待处理' : '已关闭' }}
          </template>
        </el-table-column>
        <el-table-column label="发生时间" width="180">
          <template #default="{ row }">{{ formatTime(row.start_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button type="primary" link size="small" @click="goDetail(row)">详情</el-button>
              <el-button
                v-if="!row.is_confirmed && userStore.hasRole('GEOLOGIST', 'SAFETY_HEAD')"
                type="success" link size="small"
                @click="openConfirm(row)"
              >确认异常</el-button>
              <el-button
                v-if="row.status === 'OPEN' && userStore.hasRole('GEOLOGIST', 'SAFETY_HEAD')"
                type="danger" link size="small"
                @click="openClose(row)"
              >关闭</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="confirmDialogVisible" title="确认异常趋势" width="520px">
      <el-form :model="confirmForm" label-width="100px">
        <el-form-item label="异常级别">
          <el-tag :type="getAlertType(currentAnomaly?.alert_level)">
            {{ getAlertText(currentAnomaly?.alert_level) }}
          </el-tag>
        </el-form-item>
        <el-form-item label="触发值">
          <span>{{ currentAnomaly?.trigger_value }} / 阈值: {{ currentAnomaly?.threshold_value }}</span>
        </el-form-item>
        <el-form-item label="连续超阈值次数">
          <span style="color: #f56c6c; font-weight: 600;">{{ currentAnomaly?.consecutive_count }} 次</span>
        </el-form-item>
        <el-form-item label="确认说明" required>
          <el-input v-model="confirmForm.confirmation_note" type="textarea" :rows="4" placeholder="请输入地测工程师异常趋势分析和确认意见" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="confirmDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="confirmLoading" @click="handleConfirm">确认提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="closeDialogVisible" title="关闭异常" width="480px">
      <el-form label-width="100px">
        <el-form-item label="关闭说明" required>
          <el-input v-model="closeNote" type="textarea" :rows="4" placeholder="请输入关闭原因说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="closeLoading" @click="handleClose">关闭异常</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { WarningFilled } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { useUserStore } from '@/stores/user'
import { getAnomalyRecords, confirmAnomaly, closeAnomaly } from '@/api/anomaly'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const list = ref([])
const filter = reactive({
  status: null,
  alert_level: null,
  is_confirmed: null
})

const confirmDialogVisible = ref(false)
const confirmLoading = ref(false)
const currentAnomaly = ref(null)
const confirmForm = reactive({ confirmation_note: '', is_confirmed: true })

const closeDialogVisible = ref(false)
const closeLoading = ref(false)
const closeNote = ref('')

const hasCriticalUnconfirmed = computed(() => {
  return list.value.some(a => a.alert_level === 'CRITICAL' && !a.is_confirmed)
})

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

async function loadData() {
  loading.value = true
  try {
    const params = {}
    if (filter.status) params.status = filter.status
    if (filter.alert_level) params.alert_level = filter.alert_level
    if (filter.is_confirmed != null) params.is_confirmed = filter.is_confirmed
    const res = await getAnomalyRecords(params)
    list.value = res
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function goDetail(row) {
  router.push(`/anomaly/${row.id}`)
}

function openConfirm(row) {
  currentAnomaly.value = row
  confirmForm.confirmation_note = ''
  confirmDialogVisible.value = true
}

async function handleConfirm() {
  if (!confirmForm.confirmation_note.trim()) {
    ElMessage.warning('请输入确认说明')
    return
  }
  confirmLoading.value = true
  try {
    await confirmAnomaly(currentAnomaly.value.id, confirmForm)
    ElMessage.success('异常确认成功')
    confirmDialogVisible.value = false
    await loadData()
  } catch (e) {
    console.error(e)
  } finally {
    confirmLoading.value = false
  }
}

function openClose(row) {
  currentAnomaly.value = row
  closeNote.value = ''
  closeDialogVisible.value = true
}

async function handleClose() {
  if (!closeNote.value.trim()) {
    ElMessage.warning('请输入关闭说明')
    return
  }
  closeLoading.value = true
  try {
    await closeAnomaly(currentAnomaly.value.id, closeNote.value)
    ElMessage.success('异常已关闭')
    closeDialogVisible.value = false
    await loadData()
  } catch (e) {
    console.error(e)
  } finally {
    closeLoading.value = false
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
