import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Moon, Sun, Bot, Sparkles } from 'lucide-react';
import { HealthResponse } from '../services/api';
import { Logo } from './Logo';

interface HeaderProps {
  health: HealthResponse | null;
  healthLoading: boolean;
  healthError: boolean;
  onOpenAssistant?: () => void;
  isAssistantOpen?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  healthError,
  onOpenAssistant,
  isAssistantOpen = false
}) => {
  const [isDark, setIsDark] = useState<boolean>(() => {
    return document.documentElement.classList.contains('dark');
  });

  const toggleTheme = () => {
    const nextDark = !isDark;
    setIsDark(nextDark);
    if (nextDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  };

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-900/95 transition-colors">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        {/* Brand */}
        <NavLink to="/" className="flex items-center space-x-3 group">
          <Logo size="md" className="group-hover:scale-105 transition-transform" />
          <div>
            <span className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
              MediGraph <span className="text-teal-600 dark:text-teal-400">AI</span>
            </span>
            <p className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block">
              Medication Safety & Evidence Research
            </p>
          </div>
        </NavLink>

        {/* Navigation */}
        <nav className="flex items-center space-x-1 sm:space-x-2">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300'
                  : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
              }`
            }
          >
            Dashboard
          </NavLink>
          <NavLink
            to="/history"
            className={({ isActive }) =>
              `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300'
                  : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
              }`
            }
          >
            History
          </NavLink>
        </nav>

        {/* Status, Assistant & Theme Toggle */}
        <div className="flex items-center space-x-2 sm:space-x-3">
          {/* Medicine Assistant Bot Button (Top-Right) */}
          {onOpenAssistant && (
            <button
              type="button"
              onClick={onOpenAssistant}
              aria-label="Open Medicine Assistant"
              className={`relative inline-flex items-center space-x-1.5 rounded-xl px-3 py-2 text-xs font-semibold shadow-sm transition-all ${
                isAssistantOpen
                  ? 'bg-teal-700 text-white ring-2 ring-teal-400 dark:bg-teal-600'
                  : 'bg-teal-600 text-white hover:bg-teal-500 shadow-teal-600/20 active:scale-95'
              }`}
            >
              <Bot className="h-4 w-4" />
              <span className="hidden sm:inline">Medicine Assistant</span>
              <span className="sm:hidden">Assistant</span>
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-300 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400"></span>
              </span>
            </button>
          )}

          {/* Connection Indicator */}
          <div
            className="hidden md:flex items-center space-x-1.5 rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs dark:border-slate-800 dark:bg-slate-800/80"
            title={
              healthError
                ? 'Backend unreachable'
                : health
                ? `Connected to backend (Model: ${health.model})`
                : 'Checking backend...'
            }
          >
            <span
              className={`h-2 w-2 rounded-full ${
                healthError
                  ? 'bg-rose-500 ring-2 ring-rose-200 dark:ring-rose-950'
                  : health
                  ? 'bg-emerald-500 ring-2 ring-emerald-200 dark:ring-emerald-950'
                  : 'bg-amber-400 animate-pulse'
              }`}
            />
            <span className="font-medium text-slate-600 dark:text-slate-300">
              {healthError
                ? 'Offline'
                : health
                ? 'Connected'
                : 'Connecting...'}
            </span>
          </div>

          {/* Theme Toggle Button */}
          <button
            type="button"
            onClick={toggleTheme}
            aria-label="Toggle light and dark theme"
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-500 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200 transition-colors"
          >
            {isDark ? (
              <Sun className="h-5 w-5 text-amber-400" />
            ) : (
              <Moon className="h-5 w-5 text-slate-600" />
            )}
          </button>
        </div>
      </div>
    </header>
  );
};
