import { createContext, useContext, useReducer } from 'react'
import type { AppState } from '@/types'

/** 应用初始状态 */
export const initialAppState: AppState = {
  loading: false,
  currentStore: null,
}

/** App Action 类型 */
export type AppAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_STORE'; payload: AppState['currentStore'] }

/** App Reducer */
export function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload }
    case 'SET_STORE':
      return { ...state, currentStore: action.payload }
    default:
      return state
  }
}

/** App Context */
export const AppContext = createContext<{
  state: AppState
  dispatch: React.Dispatch<AppAction>
}>({
  state: initialAppState,
  dispatch: () => {},
})

/** 使用 App 状态的 Hook */
export function useApp() {
  return useContext(AppContext)
}
