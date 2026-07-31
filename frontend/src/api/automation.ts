import client from './client'
import type { ListResponse } from './types'

export interface AutomationRule {
  id: number
  organization_id: number
  name: string
  description: string | null
  trigger_type: string
  trigger_config: Record<string, unknown> | null
  action_type: string
  action_config: Record<string, unknown> | null
  is_active: boolean
  execution_count: number
  last_executed_at: string | null
  created_at: string
  updated_at: string
}

export interface AutomationRuleCreate {
  name: string
  description?: string
  trigger_type: string
  trigger_config?: Record<string, unknown>
  action_type?: string
  action_config?: Record<string, unknown>
}

export interface AutomationRuleUpdate {
  name?: string
  description?: string
  trigger_type?: string
  trigger_config?: Record<string, unknown>
  action_type?: string
  action_config?: Record<string, unknown>
  is_active?: boolean
}

export interface AutomationLog {
  id: number
  rule_id: number
  trigger_entity_type: string
  trigger_entity_id: number | null
  action_result: Record<string, unknown> | null
  status: string
  error_message: string | null
  created_at: string
}

export const automationApi = {
  getList: async (params?: { skip?: number; limit?: number; trigger_type?: string }): Promise<ListResponse<AutomationRule>> => {
    const response = await client.get('/api/v1/automations/', { params })
    return response.data
  },

  get: async (id: number): Promise<AutomationRule> => {
    const response = await client.get(`/api/v1/automations/${id}`)
    return response.data
  },

  create: async (data: AutomationRuleCreate): Promise<AutomationRule> => {
    const response = await client.post('/api/v1/automations/', data)
    return response.data
  },

  update: async (id: number, data: AutomationRuleUpdate): Promise<AutomationRule> => {
    const response = await client.put(`/api/v1/automations/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/api/v1/automations/${id}`)
  },

  toggle: async (id: number): Promise<AutomationRule> => {
    const response = await client.post(`/api/v1/automations/${id}/toggle`)
    return response.data
  },

  getLogs: async (params?: { rule_id?: number; skip?: number; limit?: number }): Promise<ListResponse<AutomationLog>> => {
    const response = await client.get('/api/v1/automations/logs/list', { params })
    return response.data
  },

  checkTimeTriggers: async (): Promise<void> => {
    await client.post('/api/v1/automations/check-time-triggers')
  },
}
