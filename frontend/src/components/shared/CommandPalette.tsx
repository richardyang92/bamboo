import { useEffect, useState } from 'react';
import { Command } from 'cmdk';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Pencil,
  FileText,
  Play,
  History,
  Send,
  X,
  Moon,
  Command as CommandIcon,
  Trash2,
} from 'lucide-react';
import { useCommandPalette, shortcuts } from '../../hooks/useKeyboardShortcuts';
import type { BambooShortcutAction, ShortcutItem } from '../../hooks/useKeyboardShortcuts';
import { useWorkflow } from '../../contexts/WorkflowContext';
import { useTheme } from '../../contexts/ThemeContext';
import type { WorkflowType } from '../../types';

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  Pencil,
  FileText,
  Play,
  History,
  Send,
  X,
  Moon,
  Command: CommandIcon,
  Trash2,
};

const getIcon = (iconName?: string) => {
  if (!iconName) return null;
  const Icon = iconMap[iconName];
  return Icon ? <Icon className="w-4 h-4" /> : null;
};

const dispatchBambooShortcut = (action: BambooShortcutAction) => {
  window.dispatchEvent(
    new CustomEvent('bamboo:shortcut', { detail: { action } })
  );
};

interface CommandItemProps {
  shortcut: ShortcutItem;
  onSelect: () => void;
}

function CommandItem({ shortcut, onSelect }: CommandItemProps) {
  return (
    <Command.Item
      value={shortcut.id}
      onSelect={onSelect}
      className="flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer
                 text-[#f8fafc] text-sm
                 hover:bg-white/5 hover:text-[#06b6d4]
                 data-[selected=true]:bg-white/5 data-[selected=true]:text-[#06b6d4]
                 transition-colors duration-150"
    >
      <div className="flex items-center gap-3">
        <span className="text-[#64748b]">{getIcon(shortcut.icon)}</span>
        <span>{shortcut.label}</span>
      </div>
      <kbd className="bg-white/5 text-[#64748b] text-xs px-1.5 py-0.5 rounded font-mono">
        {shortcut.keys}
      </kbd>
    </Command.Item>
  );
}

export default function CommandPalette() {
  const { open, setOpen } = useCommandPalette();
  const navigate = useNavigate();
  const { setCurrentWorkflow } = useWorkflow();
  const { toggleTheme } = useTheme();
  const [activeTheme, setActiveTheme] = useState<'light' | 'dark'>('dark');

  useEffect(() => {
    const updateTheme = () => {
      const isDark = document.documentElement.classList.contains('dark');
      setActiveTheme(isDark ? 'dark' : 'light');
    };
    updateTheme();
    const observer = new MutationObserver(updateTheme);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    });
    return () => observer.disconnect();
  }, []);

  const navigationShortcuts = shortcuts.filter((s) => s.category === 'navigation');
  const actionShortcuts = shortcuts.filter(
    (s) => s.category === 'actions' && s.id !== 'action-palette'
  );

  const handleNavigation = (id: string) => {
    switch (id) {
      case 'nav-drawing':
        setCurrentWorkflow('drawing' as WorkflowType);
        navigate('/');
        break;
      case 'nav-document':
        setCurrentWorkflow('document_with_images' as WorkflowType);
        navigate('/');
        break;
      case 'nav-manim':
        setCurrentWorkflow('manim' as WorkflowType);
        navigate('/');
        break;
      case 'nav-history':
        navigate('/history');
        break;
    }
    setOpen(false);
  };

  const handleAction = (id: string) => {
    switch (id) {
      case 'action-submit':
        dispatchBambooShortcut('submit');
        break;
      case 'action-escape':
        dispatchBambooShortcut('escape');
        break;
      case 'action-theme':
        toggleTheme();
        break;
    }
    setOpen(false);
  };

  const handleSelect = (value: string) => {
    const shortcut = shortcuts.find((s) => s.id === value);
    if (!shortcut) return;

    if (shortcut.category === 'navigation') {
      handleNavigation(shortcut.id);
    } else {
      handleAction(shortcut.id);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
            onClick={() => setOpen(false)}
          />
          <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] pointer-events-none">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.15, ease: 'easeOut' }}
              className="w-full max-w-lg pointer-events-auto"
            >
              <Command
                className="bg-[#0f172a]/95 backdrop-blur-xl border border-white/10 rounded-xl
                           shadow-2xl shadow-black/40 overflow-hidden"
                loop
              >
                <div className="flex items-center gap-3 px-4 py-3 border-b border-white/10">
                  <CommandIcon className="w-5 h-5 text-[#64748b]" />
                  <Command.Input
                    placeholder="Type a command or search..."
                    className="flex-1 bg-transparent text-[#f8fafc] text-sm placeholder:text-[#64748b]
                               focus:outline-none"
                  />
                  <kbd className="bg-white/5 text-[#64748b] text-xs px-1.5 py-0.5 rounded font-mono">
                    ESC
                  </kbd>
                </div>
                <Command.List className="max-h-[400px] overflow-y-auto py-2">
                  <Command.Empty className="px-4 py-8 text-center text-sm text-[#64748b]">
                    No commands found.
                  </Command.Empty>

                  <Command.Group
                    heading="Navigation"
                    className="px-2"
                  >
                    <div className="text-[#64748b] text-xs uppercase tracking-wider px-2 py-1.5 mb-1">
                      Navigation
                    </div>
                    {navigationShortcuts.map((shortcut) => (
                      <CommandItem
                        key={shortcut.id}
                        shortcut={shortcut}
                        onSelect={() => handleSelect(shortcut.id)}
                      />
                    ))}
                  </Command.Group>

                  <div className="h-px bg-white/5 mx-2 my-2" />

                  <Command.Group
                    heading="Actions"
                    className="px-2"
                  >
                    <div className="text-[#64748b] text-xs uppercase tracking-wider px-2 py-1.5 mb-1">
                      Actions
                    </div>
                    {actionShortcuts.map((shortcut) => (
                      <CommandItem
                        key={shortcut.id}
                        shortcut={shortcut}
                        onSelect={() => handleSelect(shortcut.id)}
                      />
                    ))}
                    <Command.Item
                      value="clear-history"
                      onSelect={() => {
                        dispatchBambooShortcut('escape');
                        setOpen(false);
                      }}
                      className="flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer
                                 text-[#f8fafc] text-sm
                                 hover:bg-white/5 hover:text-[#06b6d4]
                                 data-[selected=true]:bg-white/5 data-[selected=true]:text-[#06b6d4]
                                 transition-colors duration-150"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-[#64748b]"><Trash2 className="w-4 h-4" /></span>
                        <span>Clear History</span>
                      </div>
                    </Command.Item>
                  </Command.Group>
                </Command.List>

                <div className="flex items-center justify-between px-4 py-2 border-t border-white/10
                                bg-white/[0.02] text-[#64748b] text-xs">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1.5">
                      <kbd className="bg-white/5 px-1 py-0.5 rounded font-mono">↑↓</kbd>
                      <span>Navigate</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <kbd className="bg-white/5 px-1 py-0.5 rounded font-mono">↵</kbd>
                      <span>Select</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>Theme:</span>
                    <span className={activeTheme === 'dark' ? 'text-[#06b6d4]' : 'text-amber-400'}>
                      {activeTheme === 'dark' ? 'Dark' : 'Light'}
                    </span>
                  </div>
                </div>
              </Command>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
