import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import WorkflowProvider from './contexts/WorkflowContext';
import ThemeProvider from './contexts/ThemeContext';
import App from './App';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <WorkflowProvider>
          <App />
        </WorkflowProvider>
      </ThemeProvider>
    </BrowserRouter>
  </StrictMode>
);
