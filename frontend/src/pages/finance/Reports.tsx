import { useEffect, useState } from 'react';
import { Card, Row, Col, Button, DatePicker, Select, Statistic } from 'antd';
import { WalletOutlined, TrendingUpOutlined, UsersOutlined, FileTextOutlined } from '@ant-design/icons';
import * as echarts from 'echarts';

export default function Reports() {
  const [chartsReady, setChartsReady] = useState(false);

  useEffect(() => {
    setChartsReady(true);
  }, []);

  useEffect(() => {
    if (!chartsReady) return;

    const revenueChart = echarts.init(document.getElementById('revenueChart'));
    revenueChart.setOption({
      title: { text: '月度营收', left: 'center' },
      xAxis: { type: 'category', data: ['1月', '2月', '3月', '4月', '5月', '6月'] },
      yAxis: { type: 'value' },
      series: [
        { data: [85000, 92000, 108000, 115000, 132000, 148000], type: 'line', name: '营收' },
        { data: [62000, 68000, 78000, 82000, 95000, 105000], type: 'line', name: '成本' },
      ],
    });

    const categoryChart = echarts.init(document.getElementById('categoryChart'));
    categoryChart.setOption({
      title: { text: '营收构成', left: 'center' },
      series: [
        {
          name: '营收',
          type: 'pie',
          radius: '50%',
          data: [
            { value: 45, name: '会员卡' },
            { value: 25, name: '课程销售' },
            { value: 20, name: '私教课' },
            { value: 10, name: '其他' },
          ],
        },
      ],
    });

    return () => {
      revenueChart.dispose();
      categoryChart.dispose();
    };
  }, [chartsReady]);

  return (
    <div>
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic title="本月营收" value={148500} prefix={<WalletOutlined />} suffix="元" precision={2} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="同比增长" value={23.5} prefix={<TrendingUpOutlined />} suffix="%" valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="新增会员" value={45} prefix={<UsersOutlined />} suffix="人" />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="消耗课时" value={328} prefix={<FileTextOutlined />} suffix="节" />
          </Card>
        </Col>
      </Row>
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="营收趋势">
            <div id="revenueChart" style={{ width: '100%', height: 300 }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="营收构成">
            <div id="categoryChart" style={{ width: '100%', height: 300 }} />
          </Card>
        </Col>
      </Row>
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="财务摘要">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', padding: '16px' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>¥86,500</div>
                <div style={{ color: '#999', marginTop: '8px' }}>会员卡收入</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>¥42,300</div>
                <div style={{ color: '#999', marginTop: '8px' }}>课程销售收入</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#faad14' }}>¥15,700</div>
                <div style={{ color: '#999', marginTop: '8px' }}>私教收入</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ff4d4f' }}>-¥16,000</div>
                <div style={{ color: '#999', marginTop: '8px' }}>成本支出</div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
}