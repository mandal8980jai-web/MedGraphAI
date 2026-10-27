import React, { useState } from 'react';
import { PatientContext } from '../../types';
import { User, ChevronDown, ChevronUp, Info } from 'lucide-react';

interface PatientContextFormProps {
  context: PatientContext;
  onChange: (updated: PatientContext) => void;
}

export const PatientContextForm: React.FC<PatientContextFormProps> = ({
  context,
  onChange,
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(true);

  const updateField = (field: keyof PatientContext, value: any) => {
    onChange({
      ...context,
      [field]: value === '' ? null : value,
    });
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900 mt-6">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between text-left"
      >
        <div className="flex items-center space-x-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-50 text-teal-600 dark:bg-teal-950/60 dark:text-teal-400">
            <User className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center space-x-2">
              <span>Patient Details</span>
              <span className="rounded bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-[10px] font-normal text-slate-500">
                Optional
              </span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Providing patient background helps evaluate dosage safety and medical context.
            </p>
          </div>
        </div>

        <div className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
          {isOpen ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
        </div>
      </button>

      {isOpen && (
        <div className="mt-5 grid grid-cols-1 gap-4 border-t border-slate-100 pt-5 dark:border-slate-800 sm:grid-cols-2 lg:grid-cols-3">
          {/* Age */}
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Patient Age
            </label>
            <input
              type="number"
              min="0"
              max="130"
              value={context.age ?? ''}
              onChange={(e) =>
                updateField('age', e.target.value ? parseInt(e.target.value, 10) : null)
              }
              placeholder="e.g. 45"
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-900 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
              Used to check age-specific cautions (pediatric or geriatric dosing).
            </p>
          </div>

          {/* Reason / Condition */}
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Reason for Medicine / Symptoms
            </label>
            <input
              type="text"
              value={context.reason ?? ''}
              onChange={(e) => updateField('reason', e.target.value)}
              placeholder="e.g. High fever, hypertension"
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-900 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
              Helps evaluate therapeutic indications and evidence.
            </p>
          </div>

          {/* Known Allergies */}
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Known Drug Allergies
            </label>
            <input
              type="text"
              value={context.allergies ?? ''}
              onChange={(e) => updateField('allergies', e.target.value)}
              placeholder="e.g. Penicillin, Sulfa drugs"
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-900 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
              Crucial for preventing severe allergic reactions.
            </p>
          </div>

          {/* Pregnancy Status */}
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Pregnancy Status
            </label>
            <select
              value={context.pregnancy ?? 'not_applicable'}
              onChange={(e) => updateField('pregnancy', e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-900 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="not_applicable">Not applicable</option>
              <option value="no">Not pregnant</option>
              <option value="yes">Pregnant / Nursing</option>
            </select>
            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
              Flags medicines unsafe during pregnancy or lactation.
            </p>
          </div>

          {/* Kidney / Liver */}
          <div className="sm:col-span-2">
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Kidney or Liver Health
            </label>
            <input
              type="text"
              value={context.kidney_liver ?? ''}
              onChange={(e) => updateField('kidney_liver', e.target.value)}
              placeholder="e.g. Chronic kidney disease stage 2, normal liver"
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-900 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
              Identifies medicines requiring reduced dosage due to impaired organ clearance.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
