/**
 * WorkflowViewToolbar - 工作流视图工具栏
 * 提供视图模式切换、展开/折叠控制等功能
 */
import React from 'react';
import { Space, Segmented, Button, Tooltip, Progress, Divider } from 'antd';
import {
  AppstoreOutlined,
  NodeIndexOutlined,
  FieldTimeOutlined,
  DownOutlined,
  UpOutlined,
  CompressOutlined,
  BorderOutlined,
} from '@ant-design/icons';
import type { WorkflowViewMode } from '../../../types';
import './WorkflowViewToolbar.css';

interface WorkflowViewToolbarProps {
  viewMode: WorkflowViewMode;
  onViewModeChange: (mode: WorkflowViewMode) => void;
  completedCount?: number;
  totalCount?: number;
  allExpanded: boolean;
  onToggleExpandAll: () => void;
  compactMode: boolean;
  onToggleCompactMode: () => void;
  className?: string;
}

// 视图模式选项
const VIEW_MODE_OPTIONS = [
  { label: '卡片', value: 'cards' as const, icon: <AppstoreOutlined /> },
  { label: '流程图', value: 'graph' as const, icon: <NodeIndexOutlined /> },
  { label: '时间线', value: 'timeline' as const, icon: <FieldTimeOutlined /> },
];

const WorkflowViewToolbar: React.FC<WorkflowViewToolbarProps> = ({
  viewMode,
  onViewModeChange,
  completedCount = 0,
  totalCount = 0,
  allExpanded,
  onToggleExpandAll,
  compactMode,
  onToggleCompactMode,
  className = '',
}) => {
  // 计算进度百分比
  const progressPercent = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  return (
    <div className={`workflow-view-toolbar ${className}`}>
      <div className="toolbar-main">
        <Space size="middle" wrap>
          {/* 视图模式切换器 */}
          <Segmented
            options={VIEW_MODE_OPTIONS.map(opt => ({
              label: (
                <Tooltip title={opt.label}>
                  <span className="view-mode-option">
                    {opt.icon}
                    <span className="view-label">{opt.label}</span>
                  </span>
                </Tooltip>
              ),
              value: opt.value,
            }))}
            value={viewMode}
            onChange={onViewModeChange}
          />

          <Divider orientation="vertical" />

          {/* 进度指示器 */}
          {totalCount > 0 && (
            <Space size="small" align="center">
              <Progress
                type="circle"
                percent={Math.round(progressPercent)}
                size={32}
                strokeWidth={4}
                format={() => `${completedCount}/${totalCount}`}
                className="progress-indicator"
              />
              <span className="progress-text">
                {progressPercent === 100 ? '全部完成' : `${completedCount}/${totalCount} 完成`}
              </span>
            </Space>
          )}
        </Space>

        {/* 右侧控制按钮组 */}
        <Space size="small">
          {/* 展开/折叠控制（仅卡片和时间线视图） */}
          {(viewMode === 'cards' || viewMode === 'timeline') && (
            <Tooltip title={allExpanded ? '全部折叠' : '全部展开'}>
              <Button
                type="text"
                size="small"
                icon={allExpanded ? <UpOutlined /> : <DownOutlined />}
                onClick={onToggleExpandAll}
                className="control-btn"
              >
                {allExpanded ? '折叠' : '展开'}
              </Button>
            </Tooltip>
          )}

          {/* 紧凑模式切换（仅卡片视图） */}
          {viewMode === 'cards' && (
            <Tooltip title={compactMode ? '切换到正常模式' : '切换到紧凑模式'}>
              <Button
                type="text"
                size="small"
                icon={compactMode ? <BorderOutlined /> : <CompressOutlined />}
                onClick={onToggleCompactMode}
                className={`control-btn ${compactMode ? 'compact-active' : ''}`}
              />
            </Tooltip>
          )}
        </Space>
      </div>
    </div>
  );
};

export default WorkflowViewToolbar;
