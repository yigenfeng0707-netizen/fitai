import { createContext, useContext } from 'react'
import type { UserState, UserAction } from '@/types'

/** 用户初始状态 */
export const initialUserState: UserState = {
  token: '',
  userInfo: null,
  memberInfo: null,
  isLoggedIn: false,
}

/** 用户 Reducer */
export function userReducer(state: UserState, action: UserAction): UserState {
  switch (action.type) {
    case 'LOGIN':
      return {
        token: action.payload.token,
        userInfo: action.payload.userInfo,
        memberInfo: action.payload.memberInfo || null,
        isLoggedIn: true,
      }
    case 'LOGOUT':
      return {
        ...initialUserState,
      }
    case 'UPDATE_PROFILE':
      return {
        ...state,
        userInfo: state.userInfo
          ? { ...state.userInfo, ...action.payload }
          : state.userInfo,
      }
    case 'UPDATE_MEMBER':
      return {
        ...state,
        memberInfo: action.payload,
      }
    case 'SET_TOKEN':
      return {
        ...state,
        token: action.payload,
        isLoggedIn: !!action.payload,
      }
    default:
      return state
  }
}

/** 用户 Context */
export const UserContext = createContext<{
  state: UserState
  dispatch: React.Dispatch<UserAction>
}>({
  state: initialUserState,
  dispatch: () => {},
})

/** 使用用户状态的 Hook */
export function useUser() {
  return useContext(UserContext)
}
