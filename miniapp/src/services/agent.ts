/**
 * Agent Service - FitAI Agent chat API client.
 * 
 * Provides natural language interaction with the FitAI Agent,
 * supporting three personas: health_consultant, studio_ops, growth_engine.
 */
import { post, get } from './request'

/** Agent persona type */
export type AgentPersona = 'health_consultant' | 'studio_ops' | 'growth_engine'

/** Tool call record */
export interface ToolCall {
  tool: string
  args: Record<string, any>
  result: any
  timestamp: string
}

/** Agent chat response */
export interface AgentChatResponse {
  answer: string
  tool_calls: ToolCall[]
  iterations: number
  persona: string
}

/** Agent chat request */
export interface AgentChatRequest {
  message: string
  member_id?: number
  persona?: AgentPersona
  context?: Record<string, any>
}

/** Persona info */
export interface PersonaInfo {
  id: string
  name: string
  name_cn: string
  description: string
  tools: string[]
}

/**
 * Send a message to the FitAI Agent and get a response.
 */
export async function chatWithAgent(req: AgentChatRequest): Promise<AgentChatResponse> {
  return post<AgentChatResponse>('/api/v1/agent/chat', req, {
    showLoading: false,
    showError: true,
  })
}

/**
 * List all available Agent personas.
 */
export async function getPersonas(): Promise<PersonaInfo[]> {
  const res = await get<{ personas: PersonaInfo[] }>('/api/v1/agent/personas')
  return res.personas
}

/**
 * Check Agent service health.
 */
export async function checkAgentHealth(): Promise<{
  configured: boolean
  model: string
  max_iterations: number
  reflection_enabled: boolean
  personas: string[]
}> {
  return get('/api/v1/agent/health')
}

/**
 * Quick suggestions for each persona.
 * Used to pre-fill the chat input with example prompts.
 */
export const QUICK_SUGGESTIONS: Record<AgentPersona, string[]> = {
  health_consultant: [
    '分析我最近的体测数据趋势',
    '本周有哪些适合我的课程？',
    '我的出勤率怎么样？',
    '帮我预约一节瑜伽课',
  ],
  studio_ops: [
    '本周营业数据概览',
    '教练绩效对比分析',
    '哪些会员超过30天没来了？',
    '本月营收有什么异常？',
  ],
  growth_engine: [
    '设计一个沉睡会员唤醒方案',
    '哪些会员卡即将到期？',
    '找出最有升级潜力的会员',
    '分析高价值会员的消费模式',
  ],
}
