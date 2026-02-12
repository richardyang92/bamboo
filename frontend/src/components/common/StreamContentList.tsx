/**
 * StreamContentList - 多节点流式内容列表
 * 使用 Collapse 组件展示所有节点的流式内容
 */
import React, { useState, useEffect, useRef } from 'react';
import { Collapse, Button, Space, Card, Empty } from 'antd';
import { ExpandOutlined, CompressOutlined } from '@ant-design/icons';
import type { WorkflowStep, WorkflowType } from '../../types';
import StreamContentItem from './StreamContentItem';
import './StreamContentList.css';

interface StreamContentListProps {
  steps: WorkflowStep[];
  streamContent: Map<string, string>;
  currentNode: string | null;
  isStreaming: boolean;
  workflowType: WorkflowType;
  className?: string;
}

const StreamContentList: React.FC<StreamContentListProps> = ({
  steps,
  streamContent,
  currentNode,
  isStreaming,
  workflowType,
  className = '',
}) => {
  // 展开的节点 keys
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const activeNodeRef = useRef<HTMLDivElement>(null);

  // 合并步骤和流式内容
  const itemsWithContent = steps.map(step => ({
    ...step,
    content: streamContent.get(step.step) || '',
  }));

  // 自动展开当前流式节点
  useEffect(() => {
    if (currentNode && isStreaming) {
      setExpandedKeys(prev => {
        if (!prev.includes(currentNode)) {
          return [...prev, currentNode];
        }
        return prev;
      });
    }
  }, [currentNode, isStreaming]);

  // 自动滚动到当前流式节点
  useEffect(() => {
    if (currentNode && isStreaming && activeNodeRef.current) {
      // 查找当前展开的节点元素并滚动
      const element = document.getElementById(`stream-content-panel-${currentNode}`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  }, [currentNode, isStreaming, expandedKeys]);

  // 展开/折叠全部
  const handleExpandAll = () => {
    const allKeys = itemsWithContent.map(item => item.step);
    setExpandedKeys(allKeys);
  };

  const handleCollapseAll = () => {
    setExpandedKeys([]);
  };

  // Collapse 变化处理
  const handleCollapseChange = (keys: string | string[]) => {
    setExpandedKeys(Array.isArray(keys) ? keys : [keys]);
  };

  // 空状态
  if (itemsWithContent.length === 0) {
    return (
      <Card title="节点流式内容" className={`stream-content-list ${className}`}>
        <Empty description="暂无节点信息" />
      </Card>
    );
  }

  return (
    <Card
      title="节点流式内容"
      className={`stream-content-list ${className}`}
      extra={
        <Space size="small">
          <Button
            type="text"
            size="small"
            icon={<ExpandOutlined />}
            onClick={handleExpandAll}
            disabled={expandedKeys.length === itemsWithContent.length}
          >
            全部展开
          </Button>
          <Button
            type="text"
            size="small"
            icon={<CompressOutlined />}
            onClick={handleCollapseAll}
            disabled={expandedKeys.length === 0}
          >
            全部折叠
          </Button>
        </Space>
      }
    >
      <Collapse
        activeKey={expandedKeys}
        onChange={handleCollapseChange}
        className="stream-content-collapse"
        expandIconPosition="end"
      >
        {itemsWithContent.map((item) => (
          <Collapse.Panel
            key={item.step}
            id={`stream-content-panel-${item.step}`}
            header={
              <div className="stream-content-panel-header">
                <Space size="small">
                  {item.name}
                  {item.step === currentNode && isStreaming && (
                    <span className="streaming-indicator">流式中</span>
                  )}
                </Space>
              </div>
            }
          >
            <StreamContentItem
              step={item}
              content={item.content}
              isActive={item.step === currentNode}
              isStreaming={item.step === currentNode && isStreaming}
              workflowType={workflowType}
            />
          </Collapse.Panel>
        ))}
      </Collapse>
    </Card>
  );
};

export default React.memo(StreamContentList);
