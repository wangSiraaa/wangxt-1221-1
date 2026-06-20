const TOKEN_KEY = 'tailings_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  return localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken() {
  return localStorage.removeItem(TOKEN_KEY)
}

const USER_KEY = 'tailings_user'

export function getUser() {
  const user = localStorage.getItem(USER_KEY)
  return user ? JSON.parse(user) : null
}

export function setUser(user) {
  return localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function removeUser() {
  return localStorage.removeItem(USER_KEY)
}

export function clearAuth() {
  removeToken()
  removeUser()
}
