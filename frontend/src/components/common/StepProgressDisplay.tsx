/**
 * StepProgressDisplay - 步骤进度展示组件
 * 使用Steps展示工作流步骤的执行进度，水平分布更均衡
 */
import React from 'react';
import { Steps } from 'antd';
import type { WorkflowStep } from '../../types';
import {
  CheckCircleFilled,
  CloseCircleFilled,
  LoadingOutlined,
  ClockCircleFilled,
} from '@ant-design/icons';
import dayjs from 'dayjs';

interface StepProgressDisplayProps {
  steps: WorkflowStep[];
  currentStep?: string;
  size?: 'default' | 'small';
  className?: string;
}

// 获取步骤状态对应的Steps status
const getStepStatus = (status: WorkflowStep['status']): 'finish' | 'process' | 'error' | 'wait' => {
  switch (status) {
    case 'running':
      return 'process';
    case 'completed':
      return 'finish';
    case 'error':
      return 'error';
    case 'pending':
    default:
      return 'wait';
  }
};

// 获取步骤图标
const getStepIcon = (step: WorkflowStep) => {
  const size = step.status === 'running' ? 16 : 14;

  if (step.status === 'running') {
    return <LoadingOutlined style={{ fontSize: size, color: '#1890ff' }} />;
  }
  if (step.status === 'completed') {
    return <CheckCircleFilled style={{ fontSize: size, color: '#52c41a' }} />;
  }
  if (step.status === 'error') {
    return <CloseCircleFilled style={{ fontSize: size, color: '#ff4d4f' }} />;
  }
  return <ClockCircleFilled style={{ fontSize: size, color: '#d9d9d9' }} />;
};

// 格式化时间戳
const formatTimestamp = (timestamp?: string) => {
  if (!timestamp) return '';
  return dayjs(timestamp).format('HH:mm:ss');
};

const StepProgressDisplay: React.FC<StepProgressDisplayProps> = ({
  steps,
  currentStep = '',
  size = 'default',
  className = '',
}) => {
  // 响应式：小屏幕使用垂直布局
  const [isMobile, setIsMobile] = React.useState(false);

  React.useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const stepsItems = steps.map((step) => {
    const isCurrent = step.step === currentStep;
    const status = getStepStatus(step.status);

    return {
      key: step.step,
      status,
      title: (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontWeight: isCurrent ? 500 : 'normal' }}>{step.name}</span>
          {step.error && (
            <span style={{ color: '#ff4d4f', fontSize: '12px' }}>(失败)</span>
          )}
        </div>
      ),
      description: step.timestamp ? formatTimestamp(step.timestamp) : undefined,
      icon: getStepIcon(step),
    };
  });

  return (
    <div className={`step-progress-display ${className}`}>
      <Steps
        current={steps.findIndex(s => s.step === currentStep)}
        items={stepsItems}
        size={size}
        style={{
          fontSize: size === 'small' ? '12px' : '14px',
        }}
        className={isMobile ? 'steps-vertical' : ''}
      />
    </div>
  );
};

export default StepProgressDisplay;
