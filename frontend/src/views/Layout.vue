<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon size="28" color="#409EFF"><Monitor /></el-icon>
        <span class="logo-text">尾矿库监测</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="sidebar-menu"
        background-color="#001529"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>监测概览</span>
        </el-menu-item>

        <el-sub-menu index="monitor">
          <template #title>
            <el-icon><TrendCharts /></el-icon>
            <span>监测管理</span>
          </template>
          <el-menu-item v-if="userStore.hasRole('DISPATCH', 'GEOLOGIST')" index="/monitor/data-entry">
            <el-icon><Edit /></el-icon>
            <span>数据录入</span>
          </el-menu-item>
          <el-menu-item index="/monitor/chart">
            <el-icon><LineChart /></el-icon>
            <span>监测曲线</span>
          </el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="anomaly">
          <template #title>
            <el-icon><Warning /></el-icon>
            <span>异常预警</span>
          </template>
          <el-menu-item index="/anomaly/list">
            <el-icon><List /></el-icon>
            <span>异常列表</span>
          </el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="instruction">
          <template #title>
            <el-icon><Document /></el-icon>
            <span>处置指令</span>
          </template>
          <el-menu-item index="/instruction/list">
            <el-icon><Tickets /></el-icon>
            <span>指令列表</span>
          </el-menu-item>
          <el-menu-item v-if="userStore.hasRole('SAFETY_HEAD')" index="/instruction/create">
            <el-icon><Plus /></el-icon>
            <span>签发指令</span>
          </el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="discharge">
          <template #title>
            <el-icon><Calendar /></el-icon>
            <span>排放计划</span>
          </template>
          <el-menu-item index="/discharge/list">
            <el-icon><List /></el-icon>
            <span>计划列表</span>
          </el-menu-item>
          <el-menu-item v-if="userStore.hasRole('DISPATCH', 'SAFETY_HEAD')" index="/discharge/create">
            <el-icon><Plus /></el-icon>
            <span>新增计划</span>
          </el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/disposal/list">
          <el-icon><Notebook /></el-icon>
          <span>处置记录</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-title">
          {{ currentTitle }}
        </div>
        <div class="header-user">
          <el-badge :value="alertSummary.unconfirmed_count" :hidden="alertSummary.unconfirmed_count === 0" class="alert-badge">
            <el-button type="primary" link @click="$router.push('/anomaly/list')">
              <el-icon><Bell /></el-icon>
              <span style="margin-left: 4px;">预警</span>
            </el-button>
          </el-badge>
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><UserFilled /></el-icon>
              <span>{{ userStore.realName }}</span>
              <el-tag size="small" type="info" style="margin-left: 8px;">{{ userStore.roleName }}</el-tag>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getAlertSummary } from '@/api/monitor'
import {
  Monitor, DataAnalysis, TrendCharts, Edit, LineChart, Warning, List,
  Document, Tickets, Plus, Calendar, Notebook, Bell, UserFilled,
  ArrowDown, SwitchButton
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta.title || '矿山尾矿库安全监测系统')

const alertSummary = ref({
  warning_count: 0,
  danger_count: 0,
  critical_count: 0,
  unconfirmed_count: 0
})

async function loadAlertSummary() {
  try {
    const res = await getAlertSummary()
    alertSummary.value = res
  } catch (e) {
    console.error(e)
  }
}

function handleCommand(command) {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  }
}

onMounted(() => {
  loadAlertSummary()
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background: #001529;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-bottom: 1px solid #1f2d3d;
}

.logo-text {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}

.sidebar-menu {
  border-right: none;
}

.sidebar-menu :deep(.el-menu-item),
.sidebar-menu :deep(.el-sub-menu__title) {
  height: 48px;
  line-height: 48px;
}

.header {
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.header-user {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #606266;
}

.main-content {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

.alert-badge :deep(.el-badge__content) {
  top: 4px;
}
</style>
