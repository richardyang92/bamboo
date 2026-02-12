/**
 * WorkflowExecutionTracker - 工作流执行追踪器
 * 主容器组件，提供三种视图模式和统一的工作流步骤展示
 */
import React, { useState, useEffect, useMemo } from 'react';
import type { WorkflowViewMode, WorkflowStep, WorkflowType } from '../../types';
import { getStepCounts } from '../../utils/timeUtils';
import WorkflowViewToolbar from './workflowViews/WorkflowViewToolbar';
import CardListView from './workflowViews/CardListView';
import NodeGraphView from './workflowViews/NodeGraphView';
import TimelineView from './workflowViews/TimelineView';
import './WorkflowExecutionTracker.css';

interface WorkflowExecutionTrackerProps {
  steps: WorkflowStep[];
  currentStep?: string;
  workflowType: WorkflowType;
  initialViewMode?: WorkflowViewMode;
  onNodeClick?: (stepId: string) => void;
  onStreamContentClick?: (stepId: string) => void;
  className?: string;
}

// localStorage key for view mode
const getViewModeStorageKey = (workflowType: WorkflowType): string => {
  return `workflow-view-mode-${workflowType}`;
};

const WorkflowExecutionTracker: React.FC<WorkflowExecutionTrackerProps> = ({
  steps,
  currentStep = '',
  workflowType,
  initialViewMode = 'cards',
  onNodeClick,
  onStreamContentClick,
  className = '',
}) => {
  // 从 localStorage 读取保存的视图模式
  const [viewMode, setViewMode] = useState<WorkflowViewMode>(() => {
    try {
      const saved = localStorage.getItem(getViewModeStorageKey(workflowType));
      if (saved && ['cards', 'graph', 'timeline'].includes(saved)) {
        return saved as WorkflowViewMode;
      }
    } catch (e) {
      // Ignore localStorage errors
    }
    return initialViewMode;
  });

  // 展开/折叠状态
  const [allExpanded, setAllExpanded] = useState(false);
  const [compactMode, setCompactMode] = useState(false);

  // 保存视图模式到 localStorage
  useEffect(() => {
    try {
      localStorage.setItem(getViewModeStorageKey(workflowType), viewMode);
    } catch (e) {
      // Ignore localStorage errors
    }
  }, [viewMode, workflowType]);

  // 计算步骤计数
  const [completedCount, totalCount] = useMemo(
    () => getStepCounts(steps),
    [steps]
  );

  // 处理视图模式切换
  const handleViewModeChange = (mode: WorkflowViewMode) => {
    setViewMode(mode);
  };

  // 处理展开/折叠全部
  const handleToggleExpandAll = () => {
    setAllExpanded(!allExpanded);
  };

  // 处理紧凑模式切换
  const handleToggleCompactMode = () => {
    setCompactMode(!compactMode);
  };

  // 渲染当前视图
  const renderView = () => {
    const commonProps = {
      steps,
      currentStep,
      onNodeClick,
      onStreamContentClick,
      className: 'workflow-view-content',
    };

    switch (viewMode) {
      case 'cards':
        return (
          <CardListView
            {...commonProps}
            compact={compactMode}
            allExpanded={allExpanded}
          />
        );
      case 'graph':
        return <NodeGraphView {...commonProps} />;
      case 'timeline':
        return (
          <TimelineView
            {...commonProps}
            allExpanded={allExpanded}
          />
        );
      default:
        return <CardListView {...commonProps} />;
    }
  };

  return (
    <div className={`workflow-execution-tracker ${viewMode} ${className}`}>
      {/* 工具栏 */}
      <WorkflowViewToolbar
        viewMode={viewMode}
        onViewModeChange={handleViewModeChange}
        completedCount={completedCount}
        totalCount={totalCount}
        allExpanded={allExpanded}
        onToggleExpandAll={handleToggleExpandAll}
        compactMode={compactMode}
        onToggleCompactMode={handleToggleCompactMode}
      />

      {/* 视图内容 */}
      {renderView()}
    </div>
  );
};

export default WorkflowExecutionTracker;
