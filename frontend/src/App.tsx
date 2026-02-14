/**
 * Bamboo 主应用组件
 */
import { Layout, theme, Button, ConfigProvider } from 'antd';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { HomeOutlined, HistoryOutlined, SunOutlined, MoonOutlined } from '@ant-design/icons';
import { useTheme } from './contexts/ThemeContext';
import HomePage from './pages/HomePage';
import HistoryPage from './pages/HistoryPage';
import './App.css';
import zhCN from 'antd/locale/zh_CN';

const { Header, Content } = Layout;

// 内部组件，在 ConfigProvider 内部使用
function AppContent() {
  const { mode, toggleTheme } = useTheme();
  const location = useLocation();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const isHistoryPage = location.pathname === '/history';

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          background: mode === 'dark' ? '#141414' : '#001529',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>
            Bamboo
          </div>
          <Link to="/" style={{ color: isHistoryPage ? '#ffffff80' : 'white', fontSize: '16px' }}>
            <HomeOutlined /> 首页
          </Link>
          <Link to="/history" style={{ color: isHistoryPage ? 'white' : '#ffffff80', fontSize: '16px' }}>
            <HistoryOutlined /> 历史记录
          </Link>
        </div>
        <Button
          type="text"
          icon={mode === 'dark' ? <SunOutlined /> : <MoonOutlined />}
          onClick={toggleTheme}
          style={{ color: 'white' }}
        >
          {mode === 'dark' ? '浅色' : '深色'}
        </Button>
      </Header>
      <Layout>
        <Content
          style={{
            padding: '24px',
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
            margin: '16px',
            flex: 1,
            minHeight: 0,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

function App() {
  const { mode } = useTheme();

  const configTheme = {
    algorithm: mode === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: '#1890ff',
      borderRadius: 6,
    },
  };

  return (
    <ConfigProvider theme={configTheme} locale={zhCN}>
      <AppContent />
    </ConfigProvider>
  );
}

export default App;
