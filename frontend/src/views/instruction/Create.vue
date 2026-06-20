<template>
  <div class="instruction-create">
    <el-page-header @back="$router.back()" content="返回列表" style="margin-bottom: 16px;" />

    <el-card>
      <template #header>
        <h3 class="page-title">签发处置指令</h3>
      </template>

      <el-alert
        v-if="stopDischargeInfo.has_active_stop"
        :title="`当前已存在生效的停排指令：${stopDischargeInfo.active_instructions.map(i => i.instruction_no).join(', ')}`"
        type="warning"
        show-icon
        :closable="false"
        style="margin-bottom: 16px;"
      />

      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="指令类型" prop="instruction_type">
              <el-radio-group v-model="form.instruction_type">
                <el-radio label="DOWNGRADE">
                  <el-tag type="warning">降级指令</el-tag>
                </el-radio>
                <el-radio label="STOP_DISCHARGE">
                  <el-tag type="danger" effect="dark">停排指令</el-tag>
                </el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="指令标题" prop="title">
              <el-input v-model="form.title" placeholder="请输入指令标题" maxlength="200" show-word-limit />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="生效时间" prop="effective_from">
              <el-date-picker
                v-model="form.effective_from"
                type="datetime"
                placeholder="选择生效时间"
                style="width: 100%;"
                value-format="YYYY-MM-DD HH:mm:ss"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="失效时间">
              <el-date-picker
                v-model="form.effective_to"
                type="datetime"
                placeholder="留空表示长期有效"
                style="width: 100%;"
                value-format="YYYY-MM-DD HH:mm:ss"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="关联异常">
          <el-select v-model="form.related_anomaly_ids" multiple filterable placeholder="选择关联的异常记录" style="width: 100%;">
            <el-option
              v-for="a in openAnomalies"
              :key="a.id"
              :label="`#${a.id} [${getAlertText(a.alert_level)}] ${a.point?.point_name} - ${a.trigger_value}/${a.threshold_value}`"
              :value="a.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="指令内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="8" placeholder="请详细描述处置指令内容、要求和措施" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave('draft')">保存草稿</el-button>
          <el-button type="success" :loading="issuing" @click="handleSave('issue')">保存并签发</el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { checkStopDischarge, createInstruction, issueInstruction } from '@/api/instruction'
import { getAnomalyRecords } from '@/api/anomaly'

const route = useRoute()
const router = useRouter()

const formRef = ref(null)
const saving = ref(false)
const issuing = ref(false)
const openAnomalies = ref([])
const stopDischargeInfo = ref({ has_active_stop: false, active_instructions: [] })

const form = reactive({
  instruction_type: 'DOWNGRADE',
  title: '',
  content: '',
  related_anomaly_ids: [],
  effective_from: dayjs().format('YYYY-MM-DD HH:mm:ss'),
  effective_to: null
})

const rules = {
  instruction_type: [{ required: true, message: '请选择指令类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入指令标题', trigger: 'blur' }],
  effective_from: [{ required: true, message: '请选择生效时间', trigger: 'change' }],
  content: [{ required: true, message: '请输入指令内容', trigger: 'blur' }]
}

function getAlertText(level) {
  const map = { WARNING: '预警', DANGER: '危险', CRITICAL: '严重', NORMAL: '正常' }
  return map[level] || '未知'
}

async function loadData() {
  try {
    const [anomalies, stopInfo] = await Promise.all([
      getAnomalyRecords({ status: 'OPEN' }),
      checkStopDischarge()
    ])
    openAnomalies.value = anomalies
    stopDischargeInfo.value = stopInfo

    if (route.query.anomaly_id) {
      const id = parseInt(route.query.anomaly_id)
      if (!form.related_anomaly_ids.includes(id)) {
        form.related_anomaly_ids.push(id)
      }
    }
  } catch (e) {
    console.error(e)
  }
}

async function handleSave(mode) {
  try {
    await formRef.value.validate()
    if (mode === 'draft') {
      saving.value = true
    } else {
      issuing.value = true
    }

    const payload = {
      instruction_type: form.instruction_type,
      title: form.title,
      content: form.content,
      related_anomaly_ids: form.related_anomaly_ids.length > 0 ? form.related_anomaly_ids : null,
      effective_from: form.effective_from,
      effective_to: form.effective_to || null
    }

    const created = await createInstruction(payload)

    if (mode === 'issue') {
      await issueInstruction(created.id)
      ElMessage.success('指令已签发')
    } else {
      ElMessage.success('草稿已保存')
    }

    router.push('/instruction/list')
  } catch (e) {
    if (e !== false) console.error(e)
  } finally {
    saving.value = false
    issuing.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin: 0; }
</style>
