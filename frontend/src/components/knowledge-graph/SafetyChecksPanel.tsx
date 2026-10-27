import React from 'react';
import {
  SafetyCheckResults,
  InteractionRuleResult,
  DuplicateIngredientResult,
  CoverageResult
} from '../../types';
import {
  AlertTriangle,
  ShieldAlert,
  Copy,
  HelpCircle,
  CheckCircle2,
  Info,
  ExternalLink
} from 'lucide-react';

interface SafetyChecksPanelProps {
  results: SafetyCheckResults;
}

export const SafetyChecksPanel: React.FC<SafetyChecksPanelProps> = ({ results }) => {
  const {
    interactions = [],
    duplicates = [],
    coverage = { total: 0, found_in_list: 0, not_found: [], not_checked: [] },
    notice = 'Only the medicines and rules in our sample list were checked. A missing warning does not mean there is no interaction.'
  } = results;

  const highSeverityCount = interactions.filter((i) => i.severity === 'high').length;
  const moderateSeverityCount = interactions.filter((i) => i.severity === 'moderate').length;

  return (
    <div className="space-y-6">
      {/* Notice Banner */}
      <div className="rounded-2xl border border-amber-200 bg-amber-50/90 p-4 dark:border-amber-900/60 dark:bg-amber-950/40">
        <div className="flex items-start space-x-3">
          <Info className="h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
          <div className="space-y-1">
            <p className="text-xs font-semibold text-amber-900 dark:text-amber-200">
              Sample Data Coverage Notice
            </p>
            <p className="text-xs text-amber-800 dark:text-amber-300">
              {notice}
            </p>
            <p className="text-[11px] text-amber-700/80 dark:text-amber-400/80">
              All rules are sample demo definitions. A licensed pharmacist or doctor must verify all prescriptions.
            </p>
          </div>
        </div>
      </div>

      {/* Coverage Overview Cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Total Medicines</span>
          <p className="text-xl font-bold text-slate-900 dark:text-white mt-0.5">
            {coverage.total}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-[11px] font-medium text-teal-600 dark:text-teal-400">Found in Catalog</span>
          <p className="text-xl font-bold text-teal-700 dark:text-teal-300 mt-0.5">
            {coverage.found_in_list}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-[11px] font-medium text-rose-600 dark:text-rose-400">High Risk Interactions</span>
          <p className="text-xl font-bold text-rose-600 dark:text-rose-400 mt-0.5">
            {highSeverityCount}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-[11px] font-medium text-amber-600 dark:text-amber-400">Duplicate Ingredients</span>
          <p className="text-xl font-bold text-amber-600 dark:text-amber-400 mt-0.5">
            {duplicates.length}
          </p>
        </div>
      </div>

      {/* Configured Interactions Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="h-4 w-4 text-rose-600 dark:text-rose-400" />
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Configured Drug Interactions ({interactions.length})
            </h3>
          </div>
          <span className="text-[11px] text-slate-500 dark:text-slate-400">
            Checked against sample demo rules
          </span>
        </div>

        {interactions.length === 0 ? (
          <div className="rounded-xl border border-slate-200 bg-white p-6 text-center dark:border-slate-800 dark:bg-slate-900">
            <CheckCircle2 className="mx-auto h-7 w-7 text-emerald-500 mb-2" />
            <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
              No interactions found in our sample list
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
              {notice}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {interactions.map((inter, idx) => {
              const isHigh = inter.severity === 'high';
              return (
                <div
                  key={inter.rule_id || idx}
                  className={`rounded-2xl border p-4 shadow-sm transition-all ${
                    isHigh
                      ? 'border-rose-300 bg-rose-50/70 dark:border-rose-900/60 dark:bg-rose-950/40'
                      : 'border-amber-300 bg-amber-50/70 dark:border-amber-900/60 dark:bg-amber-950/40'
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <div className="flex items-center space-x-2">
                      <span
                        className={`inline-flex items-center rounded-lg px-2 py-0.5 text-[11px] font-bold uppercase tracking-wider ${
                          isHigh
                            ? 'bg-rose-600 text-white shadow-sm shadow-rose-600/20'
                            : 'bg-amber-500 text-white shadow-sm shadow-amber-500/20'
                        }`}
                      >
                        {isHigh ? 'High Severity' : 'Moderate Severity'}
                      </span>
                      <span className="text-xs font-semibold text-slate-900 dark:text-white">
                        {inter.medicine_names ? inter.medicine_names.join(' + ') : inter.medicines.join(' + ')}
                      </span>
                    </div>

                    <span className="text-[10px] font-medium text-slate-500 dark:text-slate-400">
                      Rule ID: {inter.rule_id}
                    </span>
                  </div>

                  <p className="text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-medium">
                    {inter.note}
                  </p>

                  <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-slate-200/60 pt-2.5 text-[11px] text-slate-600 dark:border-slate-800/80 dark:text-slate-400">
                    <span className="italic">
                      Source: {inter.source_label}
                    </span>
                    <span className="font-semibold text-rose-700 dark:text-rose-300">
                      Pharmacist verification required
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Duplicate Active Ingredients Section */}
      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <Copy className="h-4 w-4 text-amber-600 dark:text-amber-400" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            Duplicate Active Ingredients ({duplicates.length})
          </h3>
        </div>

        {duplicates.length === 0 ? (
          <div className="rounded-xl border border-slate-200 bg-white p-5 text-center dark:border-slate-800 dark:bg-slate-900">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              No duplicate active ingredients detected among cataloged medicines.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {duplicates.map((dup, idx) => (
              <div
                key={idx}
                className="rounded-2xl border border-amber-300 bg-amber-50/60 p-4 shadow-sm dark:border-amber-900/50 dark:bg-amber-950/30"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold capitalize text-amber-900 dark:text-amber-200">
                    Active Ingredient: {dup.ingredient}
                  </span>
                  <span className="rounded-md bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800 dark:bg-amber-900/60 dark:text-amber-300">
                    Same ingredient found twice
                  </span>
                </div>
                <p className="text-xs text-slate-700 dark:text-slate-300">
                  Detected in:{' '}
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {dup.medicine_names ? dup.medicine_names.join(', ') : dup.medicines.join(', ')}
                  </span>
                </p>
                <p className="mt-2 text-[11px] text-amber-800/90 dark:text-amber-300/90">
                  ⚠️ Taking multiple medicines with the same active ingredient increases the risk of accidental overdose. Discuss dosage with your doctor or pharmacist.
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Unknown Medicines / Coverage Gaps Section */}
      {coverage.not_found && coverage.not_found.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <HelpCircle className="h-4 w-4 text-slate-600 dark:text-slate-400" />
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Not in Sample Demo Catalog ({coverage.not_found.length})
            </h3>
          </div>

          <div className="rounded-2xl border border-slate-300 bg-slate-50/80 p-4 dark:border-slate-700 dark:bg-slate-800/60">
            <p className="text-xs text-slate-700 dark:text-slate-300 font-medium">
              The following medicines were not found in our sample demo catalog:
            </p>
            <ul className="mt-2 space-y-1.5">
              {(coverage.not_checked || coverage.not_found.map((id) => ({ id, name_text: id, status: 'Not in demo catalog' }))).map((item, idx) => (
                <li
                  key={idx}
                  className="flex items-center justify-between rounded-lg bg-white px-3 py-2 text-xs shadow-sm dark:bg-slate-900 border border-slate-200 dark:border-slate-800"
                >
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {item.name_text || item.id}
                  </span>
                  <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-800 dark:bg-slate-800 dark:text-slate-300">
                    Not in demo catalog
                  </span>
                </li>
              ))}
            </ul>
            <div className="mt-3 rounded-xl bg-amber-100/70 p-2.5 text-[11px] text-amber-900 dark:bg-amber-950/60 dark:text-amber-200">
              <p className="font-semibold">Clinical Coverage Note:</p>
              <p>
                Absence from the local demonstration catalog does not mean a medicine is unknown or unsafe. Live medical evidence research (FDA, DailyMed, PubMed) is conducted below. Always verify all prescription medicines with a licensed physician or pharmacist.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
