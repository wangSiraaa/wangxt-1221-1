import { defineStore } from 'pinia'
import { login as loginApi, getMe } from '@/api/auth'
import { setToken, getToken, removeToken, setUser, getUser, clearAuth } from '@/utils/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: getToken() || '',
    user: getUser() || null
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    roleCode: (state) => state.user?.role?.role_code || '',
    roleName: (state) => state.user?.role?.role_name || '',
    realName: (state) => state.user?.real_name || ''
  },

  actions: {
    async login(username, password) {
      const res = await loginApi(username, password)
      this.token = res.access_token
      setToken(res.access_token)
      await this.fetchUser()
      return res
    },

    async fetchUser() {
      const res = await getMe()
      this.user = res
      setUser(res)
      return res
    },

    logout() {
      this.token = ''
      this.user = null
      clearAuth()
    },

    hasRole(...roleCodes) {
      if (!this.user?.role) return false
      return roleCodes.includes(this.user.role.role_code)
    }
  }
})
