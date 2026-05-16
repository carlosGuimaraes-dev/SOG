import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react'
import api from './api'
import { ENDPOINTS } from './endpoints'

interface User {
  username: string
}

interface AuthContextType {
  user: User | null
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    api.get(ENDPOINTS.ME)
      .then((res) => {
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
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
