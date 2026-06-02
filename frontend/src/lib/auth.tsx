import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react'
import api from './api'
import { ENDPOINTS } from './endpoints'

interface User {
  username: string
}

interface AuthContextType {
  user: User | null
  authRequired: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [authRequired, setAuthRequired] = useState(true)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    api.get(ENDPOINTS.ME)
      .then((res) => {
        setAuthRequired(res.data?.auth_required !== false)
        if (res.data?.username) {
          setUser({ username: res.data.username })
        }
      })
      .catch(() => {
        setUser(null)
      })
      .finally(() => {
        setIsLoading(false)
      })
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    setIsLoading(true)
    try {
      await api.post(ENDPOINTS.LOGIN, { username, password })
      const me = await api.get(ENDPOINTS.ME)
      setAuthRequired(me.data?.auth_required !== false)
      setUser({ username: me.data.username })
    } finally {
      setIsLoading(false)
    }
  }, [])

  const logout = useCallback(async () => {
    try {
      await api.post(ENDPOINTS.LOGOUT)
    } catch {
      // Ignora erro no logout — sessão já pode ter expirado
    } finally {
      setUser(null)
    }
  }, [])

  return (
    <AuthContext.Provider value={{ user, authRequired, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
