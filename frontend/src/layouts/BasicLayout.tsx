import { Layout, Menu, Avatar, Dropdown, Button, message } from 'antd';
import {
  BarChartOutlined,
  UserOutlined,
  CalendarOutlined,
  BookOutlined,
  TeamOutlined,
  WalletOutlined,
  SettingOutlined,
  LogoutOutlined,
  ChevronDownOutlined,
} from '@ant-design/icons';
import { useUser, roleNames } from '@/store/user';
import { Outlet, useLocation, useNavigate } from 'umi';

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: '/dashboard', label: '数据看板', icon: <BarChartOutlined /> },
  { key: '/members', label: '会员管理', icon: <UserOutlined /> },
  { key: '/courses', label: '课程管理', icon: <CalendarOutlined /> },
  { key: '/bookings', label: '预约管理', icon: <BookOutlined /> },
  { key: '/coaches', label: '教练管理', icon: <TeamOutlined /> },
  { key: '/finance', label: '财务管理', icon: <WalletOutlined /> },
  { key: '/system', label: '系统设置', icon: <SettingOutlined /> },
];

export default function BasicLayout() {
  const { user, logout } = useUser();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    message.success('已退出登录');
    navigate('/login');
  };

  const userMenu = [
    { key: 'logout', label: '退出登录', icon: <LogoutOutlined /> },
  ];

  const getRoleMenu = () => {
    if (!user) return menuItems;
    const roleMenus: Record<number, string[]> = {
      1: ['/dashboard', '/members', '/courses', '/bookings', '/coaches', '/finance', '/system'],
      2: ['/dashboard', '/members', '/courses', '/bookings', '/coaches', '/finance'],
      3: ['/dashboard', '/members', '/bookings'],
      4: ['/dashboard', '/bookings'],
      5: ['/dashboard', '/finance'],
    };
    const allowedKeys = roleMenus[user.role_id] || [];
    return menuItems.filter((item) => allowedKeys.includes(item.key));
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible theme="dark" width={200}>
        <div className="logo" style={{ padding: '16px', color: '#fff', fontSize: '18px', textAlign: 'center' }}>
          FitAI
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname.split('/')[1] ? `/${location.pathname.split('/')[1]}` : '/dashboard']}
          style={{ height: '100%', borderRight: 0 }}
        >
          {getRoleMenu().map((item) => (
            <Menu.Item key={item.key} icon={item.icon}>
              {item.label}
            </Menu.Item>
          ))}
        </Menu>
      </Sider>
      <Layout>
        <Header style={{ padding: 0, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
          <Dropdown menu={{ items: userMenu }} placement="bottomRight">
            <Button type="text" style={{ display: 'flex', alignItems: 'center', color: '#fff' }}>
              <Avatar icon={<UserOutlined />} />
              <span style={{ marginLeft: 8 }}>{user?.name}</span>
              <span style={{ marginLeft: 4 }}>({roleNames[user?.role_id || 0]})</span>
              <ChevronDownOutlined />
            </Button>
          </Dropdown>
        </Header>
        <Content style={{ padding: '24px', background: '#f0f2f5' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}