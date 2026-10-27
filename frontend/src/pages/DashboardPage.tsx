import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Upload,
  CheckCircle2,
  Cpu,
  FileText,
  ArrowLeft,
  ArrowRight,
  RefreshCw,
  Sparkles,
  AlertCircle
} from 'lucide-react';
import { UploadZone } from '../components/upload/UploadZone';
import { ConfirmStep } from '../components/confirm/ConfirmStep';
import { MedicineMap } from '../components/knowledge-graph/MedicineMap';
import { HelperPanel } from '../components/agent-panel/HelperPanel';
import { ResultsStep } from '../components/results/ResultsStep';
import {
  AnalysisResponse,
  SafetyCheckResults,
  AnalysisEvent
} from '../types';
import { fetchAnalysis, runAnalysis, getEventsStreamUrl } from '../services/api';
import { useAssistant } from '../context/AssistantContext';

export const DashboardPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResponse | null>(null);
  const [isLoadingAnalysis, setIsLoadingAnalysis] = useState<boolean>(false);
  const [events, setEvents] = useState<AnalysisEvent[]>([]);
  const [isWorkflowRunning, setIsWorkflowRunning] = useState<boolean>(false);
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const { setActiveMedicines } = useAssistant();

  // Sync confirmed medicines with assistant context whenever analysis changes
  useEffect(() => {
    if (currentAnalysis && currentAnalysis.medicines) {
      setActiveMedicines(currentAnalysis.medicines);
    } else {
      setActiveMedicines([]);
    }
  }, [currentAnalysis, setActiveMedicines]);

  // Load analysis from URL parameter ?id=... (e.g. from History page)
  useEffect(() => {
    const analysisId = searchParams.get('id');
    if (analysisId && (!currentAnalysis || currentAnalysis.id !== analysisId)) {
      setIsLoadingAnalysis(true);
      fetchAnalysis(analysisId)
        .then((res) => {
          setCurrentAnalysis(res);
          if (res.status === 'done') {
            setCurrentStep(4);
          } else if (res.status === 'confirmed' || res.status === 'running') {
            setCurrentStep(3);
          } else {
            setCurrentStep(2);
          }
        })
        .catch((err) => {
          console.error('Failed to load analysis from URL param:', err);
        })
        .finally(() => {
          setIsLoadingAnalysis(false);
        });
    }
  }, [searchParams]);

  // Clean up SSE on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const handleUploadSuccess = (analysis: AnalysisResponse) => {
    setCurrentAnalysis(analysis);
    setCurrentStep(2);
  };

  const handleConfirmSuccess = (updatedAnalysis: AnalysisResponse) => {
    setCurrentAnalysis(updatedAnalysis);
    setCurrentStep(3);
  };

  const handleStartRun = async () => {
    if (!currentAnalysis) return;
    setIsWorkflowRunning(true);
    setWorkflowError(null);
    setEvents([]);

    try {
      await runAnalysis(currentAnalysis.id);

      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      const es = new EventSource(getEventsStreamUrl(currentAnalysis.id));
      eventSourceRef.current = es;

      es.onmessage = (event) => {
        try {
          const ev: AnalysisEvent = JSON.parse(event.data);
          setEvents((prev) => {
            const exists = prev.some((p) => p.id === ev.id);
            return exists ? prev : [...prev, ev];
          });

          if (ev.component === 'Manager' && (ev.status === 'done' || ev.status === 'failed')) {
            setIsWorkflowRunning(false);
            es.close();
            fetchAnalysis(currentAnalysis.id).then((fresh) => {
              setCurrentAnalysis(fresh);
              if (ev.status === 'done') {
                setCurrentStep(4);
              }
            });
          }
        } catch (err) {
          console.error('Error parsing SSE event data:', err);
        }
      };

      es.onerror = () => {
        es.close();
        setIsWorkflowRunning(false);
        fetchAnalysis(currentAnalysis.id).then((fresh) => {
          setCurrentAnalysis(fresh);
        });
      };
    } catch (err: any) {
      setIsWorkflowRunning(false);
      setWorkflowError(err.message || 'Failed to start analysis workflow');
    }
  };

  const steps = [
    { id: 1, name: 'Upload', desc: 'Select image or PDF', icon: Upload },
    { id: 2, name: 'Confirm', desc: 'Verify medicine list', icon: CheckCircle2 },
    { id: 3, name: 'Analysis', desc: 'Helper panel & map', icon: Cpu },
    { id: 4, name: 'Results', desc: 'Findings & PDF report', icon: FileText },
  ];

  const safetyResults = currentAnalysis?.results as SafetyCheckResults | undefined;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Top Page Title */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
            Medication Safety Analysis
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Four-step clinical decision-support pipeline: Upload, Confirm, Analysis, and Results.
          </p>
        </div>

        {currentAnalysis && currentStep > 1 && (
          <div className="flex items-center space-x-2 text-xs text-slate-500 dark:text-slate-400">
            <span className="font-semibold text-slate-700 dark:text-slate-200">
              {currentAnalysis.original_name}
            </span>
            <span>•</span>
            <span className="uppercase">{currentAnalysis.text_source === 'ocr' ? 'OCR' : 'Digital PDF'}</span>
            <span>•</span>
            <span>{currentAnalysis.page_count} page(s)</span>
          </div>
        )}
      </div>

      {/* 4-Step Progress Navigation Bar */}
      <div className="mb-8">
        <nav aria-label="Progress">
          <ol className="grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4">
            {steps.map((step) => {
              const Icon = step.icon;
              const isCurrent = step.id === currentStep;
              const isPassed = step.id < currentStep;
              const canNavigate = isPassed || (step.id === 4 && currentAnalysis?.status === 'done');

              return (
                <li
                  key={step.id}
                  onClick={() => {
                    if (canNavigate) {
                      setCurrentStep(step.id);
                    }
                  }}
                  className={`flex items-center space-x-3 rounded-xl border p-3.5 transition-all ${
                    isCurrent
                      ? 'border-teal-500 bg-teal-50/50 shadow-sm dark:border-teal-400 dark:bg-teal-950/30'
                      : canNavigate
                      ? 'border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 cursor-pointer hover:border-teal-300'
                      : 'border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 opacity-60'
                  }`}
                >
                  <div
                    className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
                      isCurrent
                        ? 'bg-teal-600 text-white dark:bg-teal-500'
                        : isPassed
                        ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300'
                        : 'bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                  <div>
                    <span
                      className={`text-[11px] font-semibold uppercase tracking-wider ${
                        isCurrent
                          ? 'text-teal-600 dark:text-teal-400'
                          : isPassed
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : 'text-slate-400 dark:text-slate-500'
                      }`}
                    >
                      Step {step.id}
                    </span>
                    <p className="text-xs font-semibold text-slate-900 dark:text-white">
                      {step.name}
                    </p>
                  </div>
                </li>
              );
            })}
          </ol>
        </nav>
      </div>

      {isLoadingAnalysis && (
        <div className="flex h-64 flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white p-8 text-center dark:border-slate-800 dark:bg-slate-900">
          <RefreshCw className="h-8 w-8 animate-spin text-teal-600 mb-3" />
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
            Loading analysis records...
          </p>
        </div>
      )}

      {/* Step 1: Upload */}
      {!isLoadingAnalysis && currentStep === 1 && (
        <UploadZone onUploadSuccess={handleUploadSuccess} />
      )}

      {/* Step 2: Confirm */}
      {!isLoadingAnalysis && currentStep === 2 && currentAnalysis && (
        <ConfirmStep
          analysis={currentAnalysis}
          onConfirmSuccess={handleConfirmSuccess}
          onBackToUpload={() => setCurrentStep(1)}
        />
      )}

      {/* Step 3: Analysis (Helper Panel beside Medicine Map) */}
      {!isLoadingAnalysis && currentStep === 3 && currentAnalysis && (
        <div className="space-y-6">
          {workflowError && (
            <div className="flex items-center space-x-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-200">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-600 dark:text-rose-400" />
              <span>{workflowError}</span>
            </div>
          )}

          {/* Action Header Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center space-x-3">
              <button
                type="button"
                onClick={() => setCurrentStep(2)}
                className="inline-flex items-center space-x-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 transition-colors"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                <span>Back to Confirm</span>
              </button>

              <span className="text-xs text-slate-500 dark:text-slate-400">
                {currentAnalysis.medicines.length} medicine(s) confirmed
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={handleStartRun}
                disabled={isWorkflowRunning}
                className={`inline-flex items-center space-x-2 rounded-xl px-4 py-2 text-xs font-semibold text-white shadow-sm transition-all ${
                  isWorkflowRunning
                    ? 'bg-slate-400 cursor-not-allowed opacity-75'
                    : 'bg-teal-600 hover:bg-teal-500 shadow-teal-600/20'
                }`}
              >
                {isWorkflowRunning ? (
                  <>
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    <span>Running Analysis...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>Run AI Evidence & Research</span>
                  </>
                )}
              </button>

              {(currentAnalysis.status === 'done' || safetyResults?.interactions !== undefined) && (
                <button
                  type="button"
                  onClick={() => setCurrentStep(4)}
                  className="inline-flex items-center space-x-1.5 rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100 transition-colors"
                >
                  <span>View Results</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              )}

              <button
                type="button"
                onClick={() => {
                  setCurrentAnalysis(null);
                  setCurrentStep(1);
                }}
                className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 transition-colors"
              >
                New Upload
              </button>
            </div>
          </div>

          {/* Analysis Screen Layout: Helper Panel BESIDE Interactive Medicine Map */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 items-start">
            {/* Left Column (col-span-5): Helper Activity Panel */}
            <div className="lg:col-span-5 space-y-4">
              <HelperPanel events={events} isRunning={isWorkflowRunning} />
            </div>

            {/* Right Column (col-span-7): Interactive Medicine Map */}
            <div className="lg:col-span-7 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                    Interactive Medicine Map
                  </h2>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    Network graph of medicines, active ingredients, and interactions. Drag and zoom enabled.
                  </p>
                </div>
              </div>

              {safetyResults?.graph ? (
                <MedicineMap
                  graphData={safetyResults.graph}
                  notice={safetyResults.notice}
                />
              ) : (
                <div className="flex h-96 flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white p-8 text-center dark:border-slate-800 dark:bg-slate-900">
                  <RefreshCw className="h-8 w-8 animate-spin text-teal-600 mb-3" />
                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                    Loading medicine map...
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Step 4: Results Screen */}
      {!isLoadingAnalysis && currentStep === 4 && currentAnalysis && (
        <ResultsStep
          analysis={currentAnalysis}
          onBackToAnalysis={() => setCurrentStep(3)}
          onBackToConfirm={() => setCurrentStep(2)}
          onStartNewAnalysis={() => {
            setCurrentAnalysis(null);
            setCurrentStep(1);
          }}
        />
      )}
    </div>
  );
};
