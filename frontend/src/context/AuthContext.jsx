import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authApi } from '../utils/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('mb_user')) } catch { return null }
  })
  const [loading, setLoading] = useState(true)

  const fetchMe = useCallback(async () => {
    const token = localStorage.getItem('mb_token')
    if (!token) { setLoading(false); return }
    try {
      const me = await authApi.me()
      setUser(me)
      localStorage.setItem('mb_user', JSON.stringify(me))
    } catch {
      localStorage.removeItem('mb_token')
      localStorage.removeItem('mb_user')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchMe() }, [fetchMe])

  const login = async (email, password) => {
    const data = await authApi.login(email, password)
    localStorage.setItem('mb_token', data.access_token)
    localStorage.setItem('mb_user', JSON.stringify(data))
    setUser(data)
    return data
  }

  const register = async (email, full_name, password, otp) => {
    const data = await authApi.register(email, full_name, password, otp)
    localStorage.setItem('mb_token', data.access_token)
    localStorage.setItem('mb_user', JSON.stringify(data))
    setUser(data)
    return data
  }

  const logout = () => {
    localStorage.removeItem('mb_token')
    localStorage.removeItem('mb_user')
    setUser(null)
  }

  const refreshUser = () => fetchMe()

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)

