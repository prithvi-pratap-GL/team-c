/* eslint-disable react-refresh/only-export-components */
import { createContext, useState } from 'react'
import type { ReactNode } from 'react'
import type { User, AuthToken } from '../types'

export interface AuthContextType {
  user: User | null
  token: AuthToken | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setUser: (user: User | null) => void
  setToken: (token: AuthToken | null) => void
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<AuthToken | null>(null)

  const login = async (email: string, password: string) => {
    console.log('Login attempt:', { email, password })
  }

  const logout = () => {
    setUser(null)
    setToken(null)
  }

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!user && !!token,
    login,
    logout,
    setUser,
    setToken,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
