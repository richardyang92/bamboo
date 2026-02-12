/**
 * ThemeContext
 * 管理应用的主题（深色/浅色模式）
 */
import { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import type { ReactNode } from 'react';

type ThemeMode = 'light' | 'dark';

interface ThemeContextValue {
  mode: ThemeMode;
  toggleTheme: () => void;
  setTheme: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

/**
 * ThemeProvider 组件
 */
export function ThemeProvider({ children }: ThemeProviderProps) {
  // 从 localStorage 读取主题，默认为 light
  const [mode, setModeState] = useState<ThemeMode>(() => {
    const savedMode = localStorage.getItem('theme') as ThemeMode;
    return savedMode || 'light';
  });

  // 切换主题
  const toggleTheme = useCallback(() => {
    setModeState((prevMode) => {
      const newMode: ThemeMode = prevMode === 'light' ? 'dark' : 'light';
      localStorage.setItem('theme', newMode);
      return newMode;
    });
  }, []);

  // 设置主题
  const setTheme = useCallback((newMode: ThemeMode) => {
    localStorage.setItem('theme', newMode);
    setModeState(newMode);
  }, []);

  // 应用主题到 DOM
  useEffect(() => {
    const root = document.documentElement;
    if (mode === 'dark') {
      root.classList.add('dark');
      root.setAttribute('data-theme', 'dark');
    } else {
      root.classList.remove('dark');
      root.setAttribute('data-theme', 'light');
    }
  }, [mode]);

  // Context 值
  const value = useMemo<ThemeContextValue>(
    () => ({
      mode,
      toggleTheme,
      setTheme,
    }),
    [mode, toggleTheme, setTheme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

/**
 * useTheme Hook
 */
export const useTheme = (): ThemeContextValue => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};

export default ThemeProvider;
