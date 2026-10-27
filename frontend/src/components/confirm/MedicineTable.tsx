import React from 'react';
import { Medicine } from '../../types';
import { Plus, Trash2, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface MedicineTableProps {
  medicines: Medicine[];
  onChange: (updated: Medicine[]) => void;
}

export const MedicineTable: React.FC<MedicineTableProps> = ({ medicines, onChange }) => {
  const updateRow = (index: number, patch: Partial<Medicine>) => {
    const updated = [...medicines];
    updated[index] = { ...updated[index], ...patch };
    onChange(updated);
  };

  const removeRow = (index: number) => {
    const updated = medicines.filter((_, i) => i !== index);
    onChange(updated);
  };

  const addRow = () => {
    const newId = `m${medicines.length + 1}_manual_${Date.now().toString().slice(-4)}`;
    const newMed: Medicine = {
      id: newId,
      name_text: '',
      strength: '',
      dose: '',
      frequency: '',
      duration: '',
      page: 1,
      read_quality: 'clear',
      match_status: 'not_found',
      candidates: [],
      ingredients: [],
      confirmed: false,
    };
    onChange([...medicines, newMed]);
  };

  const confirmedCount = medicines.filter((m) => m.confirmed).length;
  const allConfirmed = medicines.length > 0 && confirmedCount === medicines.length;

  return (
    <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-4 dark:border-slate-800">
        <div>
          <h2 className="text-base font-semibold text-slate-900 dark:text-white">
            Detected Medicines
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Verify candidate names and dosages against the document before continuing.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <span
            className={`inline-flex items-center space-x-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
              allConfirmed
                ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                : 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300'
            }`}
          >
            {allConfirmed ? (
              <CheckCircle2 className="h-3.5 w-3.5" />
            ) : (
              <AlertTriangle className="h-3.5 w-3.5" />
            )}
            <span>
              {confirmedCount} of {medicines.length} checked
            </span>
          </span>

          <button
            type="button"
            onClick={addRow}
            className="inline-flex items-center space-x-1 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition-colors"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Add Medicine</span>
          </button>
        </div>
      </div>

      {medicines.length === 0 ? (
        <div className="py-12 text-center">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            No medicines found in this document.
          </p>
          <button
            type="button"
            onClick={addRow}
            className="mt-3 inline-flex items-center space-x-1 text-xs font-semibold text-teal-600 hover:text-teal-700 dark:text-teal-400"
          >
            <Plus className="h-4 w-4" />
            <span>Add a medicine manually</span>
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {medicines.map((med, index) => {
            const needsCheck =
              med.read_quality === 'unclear' ||
              med.match_status === 'several_possible' ||
              med.match_status === 'not_found';

            return (
              <div
                key={med.id}
                className={`rounded-xl border p-4 transition-all ${
                  med.confirmed
                    ? 'border-emerald-200/80 bg-emerald-50/20 dark:border-emerald-900/40 dark:bg-emerald-950/10'
                    : needsCheck
                    ? 'border-amber-300 bg-amber-50/30 dark:border-amber-800/60 dark:bg-amber-950/20'
                    : 'border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900/70'
                }`}
              >
                {/* Header row with badges & check state */}
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-slate-400 dark:text-slate-500">
                      #{index + 1}
                    </span>
                    {med.page && (
                      <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                        Page {med.page}
                      </span>
                    )}
                    {needsCheck && (
                      <span className="inline-flex items-center space-x-1 rounded bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800 dark:bg-amber-900/60 dark:text-amber-300">
                        <AlertTriangle className="h-3 w-3" />
                        <span>Please check</span>
                      </span>
                    )}
                    {med.match_status === 'matched' && (
                      <span className="rounded bg-teal-100 px-2 py-0.5 text-xs font-medium text-teal-800 dark:bg-teal-900/60 dark:text-teal-300">
                        Matched catalog
                      </span>
                    )}
                  </div>

                  <div className="flex items-center space-x-3">
                    <label className="flex items-center space-x-1.5 text-xs font-medium text-slate-700 dark:text-slate-300 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={med.confirmed}
                        onChange={(e) => updateRow(index, { confirmed: e.target.checked })}
                        className="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500 dark:border-slate-700 dark:bg-slate-800"
                      />
                      <span className={med.confirmed ? 'font-semibold text-emerald-600 dark:text-emerald-400' : ''}>
                        I checked this row
                      </span>
                    </label>

                    <button
                      type="button"
                      onClick={() => removeRow(index)}
                      className="p-1 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400"
                      title="Remove row"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Candidate picker if several possible */}
                {med.match_status === 'several_possible' && med.candidates && med.candidates.length > 0 && (
                  <div className="mb-3 rounded-lg bg-amber-50 p-2.5 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/50">
                    <p className="text-xs font-medium text-amber-900 dark:text-amber-200 mb-1.5">
                      Did you mean one of these candidates? Click to apply:
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {med.candidates.map((cand) => (
                        <button
                          key={cand}
                          type="button"
                          onClick={() => updateRow(index, { name_text: cand, match_status: 'matched' })}
                          className="rounded-md bg-white px-2 py-1 text-xs font-medium text-amber-800 shadow-sm border border-amber-300 hover:bg-amber-100 dark:bg-slate-900 dark:text-amber-300 dark:border-amber-800"
                        >
                          {cand}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Editable Fields Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-2.5">
                  <div className="md:col-span-2">
                    <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-0.5">
                      Medicine Name *
                    </label>
                    <input
                      type="text"
                      value={med.name_text}
                      onChange={(e) => updateRow(index, { name_text: e.target.value, confirmed: false })}
                      placeholder="e.g. Dolo 650"
                      className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-900 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-0.5">
                      Strength
                    </label>
                    <input
                      type="text"
                      value={med.strength || ''}
                      onChange={(e) => updateRow(index, { strength: e.target.value })}
                      placeholder="e.g. 650 mg"
                      className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-900 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-0.5">
                      Frequency
                    </label>
                    <input
                      type="text"
                      value={med.frequency || ''}
                      onChange={(e) => updateRow(index, { frequency: e.target.value })}
                      placeholder="e.g. Twice daily"
                      className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-900 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-0.5">
                      Duration
                    </label>
                    <input
                      type="text"
                      value={med.duration || ''}
                      onChange={(e) => updateRow(index, { duration: e.target.value })}
                      placeholder="e.g. 5 days"
                      className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-900 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
