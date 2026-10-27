import React, { useState } from 'react';
import {
  FileText,
  AlertTriangle,
  AlertCircle,
  ArrowLeft,
  Download,
  ShieldCheck,
  ShieldAlert,
  Search,
  Sparkles,
  MessageSquare,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Info,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Edit3
} from 'lucide-react';
import {
  AnalysisResponse,
  SafetyCheckResults,
  EvidenceItem,
  AlternativesResult,
  InteractionRuleResult,
  DuplicateIngredientResult
} from '../../types';
import { getReportDownloadUrl } from '../../services/api';
import { ChatPanel } from '../chat/ChatPanel';

interface ResultsStepProps {
  analysis: AnalysisResponse;
  onBackToAnalysis: () => void;
  onBackToConfirm: () => void;
  onStartNewAnalysis: () => void;
}

type TabType = 'medicines' | 'interactions' | 'evidence' | 'alternatives' | 'chat';

export const ResultsStep: React.FC<ResultsStepProps> = ({
  analysis,
  onBackToAnalysis,
  onBackToConfirm,
  onStartNewAnalysis,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('interactions');
  const [expandedEvidence, setExpandedEvidence] = useState<Record<string, boolean>>({});

  const results = analysis.results as (SafetyCheckResults & {
    evidence?: EvidenceItem[];
    alternatives?: AlternativesResult;
    review?: { issues?: { where: string; issue: string }[] };
    flags?: string[];
  }) | undefined;

  const interactions: InteractionRuleResult[] = results?.interactions || [];
  const duplicates: DuplicateIngredientResult[] = results?.duplicates || [];
  const coverage = results?.coverage || {
    total: analysis.medicines.length,
    found_in_list: 0,
    not_found: [],
  };
  const evidenceList: EvidenceItem[] = results?.evidence || [];
  const alternatives: AlternativesResult | undefined = results?.alternatives;
  const reviewIssues = results?.review?.issues || [];
  const flags = results?.flags || [];

  // Toggle evidence expansion
  const toggleEvidence = (id: string) => {
    setExpandedEvidence((prev) => ({
      ...prev,
      [id]: prev[id] === undefined ? false : !prev[id],
    }));
  };

  const handleDownloadReport = () => {
    const url = getReportDownloadUrl(analysis.id);
    window.open(url, '_blank');
  };

  const getSeverityBadge = (severity: string) => {
    const s = severity.toLowerCase();
    if (s === 'high') {
      return (
        <span className="inline-flex items-center space-x-1 rounded-md bg-rose-100 px-2.5 py-0.5 text-xs font-bold text-rose-800 dark:bg-rose-950/70 dark:text-rose-300">
          <ShieldAlert className="h-3.5 w-3.5" />
          <span>High Severity</span>
        </span>
      );
    }
    if (s === 'moderate') {
      return (
        <span className="inline-flex items-center space-x-1 rounded-md bg-amber-100 px-2.5 py-0.5 text-xs font-bold text-amber-800 dark:bg-amber-950/70 dark:text-amber-300">
          <AlertTriangle className="h-3.5 w-3.5" />
          <span>Moderate Severity</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 rounded-md bg-teal-100 px-2.5 py-0.5 text-xs font-bold text-teal-800 dark:bg-teal-950/70 dark:text-teal-300">
        <Info className="h-3.5 w-3.5" />
        <span>Low Severity</span>
      </span>
    );
  };

  const getMatchBadge = (status: string) => {
    switch (status) {
      case 'matched':
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
            <CheckCircle2 className="h-3 w-3" />
            <span>Local Catalog Match</span>
          </span>
        );
      case 'several_possible':
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-[11px] font-semibold text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
            <HelpCircle className="h-3 w-3" />
            <span>Several Possible</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            <XCircle className="h-3 w-3" />
            <span>Not In Demo Catalog (Live Research Available)</span>
          </span>
        );
    }
  };

  const getEvidenceTierBadge = (tier?: string, status?: string) => {
    if (tier === 'live_evidence' || (status === 'ok' && tier !== 'local_catalog' && tier !== 'cached_evidence')) {
      return (
        <span className="rounded-md bg-emerald-100 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
          Live Evidence Retrieved
        </span>
      );
    }
    if (tier === 'cached_evidence') {
      return (
        <span className="rounded-md bg-cyan-100 px-2.5 py-0.5 text-[11px] font-semibold text-cyan-800 dark:bg-cyan-950/60 dark:text-cyan-300">
          Cached Evidence
        </span>
      );
    }
    if (tier === 'local_catalog') {
      return (
        <span className="rounded-md bg-teal-100 px-2.5 py-0.5 text-[11px] font-semibold text-teal-800 dark:bg-teal-950/60 dark:text-teal-300">
          Local Catalog Match
        </span>
      );
    }
    if (tier === 'ai_generated') {
      return (
        <span className="rounded-md bg-blue-100 px-2.5 py-0.5 text-[11px] font-semibold text-blue-800 dark:bg-blue-950/60 dark:text-blue-300">
          AI-Generated Explanation
        </span>
      );
    }
    if (tier === 'not_confidently_identified' || status === 'no_results') {
      return (
        <span className="rounded-md bg-amber-100 px-2.5 py-0.5 text-[11px] font-semibold text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
          Medicine Not Confidently Identified
        </span>
      );
    }
    return (
      <span className="rounded-md bg-slate-100 px-2.5 py-0.5 text-[11px] font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-400">
        Research Unavailable
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Actions Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">
              Analysis Results & Findings
            </h2>
            <span className="rounded-md bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
              Completed
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Document: <span className="font-semibold text-slate-700 dark:text-slate-300">{analysis.original_name}</span> • {analysis.medicines.length} medicine(s) evaluated
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={onBackToAnalysis}
            className="inline-flex items-center space-x-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Analysis</span>
          </button>

          <button
            type="button"
            onClick={onBackToConfirm}
            className="inline-flex items-center space-x-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 transition-colors"
          >
            <Edit3 className="h-3.5 w-3.5" />
            <span>Edit Medicines</span>
          </button>

          <button
            type="button"
            onClick={handleDownloadReport}
            className="inline-flex items-center space-x-2 rounded-xl bg-teal-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-teal-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-600 transition-all shadow-teal-600/20"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Download PDF Report</span>
          </button>

          <button
            type="button"
            onClick={onStartNewAnalysis}
            className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 transition-colors"
          >
            New Upload
          </button>
        </div>
      </div>

      {/* Prominent Safety & Coverage Notice */}
      <div className="rounded-2xl border border-amber-200 bg-amber-50/90 p-4 text-xs text-amber-900 shadow-sm dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-200">
        <div className="flex items-start space-x-2.5">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
          <div className="space-y-1">
            <p className="font-bold">Medical Safety & Sample List Notice</p>
            <p className="text-[11px] leading-relaxed">
              Only the medicines and rules in our sample list were checked. A missing warning does not mean there is no interaction.
              MediGraph AI does not provide medical advice. Always consult a qualified physician or pharmacist before starting, stopping, or changing medications.
            </p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
        <button
          type="button"
          onClick={() => setActiveTab('interactions')}
          className={`inline-flex items-center space-x-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
            activeTab === 'interactions'
              ? 'bg-teal-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
          }`}
        >
          <ShieldAlert className="h-4 w-4" />
          <span>Interactions</span>
          {interactions.length > 0 && (
            <span className="rounded-full bg-rose-500 px-1.5 py-0.2 text-[10px] text-white">
              {interactions.length}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('medicines')}
          className={`inline-flex items-center space-x-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
            activeTab === 'medicines'
              ? 'bg-teal-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
          }`}
        >
          <FileText className="h-4 w-4" />
          <span>Medicines ({analysis.medicines.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('evidence')}
          className={`inline-flex items-center space-x-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
            activeTab === 'evidence'
              ? 'bg-teal-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
          }`}
        >
          <Search className="h-4 w-4" />
          <span>Evidence ({evidenceList.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('alternatives')}
          className={`inline-flex items-center space-x-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
            activeTab === 'alternatives'
              ? 'bg-teal-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
          }`}
        >
          <Sparkles className="h-4 w-4" />
          <span>Alternatives</span>
          {alternatives?.status === 'needs_more_info' && (
            <span className="rounded-full bg-amber-500 px-1.5 py-0.2 text-[10px] text-white">
              info needed
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('chat')}
          className={`inline-flex items-center space-x-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
            activeTab === 'chat'
              ? 'bg-teal-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
          }`}
        >
          <MessageSquare className="h-4 w-4" />
          <span>Chat Helper</span>
        </button>
      </div>

      {/* Tab 1: Confirmed Medicines */}
      {activeTab === 'medicines' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Confirmed Prescription Medicines
            </h3>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Verified by user before analysis
            </span>
          </div>

          <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs dark:divide-slate-800">
              <thead className="bg-slate-50 font-semibold text-slate-700 dark:bg-slate-800/60 dark:text-slate-300">
                <tr>
                  <th className="px-4 py-3">Medicine Name</th>
                  <th className="px-3 py-3">Strength</th>
                  <th className="px-3 py-3">Dose</th>
                  <th className="px-3 py-3">Frequency</th>
                  <th className="px-3 py-3">Duration</th>
                  <th className="px-3 py-3">Catalog Status</th>
                  <th className="px-4 py-3">Active Ingredients</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {analysis.medicines.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white">
                      {m.name_text}
                    </td>
                    <td className="px-3 py-3 text-slate-600 dark:text-slate-300">{m.strength || '—'}</td>
                    <td className="px-3 py-3 text-slate-600 dark:text-slate-300">{m.dose || '—'}</td>
                    <td className="px-3 py-3 text-slate-600 dark:text-slate-300">{m.frequency || '—'}</td>
                    <td className="px-3 py-3 text-slate-600 dark:text-slate-300">{m.duration || '—'}</td>
                    <td className="px-3 py-3">{getMatchBadge(m.match_status)}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                      {m.ingredients && m.ingredients.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {m.ingredients.map((ing, i) => (
                            <span
                              key={i}
                              className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                            >
                              {ing}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="italic text-slate-400">Not in sample catalog</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Interactions, Duplicates & Coverage */}
      {activeTab === 'interactions' && (
        <div className="space-y-6">
          {/* Coverage Summary Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center space-x-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-100 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-900 dark:text-white">
                  Sample List Coverage: {coverage.found_in_list} of {coverage.total} Medicines Checked
                </p>
                <p className="text-[11px] text-slate-500 dark:text-slate-400">
                  Medicines found in our verified demonstration rule database were evaluated for interactions.
                </p>
              </div>
            </div>
            <span className="rounded-lg bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
              {Math.round((coverage.found_in_list / (coverage.total || 1)) * 100)}% Catalog Coverage
            </span>
          </div>

          {/* Interaction Findings */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Detected Drug-Drug Interactions ({interactions.length})
              </h3>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                Deterministic clinical rules
              </span>
            </div>

            {interactions.length > 0 ? (
              <div className="grid grid-cols-1 gap-3.5">
                {interactions.map((intItem, idx) => (
                  <div
                    key={idx}
                    className={`rounded-2xl border p-5 shadow-sm transition-all ${
                      intItem.severity === 'high'
                        ? 'border-rose-300 bg-rose-50/40 dark:border-rose-900/60 dark:bg-rose-950/20'
                        : intItem.severity === 'moderate'
                        ? 'border-amber-300 bg-amber-50/40 dark:border-amber-900/60 dark:bg-amber-950/20'
                        : 'border-teal-200 bg-teal-50/40 dark:border-teal-900/60 dark:bg-teal-950/20'
                    }`}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200/60 pb-3 dark:border-slate-800">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-bold text-slate-900 dark:text-white">
                          {(intItem.medicine_names || intItem.medicines).join(' + ')}
                        </span>
                      </div>
                      {getSeverityBadge(intItem.severity)}
                    </div>

                    <div className="mt-3 space-y-2">
                      <p className="text-xs leading-relaxed text-slate-800 dark:text-slate-200">
                        {intItem.note}
                      </p>
                      <div className="flex items-center justify-between pt-1 text-[11px] text-slate-500 dark:text-slate-400">
                        <span>Source: <strong className="font-semibold text-slate-600 dark:text-slate-300">{intItem.source_label}</strong></span>
                        <span className="italic">Verify with pharmacist</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 text-center dark:border-slate-800 dark:bg-slate-900">
                <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-500 mb-2" />
                <p className="text-xs font-semibold text-slate-900 dark:text-white">
                  No known interactions found in our sample list
                </p>
                <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                  A missing warning does not mean there is no interaction. Always check with your pharmacist.
                </p>
              </div>
            )}
          </div>

          {/* Same Active Ingredients Found Twice (Duplicates) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Same Active Ingredient Found Twice (Duplicates)
              </h3>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                Overdose prevention
              </span>
            </div>

            {duplicates.length > 0 ? (
              <div className="grid grid-cols-1 gap-3">
                {duplicates.map((dup, idx) => (
                  <div
                    key={idx}
                    className="rounded-2xl border border-amber-300 bg-amber-50/50 p-4 dark:border-amber-900/60 dark:bg-amber-950/20 shadow-sm"
                  >
                    <div className="flex items-start space-x-3">
                      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
                      <div className="space-y-1">
                        <p className="text-xs font-bold text-amber-900 dark:text-amber-200">
                          Active ingredient &ldquo;{dup.ingredient}&rdquo; appears in multiple medicines:
                        </p>
                        <p className="text-xs text-amber-800 dark:text-amber-300 font-semibold">
                          {(dup.medicine_names || dup.medicines).join(', ')}
                        </p>
                        <p className="text-[11px] text-amber-700 dark:text-amber-400">
                          Taking multiple medicines with the same active ingredient increases the risk of toxicity or accidental overdose.
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
                No duplicate active ingredients detected among the checked medicines.
              </div>
            )}
          </div>

          {/* Medicines Not Checked (Not in sample list) */}
          {coverage.not_found && coverage.not_found.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Medicines Not Checked (Not in Sample List)
              </h3>

              <div className="rounded-2xl border border-rose-200 bg-rose-50/60 p-4.5 dark:border-rose-900/60 dark:bg-rose-950/30">
                <div className="flex items-start space-x-3">
                  <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600 dark:text-rose-400" />
                  <div className="space-y-1">
                    <p className="text-xs font-bold text-rose-900 dark:text-rose-200">
                      The following medicine(s) were not in our demonstration catalog:
                    </p>
                    <ul className="list-disc pl-4 text-xs text-rose-800 dark:text-rose-300 font-semibold">
                      {coverage.not_found.map((id) => {
                        const med = analysis.medicines.find((m) => m.id === id);
                        return <li key={id}>{med ? med.name_text : id}</li>;
                      })}
                    </ul>
                    <p className="text-[11px] text-rose-700 dark:text-rose-400 pt-1">
                      <strong>Critical rule:</strong> These medicines could not be checked against our sample rules and are <u>NEVER assumed to be safe</u>. Please consult a licensed pharmacist.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Evidence & Sources */}
      {activeTab === 'evidence' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Pharmacist Evidence Research & Web Grounding
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Findings grounded using Google Search. If no external sources were found, it is clearly stated.
              </p>
            </div>
          </div>

          {evidenceList.length > 0 ? (
            <div className="grid grid-cols-1 gap-4">
              {evidenceList.map((ev, idx) => {
                const isExpanded = expandedEvidence[ev.medicine_id] !== false; // default open
                return (
                  <div
                    key={idx}
                    className="rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 overflow-hidden"
                  >
                    <div
                      onClick={() => toggleEvidence(ev.medicine_id)}
                      className="flex cursor-pointer items-center justify-between border-b border-slate-100 bg-slate-50/50 p-4 dark:border-slate-800 dark:bg-slate-800/40"
                    >
                      <div className="flex items-center space-x-3">
                        <span className="text-sm font-bold text-slate-900 dark:text-white">
                          {ev.medicine_name || ev.medicine_id}
                        </span>
                        {getEvidenceTierBadge(ev.evidence_tier, ev.status)}
                      </div>
                      <span className="text-slate-400">
                        {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                      </span>
                    </div>

                    {isExpanded && (
                      <div className="p-4 space-y-3">
                        {ev.status === 'unavailable' ? (
                          <p className="text-xs italic text-slate-500 dark:text-slate-400">
                            Evidence research was unavailable for this medicine.
                          </p>
                        ) : (
                          <>
                            <ul className="space-y-2 text-xs text-slate-700 dark:text-slate-300">
                              {ev.findings.map((f, fi) => (
                                <li key={fi} className="flex items-start space-x-2">
                                  <span className="text-teal-500 mt-0.5 font-bold">•</span>
                                  <span>{f}</span>
                                </li>
                              ))}
                            </ul>

                            {ev.sources && ev.sources.length > 0 ? (
                              <div className="border-t border-slate-100 pt-3 dark:border-slate-800">
                                <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                                  Retrieved Evidence Sources:
                                </span>
                                <div className="mt-1.5 flex flex-wrap gap-2">
                                  {ev.sources.map((s, si) => (
                                    <a
                                      key={si}
                                      href={s.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-flex items-center space-x-1.5 rounded-lg bg-teal-50/70 px-2.5 py-1 text-[11px] font-medium text-teal-700 hover:bg-teal-100 hover:text-teal-900 dark:bg-teal-950/40 dark:text-teal-300 dark:hover:bg-teal-950 transition-colors"
                                    >
                                      <span className="truncate max-w-[260px]">{s.title || s.url}</span>
                                      {s.publication_date && (
                                        <span className="rounded bg-teal-100 px-1 py-0.2 text-[9px] text-teal-800 dark:bg-teal-900 dark:text-teal-200">
                                          {s.publication_date}
                                        </span>
                                      )}
                                      <ExternalLink className="h-3 w-3 shrink-0" />
                                    </a>
                                  ))}
                                </div>
                              </div>
                            ) : (
                              <div className="border-t border-slate-100 pt-2 text-[11px] text-amber-700 dark:border-slate-800 dark:text-amber-400">
                                {ev.evidence_tier === 'local_catalog'
                                  ? 'Verified against local demonstration clinical rules and catalog database.'
                                  : ev.evidence_tier === 'not_confidently_identified'
                                  ? 'No verified sources found in authoritative drug databases.'
                                  : 'No external web sources were returned for these findings.'}
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 text-center text-xs text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
              No evidence research available. Run AI Evidence & Research from Step 3 to fetch findings.
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Alternatives */}
      {activeTab === 'alternatives' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Candidate Options for Discussion with a Doctor
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Educational discussion topics for your physician or pharmacist. Never self-switch or stop medications.
              </p>
            </div>
          </div>

          {alternatives?.status === 'needs_more_info' ? (
            <div className="rounded-2xl border border-amber-300 bg-amber-50/90 p-5 dark:border-amber-900/60 dark:bg-amber-950/40 space-y-3">
              <div className="flex items-start space-x-3">
                <AlertCircle className="mt-0.5 h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0" />
                <div className="space-y-1">
                  <h4 className="text-xs font-bold text-amber-900 dark:text-amber-200">
                    Additional Clinical Information Required
                  </h4>
                  <p className="text-xs text-amber-800 dark:text-amber-300 leading-relaxed">
                    Researching therapeutic alternatives requires patient context to ensure safety. Without knowing age, diagnosis reason, allergies, pregnancy, or kidney/liver function, suggesting alternatives is unsafe.
                  </p>
                  <p className="text-[11px] text-amber-700 dark:text-amber-400 font-semibold pt-1">
                    Missing required fields: {alternatives.missing.join(', ')}
                  </p>
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={onBackToConfirm}
                  className="inline-flex items-center space-x-1.5 rounded-xl bg-amber-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-amber-500 transition-colors"
                >
                  <Edit3 className="h-3.5 w-3.5" />
                  <span>Return to Missing Patient Details Form</span>
                </button>
              </div>
            </div>
          ) : alternatives?.items && alternatives.items.length > 0 ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {alternatives.items.map((item, idx) => (
                <div
                  key={idx}
                  className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900 space-y-3"
                >
                  <div className="border-b border-slate-100 pb-2 dark:border-slate-800">
                    <span className="text-xs font-bold text-slate-900 dark:text-white">
                      Options to discuss regarding {item.medicine_name || item.for_medicine_id}
                    </span>
                    <p className="text-[10px] text-slate-400">
                      Candidate alternatives for clinical discussion
                    </p>
                  </div>

                  <ul className="space-y-1.5 text-xs text-slate-700 dark:text-slate-300">
                    {item.options.map((opt, oi) => (
                      <li key={oi} className="flex items-start space-x-2">
                        <span className="text-teal-500 mt-0.5">•</span>
                        <span>{opt}</span>
                      </li>
                    ))}
                  </ul>

                  {item.sources && item.sources.length > 0 && (
                    <div className="border-t border-slate-100 pt-2.5 dark:border-slate-800">
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                        Sources:
                      </span>
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        {item.sources.map((s, si) => (
                          <a
                            key={si}
                            href={s.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center space-x-1 rounded bg-slate-100 px-2 py-0.5 text-[10px] text-teal-700 dark:bg-slate-800 dark:text-teal-400 hover:underline"
                          >
                            <span className="truncate max-w-[160px]">{s.title}</span>
                            <ExternalLink className="h-2.5 w-2.5" />
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 text-center text-xs text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
              Alternative research is unavailable or was not conducted for this run.
            </div>
          )}
        </div>
      )}

      {/* Tab 5: Chat Helper */}
      {activeTab === 'chat' && (
        <div className="space-y-4">
          <ChatPanel analysisId={analysis.id} />
        </div>
      )}

      {/* Reviewer Notes & Safety Flags (if any) */}
      {(reviewIssues.length > 0 || flags.length > 0) && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50/70 p-4 dark:border-rose-900/60 dark:bg-rose-950/30 space-y-2">
          <h4 className="text-xs font-bold text-rose-900 dark:text-rose-200">
            Safety Gate & Reviewer Interventions:
          </h4>
          <ul className="list-disc pl-4 text-xs text-rose-800 dark:text-rose-300 space-y-1">
            {reviewIssues.map((ri, i) => (
              <li key={i}>
                <strong>[{ri.where}]:</strong> {ri.issue}
              </li>
            ))}
            {flags.map((fl, i) => (
              <li key={`flag-${i}`}>{fl}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
