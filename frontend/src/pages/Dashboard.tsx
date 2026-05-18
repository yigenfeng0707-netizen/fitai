import { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import {
  UserOutlined,
  CalendarOutlined,
  WalletOutlined,
  TrendingUpOutlined,
} from '@ant-design/icons';
import * as echarts from 'echarts';

export default function Dashboard() {
  const [chartsReady, setChartsReady] = useState(false);

  useEffect(() => {
    setChartsReady(true);
  }, []);

  useEffect(() => {
    if (!chartsReady) return;

    const revenueChart = echarts.init(document.getElementById('revenueChart'));
    revenueChart.setOption({
      title: { text: '月度营收趋势', left: 'center' },
      xAxis: { type: 'category', data: ['1月', '2月', '3月', '4月', '5月', '6月'] },
      yAxis: { type: 'value' },
      series: [{ data: [12000, 19000, 15000, 22000, 28000, 35000], type: 'line' }],
    });

    const memberChart = echarts.init(document.getElementById('memberChart'));
    memberChart.setOption({
      title: { text: '会员增长', left: 'center' },
      xAxis: { type: 'category', data: ['1月', '2月', '3月', '4月', '5月', '6月'] },
      yAxis: { type: 'value' },
      series: [{ data: [32, 45, 58, 72, 85, 98], type: 'bar' }],
    });

    const courseChart = echarts.init(document.getElementById('courseChart'));
    courseChart.setOption({
      title: { text: '课程热度', left: 'center' },
      series: [
        {
          name: '课程',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: { borderRadius: 10 },
          label: { show: true },
          data: [
            { value: 35, name: '瑜伽' },
            { value: 25, name: '普拉提' },
            { value: 20, name: '动感单车' },
            { value: 15, name: '私教' },
            { value: 5, name: '其他' },
          ],
        },
      ],
    });

    return () => {
      revenueChart.dispose();
      memberChart.dispose();
      courseChart.dispose();
    };
  }, [chartsReady]);

  return (
    <div>
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总会员数"
              value={1256}
              prefix={<UserOutlined />}
              suffix="人"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="今日预约"
              value={48}
              prefix={<CalendarOutlined />}
              suffix="次"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="本月营收"
              value={128500}
              prefix={<WalletOutlined />}
              suffix="元"
              precision={2}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="增长率"
              value={23.5}
              prefix={<TrendingUpOutlined />}
              suffix="%"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="营收趋势" style={{ height: 300 }}>
            <div id="revenueChart" style={{ width: '100%', height: 250 }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="会员增长" style={{ height: 300 }}>
            <div id="memberChart" style={{ width: '100%', height: 250 }} />
          </Card>
        </Col>
      </Row>
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="课程热度分布" style={{ height: 300 }}>
            <div id="courseChart" style={{ width: '100%', height: 250 }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="今日课程安排">
            <div style={{ padding: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0' }}>
                <span>09:00 - 10:00</span>
                <span>瑜伽基础课</span>
                <span>张教练</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0' }}>
                <span>10:30 - 11:30</span>
                <span>普拉提核心</span>
                <span>李教练</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0' }}>
                <span>14:00 - 15:00</span>
                <span>动感单车</span>
                <span>王教练</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0' }}>
                <span>15:30 - 16:30</span>
                <span>瑜伽进阶</span>
                <span>张教练</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0' }}>
                <span>19:00 - 20:00</span>
                <span>私教课</span>
                <span>刘教练</span>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
}