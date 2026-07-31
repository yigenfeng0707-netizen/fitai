import { View, Text, ScrollView, Input, ScrollViewProps } from '@tarojs/components'
import { useState, useRef, useCallback } from 'react'
import Taro from '@tarojs/taro'
import NavBar from '@/components/NavBar'
import { chatWithAgent, QUICK_SUGGESTIONS, type AgentPersona, type ToolCall } from '@/services/agent'
import { isLoggedIn } from '@/services/auth'
import './index.scss'

/** Chat message type */
interface ChatMessage {
  id: string
  role: 'user' | 'agent'
  content: string
  toolCalls?: ToolCall[]
  iterations?: number
  persona?: string
  timestamp: number
}

/** Persona display config */
const PERSONA_CONFIG: Record<AgentPersona, { label: string; icon: string; color: string }> = {
  health_consultant: { label: 'Health Consultant', icon: '\ue60a', color: '#7c5cfc' },
  studio_ops: { label: 'Studio Ops', icon: '\ue60e', color: '#3b82f6' },
  growth_engine: { label: 'Growth Engine', icon: '\ue60f', color: '#10b981' },
}

export default function AgentPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [persona, setPersona] = useState<AgentPersona>('health_consultant')
  const [showPersonaPicker, setShowPersonaPicker] = useState(false)
  const [showTools, setShowTools] = useState<Record<string, boolean>>({})
  const scrollRef = useRef<string>('')

  // Check login on show
  Taro.useDidShow(() => {
    if (!isLoggedIn()) {
      Taro.redirectTo({ url: '/pages/login/index' })
    }
  })

  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      scrollRef.current = `msg-${Date.now()}`
      // @ts-ignore
      Taro.pageScrollTo?.({ scrollTop: 99999, duration: 300 })
    }, 100)
  }, [])

  const handleSend = async (message?: string) => {
    const text = (message || input).trim()
    if (!text || loading) return

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: Date.now(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)
    scrollToBottom()

    try {
      const res = await chatWithAgent({
        message: text,
        persona,
      })

      const agentMsg: ChatMessage = {
        id: `a-${Date.now()}`,
        role: 'agent',
        content: res.answer,
        toolCalls: res.tool_calls,
        iterations: res.iterations,
        persona: res.persona,
        timestamp: Date.now(),
      }
      setMessages((prev) => [...prev, agentMsg])
    } catch (error: any) {
      const errMsg: ChatMessage = {
        id: `e-${Date.now()}`,
        role: 'agent',
        content: `Service error: ${error.message || 'Please try again'}`,
        timestamp: Date.now(),
      }
      setMessages((prev) => [...prev, errMsg])
    } finally {
      setLoading(false)
      scrollToBottom()
    }
  }

  const handlePersonaChange = (p: AgentPersona) => {
    setPersona(p)
    setShowPersonaPicker(false)
  }

  const toggleToolExpand = (msgId: string) => {
    setShowTools((prev) => ({ ...prev, [msgId]: !prev[msgId] }))
  }

  const personaCfg = PERSONA_CONFIG[persona]

  return (
    <View className="page-agent">
      <NavBar title="FitAI Agent" />

      {/* Persona selector */}
      <View className="persona-bar">
        <View
          className="persona-bar__current"
          onClick={() => setShowPersonaPicker(!showPersonaPicker)}
        >
          <Text className="persona-bar__icon" style={{ color: personaCfg.color }}>
            {personaCfg.icon}
          </Text>
          <Text className="persona-bar__label">{personaCfg.label}</Text>
          <Text className="persona-bar__arrow">{showPersonaPicker ? '\ue602' : '\ue603'}</Text>
        </View>
      </View>

      {/* Persona dropdown */}
      {showPersonaPicker && (
        <View className="persona-dropdown">
          {(Object.keys(PERSONA_CONFIG) as AgentPersona[]).map((key) => {
            const cfg = PERSONA_CONFIG[key]
            return (
              <View
                key={key}
                className={`persona-dropdown__item ${persona === key ? 'active' : ''}`}
                onClick={() => handlePersonaChange(key)}
              >
                <Text className="persona-dropdown__icon" style={{ color: cfg.color }}>
                  {cfg.icon}
                </Text>
                <View className="persona-dropdown__text">
                  <Text className="persona-dropdown__name">{cfg.label}</Text>
                </View>
                {persona === key && <Text className="persona-dropdown__check">{'\u2713'}</Text>}
              </View>
            )
          })}
        </View>
      )}

      {/* Chat area */}
      <ScrollView
        className="chat-area"
        scrollY
        scrollIntoView={scrollRef.current}
        enhanced
        showScrollbar={false}
      >
        {messages.length === 0 ? (
          <View className="chat-empty">
            <View className="chat-empty__icon">
              <Text>{'\ue610'}</Text>
            </View>
            <Text className="chat-empty__title">FitAI Agent</Text>
            <Text className="chat-empty__desc">
              Your AI-powered fitness studio assistant
            </Text>
            <Text className="chat-empty__hint">Try asking:</Text>
            <View className="chat-empty__suggestions">
              {QUICK_SUGGESTIONS[persona].map((s, i) => (
                <View key={i} className="chat-empty__suggestion" onClick={() => handleSend(s)}>
                  <Text>{s}</Text>
                </View>
              ))}
            </View>
          </View>
        ) : (
          <View className="chat-messages">
            {messages.map((msg) => (
              <View
                key={msg.id}
                id={msg.id}
                className={`msg ${msg.role === 'user' ? 'msg--user' : 'msg--agent'}`}
              >
                {msg.role === 'agent' && (
                  <View className="msg__avatar">
                    <Text style={{ color: personaCfg.color }}>{personaCfg.icon}</Text>
                  </View>
                )}
                <View className="msg__bubble">
                  <Text className="msg__text">{msg.content}</Text>

                  {/* Tool calls */}
                  {msg.toolCalls && msg.toolCalls.length > 0 && (
                    <View
                      className="msg__tools"
                      onClick={() => toggleToolExpand(msg.id)}
                    >
                      <Text className="msg__tools-toggle">
                        {showTools[msg.id] ? 'Hide' : 'Show'} {msg.toolCalls.length} tool calls
                        {msg.iterations ? ` (${msg.iterations} iterations)` : ''}
                      </Text>
                      {showTools[msg.id] && (
                        <View className="msg__tools-list">
                          {msg.toolCalls.map((tc, i) => (
                            <View key={i} className="tool-call">
                              <View className="tool-call__header">
                                <Text className="tool-call__name">{tc.tool}</Text>
                              </View>
                              <View className="tool-call__args">
                                <Text className="tool-call__label">Args:</Text>
                                <Text className="tool-call__value">
                                  {JSON.stringify(tc.args, null, 2)}
                                </Text>
                              </View>
                              <View className="tool-call__result">
                                <Text className="tool-call__label">Result:</Text>
                                <Text className="tool-call__value">
                                  {typeof tc.result === 'string'
                                    ? tc.result
                                    : JSON.stringify(tc.result, null, 2).slice(0, 500)}
                                </Text>
                              </View>
                            </View>
                          ))}
                        </View>
                      )}
                    </View>
                  )}
                </View>
              </View>
            ))}

            {/* Loading indicator */}
            {loading && (
              <View className="msg msg--agent">
                <View className="msg__avatar">
                  <Text style={{ color: personaCfg.color }}>{personaCfg.icon}</Text>
                </View>
                <View className="msg__bubble msg__bubble--loading">
                  <View className="typing-indicator">
                    <View className="typing-dot" />
                    <View className="typing-dot" />
                    <View className="typing-dot" />
                  </View>
                </View>
              </View>
            )}
          </View>
        )}
      </ScrollView>

      {/* Quick suggestions bar */}
      {messages.length > 0 && !loading && (
        <View className="quick-bar">
          <ScrollView scrollX showScrollbar={false}>
            <View className="quick-bar__items">
              {QUICK_SUGGESTIONS[persona].map((s, i) => (
                <View key={i} className="quick-bar__item" onClick={() => handleSend(s)}>
                  <Text>{s}</Text>
                </View>
              ))}
            </View>
          </ScrollView>
        </View>
      )}

      {/* Input bar */}
      <View className="input-bar">
        <Input
          className="input-bar__input"
          type="text"
          value={input}
          onInput={(e) => setInput(e.detail.value)}
          onConfirm={() => handleSend()}
          placeholder="Ask FitAI Agent..."
          confirmType="send"
          adjustPosition
        />
        <View
          className={`input-bar__send ${input.trim() ? 'active' : ''}`}
          onClick={() => handleSend()}
        >
          <Text>{'\ue600'}</Text>
        </View>
      </View>
    </View>
  )
}
