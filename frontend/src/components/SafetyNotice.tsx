import React from 'react';
import { AlertCircle } from 'lucide-react';

export const SafetyNotice: React.FC = () => {
  return (
    <aside className="border-t border-slate-200 bg-slate-100/80 px-4 py-3 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-900/80 dark:text-slate-400">
      <div className="mx-auto flex max-w-7xl items-start space-x-2.5">
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-teal-600 dark:text-teal-400" />
        <p className="leading-relaxed">
          <strong className="font-semibold text-slate-800 dark:text-slate-200">
            Important Medical Safety Notice:
          </strong>{' '}
          MediGraph AI is an educational decision-support prototype, not a medical device or a substitute for a licensed doctor or pharmacist.
          Extracted medicine names must be confirmed by the user. The system must not tell users to start, stop, replace, or change the dose of a medicine.
          Alternative medicines are research candidates for clinician review only. Never describe a medicine or alternative as &ldquo;risk-free&rdquo; or guaranteed safe.
        </p>
      </div>
    </aside>
  );
};
