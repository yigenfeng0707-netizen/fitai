import { PropsWithChildren, useReducer } from 'react'
import { useLaunch } from '@tarojs/taro'
import { UserContext, userReducer, initialUserState } from '@/store/user'
import { AppContext, appReducer, initialAppState } from '@/store/app'
import { getToken, getUserInfo, getMemberInfo } from '@/utils/storage'
import type { UserInfo, MemberInfo } from '@/types'
import './app.scss'

function App({ children }: PropsWithChildren) {
  const [userState, userDispatch] = useReducer(userReducer, initialUserState)
  const [appState, appDispatch] = useReducer(appReducer, initialAppState)

  useLaunch(async () => {
    console.log('FitAI 小程序启动')
    try {
      const token = getToken()
      if (token) {
        const userInfo = await getUserInfo<UserInfo>().catch(() => null)
        const memberInfo = await getMemberInfo<MemberInfo>().catch(() => null)
        userDispatch({
          type: 'LOGIN',
          payload: { token, userInfo, memberInfo },
        })
      }
    } catch (error) {
      console.error('Failed to hydrate user state', error)
    }
  })

  return (
    <UserContext.Provider value={{ state: userState, dispatch: userDispatch }}>
      <AppContext.Provider value={{ state: appState, dispatch: appDispatch }}>
        {children}
      </AppContext.Provider>
    </UserContext.Provider>
  )
}

export default App
