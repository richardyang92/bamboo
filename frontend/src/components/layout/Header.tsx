import { useLocation } from 'react-router-dom';
import { useWorkflow } from '../../contexts/WorkflowContext';
import { useTheme } from '../../contexts/ThemeContext';
import ModelSelector from '../shared/ModelSelector';
import type { WorkflowType } from '../../types';

const workflowTitles: Record<WorkflowType, string> = {
  drawing: '智能绘图',
  document_with_images: '文档生成',
  manim: '数学动画',
};

function Header() {
  const { state } = useWorkflow();
  const { mode } = useTheme();
  const location = useLocation();

  const isHistoryPage = location.pathname === '/history';
  
  const title = isHistoryPage
    ? '历史记录'
    : workflowTitles[state.currentWorkflow] || 'Bamboo';

  return (
    <header
      className={`flex items-center justify-between h-10 px-4 shrink-0 transition-colors duration-200 ${
        mode === 'dark'
          ? 'bg-[var(--color-bg-card)] border-b border-[var(--color-border)]'
          : 'bg-gray-50 border-b border-gray-200'
      }`}
    >
      <h1 className="text-sm font-medium text-[var(--color-text-primary)]">
        {title}
      </h1>
      <ModelSelector />
    </header>
  );
}

export default Header;
