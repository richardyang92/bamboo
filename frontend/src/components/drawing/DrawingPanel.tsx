/**
 * 绘图工作流面板 - 增强版
 * 集成实时状态展示、步骤进度和流式内容
 */
import { useState } from 'react';
import { Card, Input, Button, Space, Image, Tabs, message } from 'antd';
import { SendOutlined, LoadingOutlined } from '@ant-design/icons';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useWorkflow } from '../../contexts/WorkflowContext';
import * as api from '../../services/api';
import WorkflowStatusIndicator from '../common/WorkflowStatusIndicator';
import WorkflowExecutionTracker from '../common/WorkflowExecutionTracker';
import WorkflowTimeline from '../common/WorkflowTimeline';
import EmptyView from '../common/EmptyView';
import ResultPlaceholder from '../common/ResultPlaceholder';

const { TextArea } = Input;

function DrawingPanel() {
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
  } = useWebSocket('drawing');

  const { state: { modelConfig } } = useWorkflow();
  const [prompt, setPrompt] = useState('');

  const handleStart = async () => {
    if (!prompt.trim()) {
      message.warning('请输入绘图需求');
      return;
    }

    try {
      await api.startDrawingWorkflow(prompt, {
        provider: modelConfig.provider,
        model: modelConfig.model,
        enable_thinking: modelConfig.enable_thinking,
      });
      message.success('绘图工作流已启动');
    } catch (err) {
      message.error(err instanceof Error ? err.message : '启动失败');
    }
  };

  const handleClear = async () => {
    try {
      await api.clearDrawingHistory();
      message.success('历史记录已清除');
    } catch (err) {
      message.error(err instanceof Error ? err.message : '清除失败');
    }
  };

  const isRunning = status === 'running';

  return (
    <div className="workflow-panel">
      <div className="workflow-panel-left">
        <Space style={{ width: '100%' }} orientation="vertical" size="large">
          {/* 输入区域 - 带状态指示器 */}
          <Card
            title={
              <Space>
                <span>绘图需求</span>
                <WorkflowStatusIndicator
                  workflowStatus={status}
                  connectionState={connectionState}
                  workflowType="drawing"
                />
              </Space>
            }
          >
            <Space style={{ width: '100%' }} orientation="vertical">
              <TextArea
                rows={4}
                placeholder="请描述你想要绘制的图表，例如：绘制一个正弦函数图像"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={isRunning}
              />
              <Space style={{ width: '100%' }}>
                <Button
                  type="primary"
                  icon={isRunning ? <LoadingOutlined /> : <SendOutlined />}
                  onClick={handleStart}
                  disabled={isRunning}
                >
                  {isRunning ? '生成中...' : '开始生成'}
                </Button>
                <Button onClick={handleClear} disabled={isRunning}>
                  清除历史
                </Button>
              </Space>
            </Space>
          </Card>

          {/* 工作流执行时间线 */}
          <Card title="执行时间线">
            {steps.filter(s => s.status !== 'pending').length > 0 ? (
              <WorkflowTimeline
                steps={steps}
                streamContent={streamContent}
                reasoningContent={reasoningContent}
                currentNode={currentNode}
                isStreaming={isStreaming}
                workflowType="drawing"
              />
            ) : (
              <EmptyView workflowType="drawing" />
            )}
          </Card>
        </Space>
      </div>

      {/* 右侧结果区域 */}
      <div className="workflow-panel-right">
        {result && result.image_url ? (
          /* 优先：显示生成结果 */
          <Card title="生成结果">
            <Tabs
              items={[
                {
                  key: 'image',
                  label: '图片',
                  children: (
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 0 }}>
                      <Image
                        src={result.image_url}
                        alt="生成的图表"
                        style={{ maxHeight: 'calc(100vh - 320px)', maxWidth: '100%', objectFit: 'contain' }}
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
              workflowType="drawing"
            />
          </Card>
        ) : (
          /* 默认：显示占位符 */
          <Card title="生成结果">
            <ResultPlaceholder type="drawing" error={error} />
          </Card>
        )}
      </div>
    </div>
  );
}

export default DrawingPanel;
