/**
 * Manim 动画工作流面板 - 增强版
 * 集成实时状态展示、步骤进度和流式内容
 */
import { useState } from 'react';
import { Card, Input, Button, Space, Tabs, Select, message } from 'antd';
import { SendOutlined, LoadingOutlined } from '@ant-design/icons';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useWorkflow } from '../../contexts/WorkflowContext';
import * as api from '../../services/api';
import WorkflowStatusIndicator from '../common/WorkflowStatusIndicator';
import WorkflowExecutionTracker from '../common/WorkflowExecutionTracker';
import StreamContentList from '../common/StreamContentList';
import ResultPlaceholder from '../common/ResultPlaceholder';

const { TextArea } = Input;

function ManimPanel() {
  const {
    status,
    steps,
    currentStep,
    result,
    error,
    connectionState,
    currentNode,
    isStreaming,
    streamContent,
    reasoningContent,  // 新增：获取思考内容
  } = useWebSocket('manim');

  const { state: { modelConfig } } = useWorkflow();
  const [prompt, setPrompt] = useState('');
  const [quality, setQuality] = useState<'low' | 'medium' | 'high' | '4k'>('medium');

  const handleStart = async () => {
    if (!prompt.trim()) {
      message.warning('请输入动画需求');
      return;
    }

    try {
      await api.startManimWorkflow(prompt, quality, {
        provider: modelConfig.provider,
        model: modelConfig.model,
        enable_thinking: modelConfig.enable_thinking,
      });
      message.success('动画工作流已启动');
    } catch (err) {
      message.error(err instanceof Error ? err.message : '启动失败');
    }
  };

  const handleClear = async () => {
    try {
      await api.clearManimHistory();
      message.success('历史记录已清除');
    } catch (err) {
      message.error(err instanceof Error ? err.message : '清除失败');
    }
  };

  const isRunning = status === 'running';

  const qualityOptions = [
    { label: '低质量 (360p)', value: 'low' },
    { label: '中等质量 (480p)', value: 'medium' },
    { label: '高质量 (720p)', value: 'high' },
    { label: '4K 质量 (2160p)', value: '4k' },
  ];

  return (
    <div className="workflow-panel">
      <div className="workflow-panel-left">
        <Space style={{ width: '100%' }} direction="vertical" size="large">
          {/* 输入区域 - 带状态指示器 */}
          <Card
            title={
              <Space>
                <span>动画需求</span>
                <WorkflowStatusIndicator
                  workflowStatus={status}
                  connectionState={connectionState}
                  workflowType="manim"
                />
              </Space>
            }
          >
            <Space style={{ width: '100%' }} direction="vertical">
              <TextArea
                rows={4}
                placeholder="请描述你想要的数学动画，例如：展示正弦函数的生成过程"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={isRunning}
              />
              <Space>
                <span>渲染质量：</span>
                <Select
                  value={quality}
                  onChange={setQuality}
                  style={{ width: 200 }}
                  disabled={isRunning}
                  options={qualityOptions}
                />
              </Space>
              <Space style={{ width: '100%' }}>
                <Button
                  type="primary"
                  icon={isRunning ? <LoadingOutlined /> : <SendOutlined />}
                  onClick={handleStart}
                  disabled={isRunning}
                >
                  {isRunning ? '渲染中...' : '开始渲染'}
                </Button>
                <Button onClick={handleClear} disabled={isRunning}>
                  清除历史
                </Button>
              </Space>
            </Space>
          </Card>

          {/* 流式内容展示 */}
          <StreamContentList
            steps={steps}
            streamContent={streamContent}
            reasoningContent={reasoningContent}
            currentNode={currentNode}
            isStreaming={isStreaming}
            workflowType="manim"
          />
        </Space>
      </div>

      {/* 右侧结果区域 */}
      <div className="workflow-panel-right">
        {result && result.video_url ? (
          /* 优先：显示生成结果 */
          <Card title="生成结果">
            <Tabs
              items={[
                {
                  key: 'video',
                  label: '视频',
                  children: (
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 0 }}>
                      <video
                        src={result.video_url}
                        controls
                        style={{ maxWidth: '100%', maxHeight: 'calc(100vh - 320px)' }}
                      />
                    </div>
                  ),
                },
                {
                  key: 'code',
                  label: '代码',
                  children: (
                    <pre style={{ background: '#f5f5f5', padding: '16px', borderRadius: '4px' }}>
                      {result.generated_code}
                    </pre>
                  ),
                },
              ]}
            />
          </Card>
        ) : steps.length > 0 ? (
          /* 有步骤历史：显示执行进度 */
          <Card title="执行进度">
            <WorkflowExecutionTracker
              steps={steps}
              currentStep={currentStep}
              workflowType="manim"
            />
          </Card>
        ) : (
          /* 默认：显示占位符 */
          <Card title="生成结果">
            <ResultPlaceholder type="manim" error={error} />
          </Card>
        )}
      </div>
    </div>
  );
}

export default ManimPanel;
