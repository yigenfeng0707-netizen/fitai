import { useState } from 'react'
import { Card, Row, Col, Button, message } from 'antd'
import { DownloadOutlined, TeamOutlined, DollarOutlined, ScheduleOutlined, AuditOutlined } from '@ant-design/icons'
import { exportApi, downloadBlob } from '../api'

const EXPORT_ITEMS = [
  { key: 'members', label: '会员数据', icon: <TeamOutlined />, description: '导出所有会员基本信息、卡信息、消费记录' },
  { key: 'orders', label: '订单数据', icon: <DollarOutlined />, description: '导出所有订单金额、支付状态、时间' },
  { key: 'bookings', label: '预约数据', icon: <ScheduleOutlined />, description: '导出所有预约记录、课程、签到状态' },
  { key: 'leads', label: '潜客数据', icon: <AuditOutlined />, description: '导出所有潜客信息、来源、跟进记录' },
]

const DataExport = () => {
  const [loading, setLoading] = useState<string | null>(null)

  const handleExport = async (key: string, label: string) => {
    setLoading(key)
    try {
      const blob = await exportApi.download(key)
      const date = new Date().toISOString().slice(0, 10).replace(/-/g, '')
      downloadBlob(blob, `${label}_${date}.xlsx`)
      message.success(`${label}导出成功`)
    } catch {
      message.error(`${label}导出失败`)
    }
    setLoading(null)
  }

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}><DownloadOutlined /> 数据导出</h2>
      <Row gutter={[16, 16]}>
        {EXPORT_ITEMS.map(item => (
          <Col xs={24} sm={12} lg={12} key={item.key}>
            <Card>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 18, fontWeight: 'bold', marginBottom: 4 }}>
                    {item.icon} {item.label}
                  </div>
                  <div style={{ color: '#999' }}>{item.description}</div>
                </div>
                <Button
                  type="primary"
                  icon={<DownloadOutlined />}
                  loading={loading === item.key}
                  onClick={() => handleExport(item.key, item.label)}
                >
                  导出 Excel
                </Button>
              </div>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  )
}

export default DataExport
