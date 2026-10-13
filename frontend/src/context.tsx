import { createContext, useContext, useEffect, useMemo, useState, ReactNode } from 'react'
import { api } from './api'
type AuthValue = { user: any; login:(username:string,password:string)=>Promise<void>; register:(data:any)=>Promise<void>; logout:()=>void; refreshProfile:()=>Promise<void> }
const AuthContext = createContext<AuthValue | null>(null)
export function AuthProvider({children}:{children:ReactNode}) {
  const [user,setUser] = useState<any>(null)
  const refreshProfile = async () => { if (!localStorage.getItem('access')) {setUser(null); return} try {setUser((await api.get('/profile/')).data)} catch {setUser(null)} }
  useEffect(()=>{ void refreshProfile() },[])
  const login = async (username:string,password:string) => {
    const {data} = await api.post('/auth/token/',{username,password})
    localStorage.setItem('access',data.access); localStorage.setItem('refresh',data.refresh); await refreshProfile()
  }
  const register = async (data:any) => { await api.post('/auth/register/',data); await login(data.username,data.password) }
  const logout = () => {localStorage.removeItem('access');localStorage.removeItem('refresh');setUser(null)}
  const value = useMemo(()=>({user,login,register,logout,refreshProfile}),[user])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
export const useAuth = () => { const ctx=useContext(AuthContext); if(!ctx) throw new Error('AuthProvider missing'); return ctx }
