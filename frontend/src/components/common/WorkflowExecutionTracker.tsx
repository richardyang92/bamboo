/**
 * WorkflowExecutionTracker - 工作流执行追踪器
 * 仅显示流程图视图，真实反映CodeAct流程
 * Now using React Flow for improved visualization
 */
import React, { useMemo } from 'react';
import type { WorkflowStep, WorkflowType } from '../../types';
import { getStepCounts } from '../../utils/timeUtils';
import ReactFlowNodeGraphView from './workflowViews/ReactFlowNodeGraphView';
import './WorkflowExecutionTracker.css';

interface WorkflowExecutionTrackerProps {
  steps: WorkflowStep[];
  currentStep?: string;
  workflowType: WorkflowType;
  onNodeClick?: (stepId: string) => void;
  className?: string;
}

const WorkflowExecutionTracker: React.FC<WorkflowExecutionTrackerProps> = ({
  steps,
  currentStep = '',
  workflowType,
  onNodeClick,
  className = '',
}) => {
  // 计算步骤计数
  const [completedCount, totalCount] = useMemo(
    () => getStepCounts(steps),
    [steps]
  );

  return (
    <div className={`workflow-execution-tracker graph ${className}`}>
      {/* 简单的头部信息 */}
      <div className="workflow-graph-header">
        <span className="step-count">
          进度: {completedCount}/{totalCount} 步骤完成
        </span>
      </div>

      {/* 流程图视图 - React Flow 实现 */}
      <ReactFlowNodeGraphView
        steps={steps}
        currentStep={currentStep}
        onNodeClick={onNodeClick}
        workflowType={workflowType}
        className="workflow-view-content"
      />
    </div>
  );
};

export default WorkflowExecutionTracker;
