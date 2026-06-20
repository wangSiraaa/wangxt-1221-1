<template>
  <div class="discharge-create">
    <el-page-header @back="$router.back()" content="返回列表" style="margin-bottom: 16px;" />

    <el-card>
      <template #header>
        <h3 class="page-title">新增排放计划</h3>
      </template>

      <el-alert
        v-if="stopDischargeInfo.has_active_stop"
        :title="`存在未解除的停排指令（${stopDischargeInfo.active_instructions.map(i => i.instruction_no).join(', ')}），禁止新增排放计划！`"
        type="error"
        show-icon
        :closable="false"
        style="margin-bottom: 16px;"
      />

      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px" :disabled="stopDischargeInfo.has_active_stop">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="计划日期" prop="plan_date">
              <el-date-picker
                v-model="form.plan_date"
                type="date"
                placeholder="选择计划日期"
                style="width: 100%;"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计划排放量(m³)" prop="planned_volume">
              <el-input-number
                v-model="form.planned_volume"
                :precision="2"
                :min="0"
                :controls="false"
                style="width: 100%;"
                placeholder="请输入计划排放量"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="排放地点">
          <el-input v-model="form.discharge_location" placeholder="请输入排放地点" />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="4" placeholder="请输入备注" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { createDischargePlan } from '@/api/discharge'
import { checkStopDischarge } from '@/api/instruction'

const router = useRouter()

const formRef = ref(null)
const saving = ref(false)
const stopDischargeInfo = ref({ has_active_stop: false, active_instructions: [] })

const form = reactive({
  plan_date: dayjs().format('YYYY-MM-DD'),
  planned_volume: null,
  discharge_location: '',
  remark: ''
})

const rules = {
  plan_date: [{ required: true, message: '请选择计划日期', trigger: 'change' }],
  planned_volume: [{ required: true, message: '请输入计划排放量', trigger: 'blur' }]
}

async function loadStopCheck() {
  try {
    stopDischargeInfo.value = await checkStopDischarge()
  } catch (e) {
    console.error(e)
  }
}

async function handleSave() {
  try {
    await formRef.value.validate()
    saving.value = true
    await createDischargePlan(form)
    ElMessage.success('排放计划已创建，等待审批')
    router.push('/discharge/list')
  } catch (e) {
    if (e !== false) console.error(e)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadStopCheck()
})
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin: 0; }
</style>
