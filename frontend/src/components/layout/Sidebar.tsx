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
  { type: 'workflow', workflow: 'drawing', icon: BarChart3, label: '绘图' },
  { type: 'workflow', workflow: 'document_with_images', icon: FileText, label: '文档' },
  { type: 'workflow', workflow: 'manim', icon: Video, label: '动画' },
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
      className={`w-14 h-full flex flex-col shrink-0 transition-colors duration-200 ${
        mode === 'dark' ? 'bg-[var(--color-bg-dark)]' : 'bg-white'
      }`}
    >
      <nav className="flex-1 flex flex-col gap-1 py-3">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item);

          const buttonContent = (
            <div className="relative flex items-center justify-center w-10 h-10 rounded-lg transition-colors">
              {active && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-[var(--color-accent)] rounded-r" />
              )}
              <Icon
                className={`w-5 h-5 transition-colors ${
                  active
                    ? 'text-[var(--color-accent)]'
                    : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'
                }`}
              />
            </div>
          );

          if (item.type === 'workflow' && item.workflow) {
            return (
              <button
                key={item.label}
                onClick={() => handleWorkflowClick(item.workflow!)}
                className="flex items-center justify-center group"
                title={item.label}
              >
                {buttonContent}
              </button>
            );
          }

          return (
            <Link
              key={item.label}
              to={item.route!}
              className="flex items-center justify-center group"
              title={item.label}
            >
              {buttonContent}
            </Link>
          );
        })}
      </nav>

      <div className="py-3 flex justify-center">
        <button
          onClick={toggleTheme}
          className="relative flex items-center justify-center w-10 h-10 rounded-lg transition-colors hover:bg-[var(--color-bg-card)]/50"
          title={mode === 'dark' ? '切换到浅色主题' : '切换到深色主题'}
        >
          {mode === 'dark' ? (
            <Sun className="w-5 h-5 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors" />
          ) : (
            <Moon className="w-5 h-5 text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors" />
          )}
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
