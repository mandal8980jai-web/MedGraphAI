import React, { useState } from 'react';
import { AnalysisEvent } from '../../types';
import {
  ShieldCheck,
  Search,
  Sparkles,
  ShieldAlert,
  Sliders,
  CheckCircle2,
  Clock,
  Loader2,
  XCircle,
  ChevronDown,
  ChevronRight
} from 'lucide-react';

interface HelperPanelProps {
  events: AnalysisEvent[];
  isRunning: boolean;
}

interface HelperSpec {
  name: string;
  role: string;
  icon: React.ComponentType<{ className?: string }>;
}

const HELPERS: HelperSpec[] = [
  { name: 'Manager', role: 'Workflow Coordinator', icon: Sliders },
  { name: 'Safety Checker', role: 'Deterministic Rule Engine', icon: ShieldCheck },
  { name: 'Evidence Helper', role: 'Pharmacist Search Research', icon: Search },
  { name: 'Alternatives Helper', role: 'Clinician Options Research', icon: Sparkles },
  { name: 'Safety Reviewer', role: 'Critic & Safety Verifier', icon: ShieldAlert },
];

export const HelperPanel: React.FC<HelperPanelProps> = ({ events, isRunning }) => {
  const [expandedHelper, setExpandedHelper] = useState<string | null>(null);

  // Group latest event per component
  const componentEvents: Record<string, AnalysisEvent> = {};
  for (const ev of events) {
    componentEvents[ev.component] = ev;
  }

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'running':
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-teal-50 px-2.5 py-0.5 text-[11px] font-semibold text-teal-700 dark:bg-teal-950/60 dark:text-teal-300">
            <Loader2 className="h-3 w-3 animate-spin" />
            <span>Working</span>
          </span>
        );
      case 'done':
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
            <CheckCircle2 className="h-3 w-3" />
            <span>Done</span>
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-rose-50 px-2.5 py-0.5 text-[11px] font-semibold text-rose-700 dark:bg-rose-950/60 dark:text-rose-300">
            <XCircle className="h-3 w-3" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-medium text-slate-500 dark:bg-slate-800 dark:text-slate-400">
            <Clock className="h-3 w-3" />
            <span>Waiting</span>
          </span>
        );
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
        <div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            Helper Activity (Live Stream)
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Real-time backend agent events via Server-Sent Events (SSE).
          </p>
        </div>
        {isRunning && (
          <div className="flex items-center space-x-1.5 text-xs font-semibold text-teal-600 dark:text-teal-400">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-teal-400 opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-teal-500"></span>
            </span>
            <span>Live</span>
          </div>
        )}
      </div>

      <div className="space-y-2.5">
        {HELPERS.map((helper) => {
          const ev = componentEvents[helper.name];
          const status = ev ? ev.status : 'waiting';
          const task = ev ? ev.task : 'Waiting to start...';
          const detail = ev ? ev.detail : '';
          const Icon = helper.icon;
          const isExpanded = expandedHelper === helper.name;

          return (
            <div
              key={helper.name}
              className={`rounded-xl border transition-all ${
                status === 'running'
                  ? 'border-teal-300 bg-teal-50/30 dark:border-teal-800 dark:bg-teal-950/20 shadow-sm'
                  : 'border-slate-100 bg-slate-50/50 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-800/40 dark:hover:bg-slate-800/70'
              }`}
            >
              <div
                onClick={() => setExpandedHelper(isExpanded ? null : helper.name)}
                className="flex cursor-pointer items-center justify-between p-3"
              >
                <div className="flex items-center space-x-3 min-w-0">
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                      status === 'done'
                        ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300'
                        : status === 'running'
                        ? 'bg-teal-100 text-teal-700 dark:bg-teal-900/60 dark:text-teal-300'
                        : 'bg-slate-200/80 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-slate-900 dark:text-white">
                        {helper.name}
                      </span>
                      <span className="text-[10px] text-slate-400 dark:text-slate-500">
                        • {helper.role}
                      </span>
                    </div>
                    <p className="truncate text-xs text-slate-600 dark:text-slate-300">
                      {task}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0 ml-3">
                  {getStatusBadge(status)}
                  {detail && (
                    <span className="text-slate-400">
                      {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                    </span>
                  )}
                </div>
              </div>

              {isExpanded && detail && (
                <div className="border-t border-slate-100 px-3 py-2 text-[11px] text-slate-600 dark:border-slate-800 dark:text-slate-400 bg-white/60 dark:bg-slate-900/60 rounded-b-xl">
                  <p className="font-semibold text-slate-700 dark:text-slate-300">Details:</p>
                  <p className="mt-0.5">{detail}</p>
                  {ev?.time && (
                    <p className="mt-1 text-[10px] text-slate-400">
                      Timestamp: {new Date(ev.time).toLocaleTimeString()}
                    </p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
