/**
 * 首页 - 包含三个工作流标签页
 */
import { useState } from 'react';
import { Tabs } from 'antd';
import { BarChartOutlined, FileTextOutlined, VideoCameraOutlined } from '@ant-design/icons';
import { useWorkflow } from '../contexts/WorkflowContext';
import DrawingPanel from '../components/drawing/DrawingPanel';
import DocumentPanel from '../components/document/DocumentPanel';
import ManimPanel from '../components/manim/ManimPanel';

function HomePage() {
  const { setCurrentWorkflow } = useWorkflow();
  const [activeTab, setActiveTab] = useState('drawing');

  const handleTabChange = (key: string) => {
    setActiveTab(key);
    setCurrentWorkflow(key as any);
  };

  const tabItems = [
    {
      key: 'drawing',
      label: (
        <span>
          <BarChartOutlined /> 数据可视化
        </span>
      ),
      children: null,
    },
    {
      key: 'document',
      label: (
        <span>
          <FileTextOutlined /> 文档+图表
        </span>
      ),
      children: null,
    },
    {
      key: 'manim',
      label: (
        <span>
          <VideoCameraOutlined /> 数学动画
        </span>
      ),
      children: null,
    },
  ];

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <Tabs
        activeKey={activeTab}
        onChange={handleTabChange}
        items={tabItems}
        size="large"
        style={{ flexShrink: 0 }}
      />
      <div style={{ flex: 1, overflow: 'hidden', minHeight: 0 }}>
        {activeTab === 'drawing' && <DrawingPanel />}
        {activeTab === 'document' && <DocumentPanel />}
        {activeTab === 'manim' && <ManimPanel />}
      </div>
    </div>
  );
}

export default HomePage;
