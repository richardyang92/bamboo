/**
 * CardListView - 卡片列表视图
 * 以卡片形式展示工作流步骤，支持展开/折叠
 */
import React, { useState } from 'react';
import { Space } from 'antd';
import WorkflowNodeCard from '../workflowNodes/WorkflowNodeCard';
import type { WorkflowStep } from '../../../types';
import './CardListView.css';

interface CardListViewProps {
  steps: WorkflowStep[];
  currentStep?: string;
  compact?: boolean;
  allExpanded?: boolean;
  onNodeClick?: (stepId: string) => void;
  onStreamContentClick?: (stepId: string) => void;
  className?: string;
}

const CardListView: React.FC<CardListViewProps> = ({
  steps,
  currentStep = '',
  compact = false,
  allExpanded = false,
  onNodeClick,
  onStreamContentClick,
  className = '',
}) => {
  // 管理每个步骤的展开状态
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());

  // 切换步骤展开状态
  const toggleStep = (stepId: string) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepId)) {
      newExpanded.delete(stepId);
    } else {
      newExpanded.add(stepId);
    }
    setExpandedSteps(newExpanded);
    onNodeClick?.(stepId);
  };

  // 判断步骤是否展开
  const isStepExpanded = (stepId: string): boolean => {
    return allExpanded || expandedSteps.has(stepId);
  };

  if (steps.length === 0) {
    return (
      <div className={`card-list-view empty ${className}`}>
        <p style={{ textAlign: 'center', color: '#999', marginTop: 40 }}>
          暂无步骤信息
        </p>
      </div>
    );
  }

  return (
    <div className={`card-list-view ${compact ? 'compact' : ''} ${className}`}>
      <Space
        direction="vertical"
        size={compact ? 'small' : 'middle'}
        style={{ width: '100%' }}
      >
        {steps.map((step) => {
          const isCurrent = step.step === currentStep;

          return (
            <WorkflowNodeCard
              key={step.step}
              step={step}
              isExpanded={isStepExpanded(step.step)}
              onToggle={() => toggleStep(step.step)}
              compact={compact}
              showStreamContentLink={isCurrent}
              onStreamContentClick={() => onStreamContentClick?.(step.step)}
              className={isCurrent ? 'current-step' : ''}
            />
          );
        })}
      </Space>
    </div>
  );
};

export default CardListView;
