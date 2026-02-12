/**
 * TimelineView - 时间线视图
 * 以垂直时间线形式展示工作流步骤
 */
import React, { useState } from 'react';
import { Space, Tag } from 'antd';
import {
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import type { WorkflowStep } from '../../../types';
import {
  formatDuration,
  formatTimestamp,
  getDurationColor,
  getRelativeTime,
} from '../../../utils/timeUtils';
import './TimelineView.css';

interface TimelineViewProps {
  steps: WorkflowStep[];
  currentStep?: string;
  allExpanded?: boolean;
  onNodeClick?: (stepId: string) => void;
  onStreamContentClick?: (stepId: string) => void;
  className?: string;
}

// 获取步骤状态图标
const getStatusIcon = (status: WorkflowStep['status']) => {
  switch (status) {
    case 'running':
      return <LoadingOutlined style={{ color: '#1890ff' }} spin />;
    case 'completed':
      return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
    case 'error':
      return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
    case 'pending':
    default:
      return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />;
  }
};

const TimelineView: React.FC<TimelineViewProps> = ({
  steps,
  currentStep = '',
  allExpanded = false,
  onNodeClick,
  onStreamContentClick,
  className = '',
}) => {
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());

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

  const isStepExpanded = (stepId: string): boolean => {
    return allExpanded || expandedSteps.has(stepId);
  };

  if (steps.length === 0) {
    return (
      <div className={`timeline-view empty ${className}`}>
        <p style={{ textAlign: 'center', color: '#999', marginTop: 60 }}>
          暂无步骤信息
        </p>
      </div>
    );
  }

  return (
    <div className={`timeline-view ${className}`}>
      <div className="timeline-container">
        {/* 时间轴线 */}
        <div className="timeline-line" />

        {/* 时间线项目 */}
        {steps.map((step, index) => {
          const isCurrent = step.step === currentStep;
          const duration = step.completed_at && step.timestamp
            ? new Date(step.completed_at).getTime() - new Date(step.timestamp).getTime()
            : undefined;

          return (
            <div
              key={step.step}
              className={`timeline-item ${step.status} ${isCurrent ? 'current' : ''}`}
              onClick={() => toggleStep(step.step)}
            >
              {/* 时间点 */}
              <div className="timeline-dot">
                <div className="timeline-dot-inner">
                  {getStatusIcon(step.status)}
                </div>
              </div>

              {/* 内容卡片 */}
              <div className="timeline-content">
                {/* 基本信息行 */}
                <div className="timeline-header">
                  <Space size="small">
                    <span className="timeline-step-number">{index + 1}</span>
                    <span className="timeline-step-name">{step.name}</span>
                    {isCurrent && (
                      <Tag color="processing" style={{ fontSize: '11px' }}>
                        当前
                      </Tag>
                    )}
                    {duration !== undefined && (
                      <Tag
                        color={getDurationColor(duration)}
                        style={{ fontSize: '11px' }}
                      >
                        {formatDuration(duration)}
                      </Tag>
                    )}
                  </Space>
                </div>

                {/* 展开的详细信息 */}
                {isStepExpanded(step.step) && (
                  <div className="timeline-details">
                    {/* 时间信息 */}
                    <div className="timeline-time-info">
                      {step.timestamp && (
                        <span className="time-label">
                          {formatTimestamp(step.timestamp)}
                        </span>
                      )}
                      {step.completed_at && (
                        <>
                          <span className="time-arrow">→</span>
                          <span className="time-label">
                            {formatTimestamp(step.completed_at)}
                          </span>
                        </>
                      )}
                      {step.timestamp && (
                        <span className="time-relative">
                          ({getRelativeTime(step.timestamp)})
                        </span>
                      )}
                    </div>

                    {/* 错误信息 */}
                    {step.error && (
                      <div className="timeline-error">
                        <pre>{step.error}</pre>
                      </div>
                    )}

                    {/* 流式内容链接 */}
                    {isCurrent && onStreamContentClick && (
                      <span
                        className="stream-content-link"
                        onClick={(e) => {
                          e.stopPropagation();
                          onStreamContentClick(step.step);
                        }}
                      >
                        查看流式内容 →
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TimelineView;
