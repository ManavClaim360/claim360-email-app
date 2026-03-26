import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authApi } from '../utils/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('mb_user')) } catch { return null }
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchMe = useCallback(async () => {
    const token = localStorage.getItem('mb_token')
    if (!token) { 
      console.log('[AUTH] No token, user is logged out')
      setLoading(false)
      return 
    }
    
    console.log('[AUTH] Fetching user info from /api/auth/me')
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 5000) // 5 second timeout
      
      const me = await authApi.me()
      clearTimeout(timeout)
      console.log('[AUTH] ✓ Got user:', me.email)
      setUser(me)
      localStorage.setItem('mb_user', JSON.stringify(me))
      setError(null)
    } catch (err) {
      console.error('[AUTH] ❌ Failed to fetch user:', err.message)
      setError(err.message)
      localStorage.removeItem('mb_token')
      localStorage.removeItem('mb_user')
      setUser(null)
    } finally {
      console.log('[AUTH] Done loading')
      setLoading(false)
    }
  }, [])

  useEffect(() => { 
    console.log('[AUTH] Provider mounted, running fetchMe')
    fetchMe() 
  }, [fetchMe])

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
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser, error }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)

