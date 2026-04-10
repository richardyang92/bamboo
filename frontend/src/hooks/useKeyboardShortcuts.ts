/**
 * useKeyboardShortcuts.ts
 * Keyboard shortcuts registry and hook for the Bamboo platform
 */
import { useState, useEffect, useRef } from 'react';
import { useHotkeys } from 'react-hotkeys-hook';

// =============================================================================
// Types
// =============================================================================

export interface ShortcutItem {
  id: string;
  label: string;
  keys: string;
  category: 'navigation' | 'actions';
  icon?: string;
  hotkey: string; // The actual hotkey combination for react-hotkeys-hook
}

export interface UseCommandPaletteReturn {
  open: boolean;
  setOpen: (open: boolean) => void;
  shortcuts: ShortcutItem[];
}

// =============================================================================
// Custom Events
// =============================================================================

export type BambooShortcutAction =
  | 'submit'
  | 'escape'
  | 'switch-drawing'
  | 'switch-document'
  | 'switch-manim'
  | 'go-history'
  | 'toggle-theme';

const dispatchBambooShortcut = (action: BambooShortcutAction) => {
  window.dispatchEvent(
    new CustomEvent('bamboo:shortcut', { detail: { action } })
  );
};

// =============================================================================
// Shortcut Registry
// =============================================================================

export const shortcuts: ShortcutItem[] = [
  // Navigation shortcuts
  {
    id: 'nav-drawing',
    label: 'Go to Drawing',
    keys: '⌘1',
    category: 'navigation',
    icon: 'Pencil',
    hotkey: 'mod+1',
  },
  {
    id: 'nav-document',
    label: 'Go to Document',
    keys: '⌘2',
    category: 'navigation',
    icon: 'FileText',
    hotkey: 'mod+2',
  },
  {
    id: 'nav-manim',
    label: 'Go to Manim',
    keys: '⌘3',
    category: 'navigation',
    icon: 'Play',
    hotkey: 'mod+3',
  },
  {
    id: 'nav-history',
    label: 'Go to History',
    keys: '⌘4',
    category: 'navigation',
    icon: 'History',
    hotkey: 'mod+4',
  },
  // Action shortcuts
  {
    id: 'action-submit',
    label: 'Submit Workflow',
    keys: '⌘Enter',
    category: 'actions',
    icon: 'Send',
    hotkey: 'mod+enter',
  },
  {
    id: 'action-escape',
    label: 'Stop / Close',
    keys: 'Esc',
    category: 'actions',
    icon: 'X',
    hotkey: 'escape',
  },
  {
    id: 'action-theme',
    label: 'Toggle Theme',
    keys: '⌘⇧T',
    category: 'actions',
    icon: 'Moon',
    hotkey: 'mod+shift+t',
  },
  {
    id: 'action-palette',
    label: 'Open Command Palette',
    keys: '⌘K',
    category: 'actions',
    icon: 'Command',
    hotkey: 'mod+k',
  },
];

// =============================================================================
// Hook: useCommandPalette
// =============================================================================

export function useCommandPalette(): UseCommandPaletteReturn {
  const [open, setOpen] = useState(false);

  // Cmd+K: Always works, even in form elements
  useHotkeys(
    'mod+k',
    (e) => {
      e.preventDefault();
      setOpen((prev) => !prev);
    },
    { enableOnFormTags: true, preventDefault: true }
  );

  // Escape: Close palette if open
  useHotkeys(
    'escape',
    () => {
      if (open) {
        setOpen(false);
      } else {
        dispatchBambooShortcut('escape');
      }
    },
    { enableOnFormTags: true }
  );

  return { open, setOpen, shortcuts };
}

// =============================================================================
// Hook: useGlobalShortcuts
// =============================================================================

export function useGlobalShortcuts(): void {
  // Cmd/Ctrl+Enter: Submit workflow (disabled in form elements)
  useHotkeys(
    'mod+enter',
    (e) => {
      e.preventDefault();
      dispatchBambooShortcut('submit');
    },
    { enableOnFormTags: false, preventDefault: true }
  );

  // Cmd/Ctrl+1: Switch to Drawing
  useHotkeys(
    'mod+1',
    (e) => {
      e.preventDefault();
      dispatchBambooShortcut('switch-drawing');
    },
    { enableOnFormTags: false, preventDefault: true }
  );

  // Cmd/Ctrl+2: Switch to Document
  useHotkeys(
    'mod+2',
    (e) => {
      e.preventDefault();
      dispatchBambooShortcut('switch-document');
    },
    { enableOnFormTags: false, preventDefault: true }
  );

  // Cmd/Ctrl+3: Switch to Manim
  useHotkeys(
    'mod+3',
    (e) => {
      e.preventDefault();
      dispatchBambooShortcut('switch-manim');
    },
    { enableOnFormTags: false, preventDefault: true }
  );

  // Cmd/Ctrl+4: Go to History
  useHotkeys(
    'mod+4',
    (e) => {
      e.preventDefault();
      dispatchBambooShortcut('go-history');
    },
    { enableOnFormTags: false, preventDefault: true }
  );

  // Cmd/Ctrl+Shift+T: Toggle Theme
  useHotkeys(
    'mod+shift+t',
    (e) => {
      e.preventDefault();
      dispatchBambooShortcut('toggle-theme');
    },
    { enableOnFormTags: false, preventDefault: true }
  );
}

// =============================================================================
// Hook: useBambooShortcut
// =============================================================================

export function useBambooShortcut(
  action: BambooShortcutAction,
  callback: () => void
): void {
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  });

  useEffect(() => {
    const handler = (e: CustomEvent<{ action: BambooShortcutAction }>) => {
      if (e.detail.action === action) {
        callbackRef.current();
      }
    };

    window.addEventListener('bamboo:shortcut', handler as EventListener);
    return () => {
      window.removeEventListener('bamboo:shortcut', handler as EventListener);
    };
  }, [action]);
}
