import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Table, Button, Card, Row, Col, Statistic, message, Spin, Space } from 'antd'
import { ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons'
import { aiApi } from '../api'
import type { BodyTestAnalysis } from '../api/types'

const BodyTest = () => {
  const { memberId } = useParams()
  const navigate = useNavigate()
  const [analysis, setAnalysis] = useState<BodyTestAnalysis | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!memberId) return
    aiApi.analyzeBodyTest(Number(memberId))
      .then(setAnalysis)
      .catch(() => message.error('获取体测数据失败'))
      .finally(() => setLoading(false))
  }, [memberId])

  if (loading) {
    return <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />
  }

  if (!analysis?.current) {
    return (
      <div>
        <h1>体测分析</h1>
        <p style={{ color: '#999', marginTop: 24 }}>该会员尚无体测数据</p>
        <Button type="primary" onClick={() => navigate(`/members`)}>返回会员列表</Button>
      </div>
    )
  }

  const { current, previous, trends, suggestions } = analysis

  const trendIcon = (key: string, reverse = false) => {
    if (!(key in trends)) return <MinusOutlined style={{ color: '#999' }} />
    const val = trends[key]
    if (val === 0) return <MinusOutlined style={{ color: '#999' }} />
    const isUp = reverse ? val < 0 : val > 0
    return isUp
      ? <ArrowUpOutlined style={{ color: val > 0 ? '#ff4d4f' : '#52c41a' }} />
      : <ArrowDownOutlined style={{ color: val < 0 ? '#52c41a' : '#ff4d4f' }} />
  }

  const statStyle = { textAlign: 'center' as const }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <h1 style={{ margin: 0 }}>体测分析</h1>
        <Button onClick={() => navigate('/members')}>返回会员列表</Button>
      </Space>

      {current.score !== null && (
        <Card size="small" style={{ marginBottom: 16, width: 200 }}>
          <Statistic
            title="综合评分"
            value={current.score}
            suffix="分"
            valueStyle={{ color: (current.score || 0) >= 80 ? '#52c41a' : (current.score || 0) >= 60 ? '#faad14' : '#ff4d4f' }}
          />
        </Card>
      )}

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}><Card size="small" style={statStyle}>
          <Statistic title="身高" value={current.height || '-'} suffix={current.height ? 'cm' : ''} />
        </Card></Col>
        <Col span={6}><Card size="small" style={statStyle}>
          <Statistic title="体重" value={current.weight || '-'} prefix={trendIcon('weight_change')} suffix={current.weight ? 'kg' : ''} />
        </Card></Col>
        <Col span={6}><Card size="small" style={statStyle}>
          <Statistic title="体脂率" value={current.body_fat_percentage || '-'} prefix={trendIcon('body_fat_change', true)} suffix={current.body_fat_percentage ? '%' : ''} />
        </Card></Col>
        <Col span={6}><Card size="small" style={statStyle}>
          <Statistic title="肌肉量" value={current.muscle_mass || '-'} prefix={trendIcon('muscle_mass_change')} suffix={current.muscle_mass ? 'kg' : ''} />
        </Card></Col>
        <Col span={6}><Card size="small" style={statStyle}>
          <Statistic title="BMI" value={current.bmi || '-'} />
        </Card></Col>
        <Col span={6}><Card size="small" style={statStyle}>
          <Statistic title="骨量" value={current.bone_mass || '-'} suffix={current.bone_mass ? 'kg' : ''} />
        </Card></Col>
        <Col span={6}><Card size="small" style={statStyle}>
          <Statistic title="体水分" value={current.body_water || '-'} suffix={current.body_water ? '%' : ''} />
        </Card></Col>
        <Col span={6}><Card size="small" style={statStyle}>
          <Statistic title="基础代谢" value={current.basal_metabolism || '-'} suffix={current.basal_metabolism ? 'kcal' : ''} />
        </Card></Col>
        <Col span={6}><Card size="small" style={statStyle}>
          <Statistic title="内脏脂肪" value={current.visceral_fat || '-'} />
        </Card></Col>
        <Col span={6}><Card size="small" style={statStyle}>
          <Statistic title="体年龄" value={current.body_age || '-'} suffix={current.body_age ? '岁' : ''} />
        </Card></Col>
        <Col span={6}><Card size="small" style={statStyle}>
          <Statistic title="蛋白质" value={current.protein || '-'} suffix={current.protein ? '%' : ''} />
        </Card></Col>
      </Row>

      {suggestions.length > 0 && (
        <Card title="AI 分析建议" size="small" style={{ marginBottom: 16 }}>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {suggestions.map((s, i) => <li key={i} style={{ marginBottom: 4 }}>{s}</li>)}
          </ul>
        </Card>
      )}

      {previous && (
        <Card title="上次体测对比" size="small">
          <Table
            dataSource={[
              { label: '体重', current: current.weight, previous: previous.weight, unit: 'kg', key: 'weight_change', reverse: false },
              { label: '体脂率', current: current.body_fat_percentage, previous: previous.body_fat_percentage, unit: '%', key: 'body_fat_change', reverse: true },
              { label: '肌肉量', current: current.muscle_mass, previous: previous.muscle_mass, unit: 'kg', key: 'muscle_mass_change', reverse: false },
              { label: 'BMI', current: current.bmi, previous: previous.bmi, unit: '', key: '', reverse: false },
            ]}
            columns={[
              { title: '指标', dataIndex: 'label' },
              { title: '当前值', render: (_: any, r: any) => r.current != null ? `${r.current}${r.unit}` : '-' },
              { title: '上次值', render: (_: any, r: any) => r.previous != null ? `${r.previous}${r.unit}` : '-' },
              { title: '变化', render: (_: any, r: any) => {
                if (r.current == null || r.previous == null) return '-'
                const diff = r.current - r.previous
                const color = r.reverse ? (diff < 0 ? '#52c41a' : '#ff4d4f') : (diff > 0 ? '#52c41a' : '#ff4d4f')
                return <span style={{ color }}>{diff > 0 ? '+' : ''}{diff.toFixed(1)}{r.unit}</span>
              }},
            ]}
            pagination={false}
            rowKey="label"
          />
        </Card>
      )}
    </div>
  )
}

export default BodyTest
