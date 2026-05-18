import { useEffect, useState } from 'react';
import { Card, Button, Form, Select, DatePicker, TimePicker, message, Modal, Table } from 'antd';
import { PlusOutlined, CalendarOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { courses, coaches } from '@/services/api';

interface Schedule {
  id: number;
  course: { name: string };
  classroom: { name: string };
  coach_id: number;
  date: string;
  start_time: string;
  end_time: string;
  status: string;
  max_capacity: number;
  current_count: number;
}

export default function CourseSchedules() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [coursesList, setCoursesList] = useState<{ id: number; name: string }[]>([]);
  const [classrooms, setClassrooms] = useState<{ id: number; name: string }[]>([]);
  const [coachesList, setCoachesList] = useState<{ id: number; name: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [schedulesData, coursesData, classroomsData, coachesData] = await Promise.all([
        courses.schedules(),
        courses.list(),
        courses.classrooms(),
        coaches.list(),
      ]);
      setSchedules(schedulesData);
      setCoursesList(coursesData);
      setClassrooms(classroomsData);
      setCoachesList(coachesData);
    } catch (error) {
      message.error('获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (values: { course_id: number; classroom_id: number; coach_id: number; date: string; start_time: string; end_time: string }) => {
    try {
      await courses.createSchedule({
        course_id: values.course_id,
        classroom_id: values.classroom_id,
        coach_id: values.coach_id,
        date: values.date,
        start_time: values.start_time,
        end_time: values.end_time,
      });
      message.success('排课成功');
      setModalVisible(false);
      form.resetFields();
      fetchData();
    } catch (error) {
      message.error('排课失败');
    }
  };

  const columns = [
    { title: '课程', dataIndex: 'course', key: 'course', render: (c: { name: string }) => c.name },
    { title: '教室', dataIndex: 'classroom', key: 'classroom', render: (c: { name: string }) => c.name },
    { title: '日期', dataIndex: 'date', key: 'date' },
    { title: '开始时间', dataIndex: 'start_time', key: 'start_time' },
    { title: '结束时间', dataIndex: 'end_time', key: 'end_time' },
    { title: '教练', dataIndex: 'coach_id', key: 'coach_id', render: (id: number) => coachesList.find(c => c.id === id)?.name || id },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) =>
        status === 'scheduled' ? (
          <span style={{ color: '#52c41a' }}>已排课</span>
        ) : (
          <span style={{ color: '#ff4d4f' }}>{status}</span>
        ),
    },
    {
      title: '人数',
      key: 'capacity',
      render: (_, record: Schedule) => `${record.current_count}/${record.max_capacity}`,
    },
  ];

  return (
    <Card
      title="排课管理"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
          新增排课
        </Button>
      }
    >
      <Table
        dataSource={schedules}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title="新增排课"
        visible={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form form={form} onFinish={handleSubmit} layout="vertical">
          <Form.Item
            name="course_id"
            label="课程"
            rules={[{ required: true, message: '请选择课程' }]}
          >
            <Select placeholder="请选择课程">
              {coursesList.map((c) => (
                <Select.Option key={c.id} value={c.id}>
                  {c.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="classroom_id"
            label="教室"
            rules={[{ required: true, message: '请选择教室' }]}
          >
            <Select placeholder="请选择教室">
              {classrooms.map((c) => (
                <Select.Option key={c.id} value={c.id}>
                  {c.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="coach_id"
            label="教练"
            rules={[{ required: true, message: '请选择教练' }]}
          >
            <Select placeholder="请选择教练">
              {coachesList.map((c) => (
                <Select.Option key={c.id} value={c.id}>
                  {c.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="date"
            label="日期"
            rules={[{ required: true, message: '请选择日期' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="start_time"
            label="开始时间"
            rules={[{ required: true, message: '请选择开始时间' }]}
          >
            <TimePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="end_time"
            label="结束时间"
            rules={[{ required: true, message: '请选择结束时间' }]}
          >
            <TimePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">
              确认排课
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}