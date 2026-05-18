import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import './index.css';

function MyApp({ children }: { children: React.ReactNode }) {
  return (
    <ConfigProvider locale={zhCN}>
      {children}
    </ConfigProvider>
  );
}

export default MyApp;