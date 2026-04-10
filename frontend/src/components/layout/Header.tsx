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
    : workflowTitles[state.currentWorkflow] || 'Bamboo AI';

  return (
    <header
      className={`relative flex items-center justify-between h-12 px-5 shrink-0 glass-header transition-colors duration-200 ${
        mode === 'dark' ? '' : 'bg-white/60'
      }`}
    >
      <h1 className="text-base font-medium text-[var(--color-text-primary)] tracking-wide">
        {title}
      </h1>
      <ModelSelector />
      <div
        className="absolute bottom-0 left-0 right-0 h-px pointer-events-none"
        style={{
          background:
            mode === 'dark'
              ? 'linear-gradient(90deg, transparent 0%, rgba(6, 182, 212, 0.3) 50%, transparent 100%)'
              : 'linear-gradient(90deg, transparent 0%, rgba(6, 182, 212, 0.2) 50%, transparent 100%)',
        }}
      />
    </header>
  );
}

export default Header;
