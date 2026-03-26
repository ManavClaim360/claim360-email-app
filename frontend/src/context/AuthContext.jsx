import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authApi } from '../utils/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { 
      const stored = JSON.parse(localStorage.getItem('mb_user'))
      console.log('✓ User from localStorage:', stored?.email || 'none')
      return stored
    } catch (e) { 
      console.log('No stored user found')
      return null 
    }
  })
  const [loading, setLoading] = useState(true)

  const fetchMe = useCallback(async () => {
    const token = localStorage.getItem('mb_token')
    console.log('🔄 fetchMe: checking token...')
    if (!token) { 
      console.log('No token found, user is logged out')
      setLoading(false)
      return 
    }
    try {
      console.log('📡 Calling /api/auth/me...')
      const me = await authApi.me()
      console.log('✓ Got user from API:', me.email)
      setUser(me)
      localStorage.setItem('mb_user', JSON.stringify(me))
    } catch (err) {
      console.error('❌ Failed to fetch user:', err.message)
      localStorage.removeItem('mb_token')
      localStorage.removeItem('mb_user')
      setUser(null)
    } finally {
      console.log('✓ Auth initialization complete')
      setLoading(false)
    }
  }, [])

  useEffect(() => { 
    console.log('⚡ AuthProvider mounted, running fetchMe')
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
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
