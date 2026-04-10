import { Link, useLocation, useNavigate } from 'react-router-dom';
import { BarChart3, FileText, Video, History, Sun, Moon } from 'lucide-react';
import { useWorkflow } from '../../contexts/WorkflowContext';
import { useTheme } from '../../contexts/ThemeContext';
import type { WorkflowType } from '../../types';

interface NavItem {
  type: 'workflow' | 'route';
  workflow?: WorkflowType;
  route?: string;
  icon: React.ElementType;
  label: string;
}

const navItems: NavItem[] = [
  { type: 'workflow', workflow: 'drawing', icon: BarChart3, label: '智能绘图' },
  { type: 'workflow', workflow: 'document_with_images', icon: FileText, label: '文档生成' },
  { type: 'workflow', workflow: 'manim', icon: Video, label: '数学动画' },
  { type: 'route', route: '/history', icon: History, label: '历史记录' },
];

function Sidebar() {
  const { state, setCurrentWorkflow } = useWorkflow();
  const { mode, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();

  const handleWorkflowClick = (workflow: WorkflowType) => {
    setCurrentWorkflow(workflow);
    if (location.pathname !== '/') {
      navigate('/');
    }
  };

  const isActive = (item: NavItem): boolean => {
    if (item.type === 'workflow') {
      return state.currentWorkflow === item.workflow && location.pathname !== '/history';
    }
    if (item.type === 'route' && item.route) {
      return location.pathname === item.route;
    }
    return false;
  };

  return (
    <aside
      className={`group h-full flex flex-col shrink-0 glass-sidebar overflow-hidden transition-all duration-300 w-[72px] hover:w-[200px]`}
    >
      <nav className="flex-1 flex flex-col gap-1 py-4 px-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item);

          const buttonContent = (
            <div
              className={`relative flex items-center w-full h-11 rounded-lg transition-all duration-200 cursor-pointer ${
                active
                  ? 'bg-[var(--color-accent)]/10'
                  : 'hover:bg-[var(--color-bg-card)]/50'
              }`}
            >
              {active && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-6 bg-[var(--color-accent)] rounded-r" />
              )}
              <div className="flex items-center justify-center w-14 shrink-0">
                <Icon
                  strokeWidth={active ? 2.5 : 1.5}
                  className={`w-5 h-5 transition-colors ${
                    active
                      ? 'text-[var(--color-accent)]'
                      : 'text-[var(--color-text-muted)] group-hover:text-[var(--color-text-secondary)]'
                  }`}
                />
              </div>
              <span
                className={`whitespace-nowrap text-sm font-medium transition-all duration-300 overflow-hidden max-w-0 group-hover:max-w-[120px] ${
                  active
                    ? 'text-[var(--color-accent)]'
                    : 'text-[var(--color-text-muted)] group-hover:text-[var(--color-text-secondary)]'
                }`}
              >
                {item.label}
              </span>
            </div>
          );

          if (item.type === 'workflow' && item.workflow) {
            return (
              <button
                key={item.label}
                onClick={() => handleWorkflowClick(item.workflow!)}
                className="w-full"
              >
                {buttonContent}
              </button>
            );
          }

          return (
            <Link
              key={item.label}
              to={item.route!}
              className="w-full"
            >
              {buttonContent}
            </Link>
          );
        })}
      </nav>

      <div className="py-4 px-2">
        <div className="h-px bg-[var(--color-border)] mx-2 mb-4" />
        <button
          onClick={toggleTheme}
          className="relative flex items-center w-full h-11 rounded-lg transition-all duration-200 cursor-pointer hover:bg-[var(--color-bg-card)]/50"
        >
          <div className="flex items-center justify-center w-14 shrink-0">
            {mode === 'dark' ? (
              <Sun
                strokeWidth={1.5}
                className="w-5 h-5 text-[var(--color-text-secondary)] group-hover:text-[var(--color-text-primary)] transition-colors"
              />
            ) : (
              <Moon
                strokeWidth={1.5}
                className="w-5 h-5 text-[var(--color-text-muted)] group-hover:text-[var(--color-text-secondary)] transition-colors"
              />
            )}
          </div>
          <span className="whitespace-nowrap text-sm font-medium text-[var(--color-text-muted)] group-hover:text-[var(--color-text-secondary)] transition-colors overflow-hidden max-w-0 group-hover:max-w-[120px]">
            {mode === 'dark' ? '浅色主题' : '深色主题'}
          </span>
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
