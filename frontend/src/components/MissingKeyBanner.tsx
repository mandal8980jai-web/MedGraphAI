import React from 'react';
import { KeyRound } from 'lucide-react';

interface MissingKeyBannerProps {
  show: boolean;
}

export const MissingKeyBanner: React.FC<MissingKeyBannerProps> = ({ show }) => {
  if (!show) return null;

  return (
    <div className="border-b border-amber-300 bg-amber-50 px-4 py-3 text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-200">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="rounded-full bg-amber-200 p-1.5 dark:bg-amber-900/80">
            <KeyRound className="h-4 w-4 text-amber-800 dark:text-amber-200" />
          </div>
          <div>
            <p className="text-sm font-semibold">
              Add your Gemini key to backend/.env and restart the backend.
            </p>
            <p className="text-xs text-amber-700 dark:text-amber-300/80">
              Deterministic safety checks, document parsing, and PDF reports remain operational. AI research features will be enabled once your key is set.
            </p>
          </div>
        </div>
        <div className="hidden sm:flex items-center text-xs font-medium text-amber-800 dark:text-amber-300 bg-amber-100 dark:bg-amber-900/50 px-2.5 py-1 rounded">
          Setup Required
        </div>
      </div>
    </div>
  );
};
