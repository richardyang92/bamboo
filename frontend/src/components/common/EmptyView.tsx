import React from 'react';
import { Clock } from 'lucide-react';

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
    <div className="flex items-center gap-3 px-4 py-4 font-mono text-[var(--color-text-muted)] text-sm">
      <Clock className="w-4 h-4 text-[var(--color-text-muted)] flex-shrink-0" strokeWidth={1.5} />
      <span className="italic text-xs">{getEmptyText()}</span>
    </div>
  );
};

export default EmptyView;
