/**
 * 全局模型配置栏
 * 放置在页面顶部，所有工作流共享
 */
import { Card } from 'antd';
import { useWorkflow } from '../../contexts/WorkflowContext';
import ModelSelector from './ModelSelector';

function GlobalModelBar() {
  const { setModelConfig } = useWorkflow();

  return (
    <Card size="small" style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <strong>AI 模型配置</strong>
          <div style={{ fontSize: 12, color: '#999' }}>
            选择用于生成内容的 AI 模型
          </div>
        </div>
        <ModelSelector onModelChange={(config) => {
          console.log('模型已切换:', config);
          setModelConfig(config);
        }} />
      </div>
    </Card>
  );
}

export default GlobalModelBar;
