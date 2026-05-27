import client from './client'
import type { OrganizationInfo, UserManageInfo, RoleInfo, ListResponse } from './types'

export interface OrganizationUpdate {
  name?: string
  contact_name?: string
  contact_phone?: string
  contact_email?: string
  settings?: Record<string, unknown>
}

export interface UserCreateByAdmin {
  username: string
  password: string
  role: string
}

export interface UserUpdateByAdmin {
  role?: string
  is_active?: boolean
  password?: string
}

export const settingsApi = {
  getOrganization: async (): Promise<OrganizationInfo> => {
    const response = await client.get('/api/v1/settings/organization')
    return response.data
  },

  updateOrganization: async (data: OrganizationUpdate): Promise<OrganizationInfo> => {
    const response = await client.put('/api/v1/settings/organization', data)
    return response.data
  },

  listUsers: async (params?: { skip?: number; limit?: number }): Promise<ListResponse<UserManageInfo>> => {
    const response = await client.get('/api/v1/settings/users', { params })
    return response.data
  },

  createUser: async (data: UserCreateByAdmin): Promise<UserManageInfo> => {
    const response = await client.post('/api/v1/settings/users', data)
    return response.data
  },

  updateUser: async (userId: number, data: UserUpdateByAdmin): Promise<UserManageInfo> => {
    const response = await client.put(`/api/v1/settings/users/${userId}`, data)
    return response.data
  },

  listRoles: async (): Promise<RoleInfo[]> => {
    const response = await client.get('/api/v1/settings/roles')
    return response.data
  },
}

export default settingsApi
