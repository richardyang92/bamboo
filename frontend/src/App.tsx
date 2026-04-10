import { Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { WorkflowProvider } from './contexts/WorkflowContext';
import { Toaster } from 'sonner';
import 'sonner/dist/styles.css';
import HomePage from './pages/HomePage';
import HistoryPage from './pages/HistoryPage';
import CommandPalette from './components/shared/CommandPalette';

function App() {
  return (
    <ThemeProvider>
        <WorkflowProvider>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
          <CommandPalette />
          <Toaster
          position="top-right"
          richColors
          theme="dark"
          toastOptions={{
            style: {
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-primary)',
            },
          }}
        />
      </WorkflowProvider>
    </ThemeProvider>
  );
}

export default App;
