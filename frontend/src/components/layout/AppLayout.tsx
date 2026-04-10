import { useTheme } from '../../contexts/ThemeContext';
import Sidebar from './Sidebar';
import Header from './Header';

interface AppLayoutProps {
  children: React.ReactNode;
}

function AppLayout({ children }: AppLayoutProps) {
  const { mode } = useTheme();

  return (
    <div
      className={`flex h-screen transition-colors duration-200 ${
        mode === 'dark' ? 'bg-gradient-main' : 'bg-gray-50'
      }`}
    >
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <Header />
        <main className="flex-1 overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  );
}

export default AppLayout;
