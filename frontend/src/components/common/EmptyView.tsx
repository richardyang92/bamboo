/**
 * EmptyView - 空状态占位组件
 * 工作流未开始时显示
 */
import React from 'react';
import { Clock } from 'lucide-react';
import './EmptyView.css';

interface EmptyViewProps {
  workflowType: 'drawing' | 'document_with_images' | 'manim';
}

const EmptyView: React.FC<EmptyViewProps> = ({ workflowType }) => {
  const getEmptyText = () => {
    switch (workflowType) {
      case 'drawing':
        return '等待绘图工作流启动...';
      case 'document_with_images':
        return '等待文档工作流启动...';
      case 'manim':
        return '等待动画工作流启动...';
      default:
        return '等待工作流启动...';
    }
  };

  return (
    <div className="cli-empty-view">
      <Clock className="cli-empty-icon" size={16} strokeWidth={1.5} />
      <span className="cli-empty-text">{getEmptyText()}</span>
    </div>
  );
};

export default EmptyView;
