import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Clock,
  ArrowLeft,
  Trash2,
  ExternalLink,
  Download,
  AlertTriangle,
  RefreshCw,
  FileText,
  CheckCircle2,
  XCircle,
  HelpCircle,
  FolderOpen
} from 'lucide-react';
import { fetchAnalyses, deleteAnalysis, getReportDownloadUrl } from '../services/api';
import { AnalysisSummary } from '../types';

export const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Deletion state
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [analysisToDelete, setAnalysisToDelete] = useState<AnalysisSummary | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  const loadAnalyses = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchAnalyses();
      // Sort newest first
      data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setAnalyses(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load past analyses');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAnalyses();
  }, []);

  const handleOpenAnalysis = (id: string) => {
    navigate(`/?id=${id}`);
  };

  const handleConfirmDelete = async () => {
    if (!analysisToDelete) return;
    setIsDeleting(true);
    try {
      await deleteAnalysis(analysisToDelete.id);
      setAnalyses((prev) => prev.filter((a) => a.id !== analysisToDelete.id));
      setAnalysisToDelete(null);
    } catch (err: any) {
      alert(err.message || 'Failed to delete analysis');
    } finally {
      setIsDeleting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'done':
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
            <CheckCircle2 className="h-3 w-3" />
            <span>Completed</span>
          </span>
        );
      case 'running':
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-teal-100 px-2.5 py-0.5 text-xs font-semibold text-teal-800 dark:bg-teal-950/60 dark:text-teal-300">
            <RefreshCw className="h-3 w-3 animate-spin" />
            <span>Analyzing</span>
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-rose-100 px-2.5 py-0.5 text-xs font-semibold text-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
            <XCircle className="h-3 w-3" />
            <span>Failed</span>
          </span>
        );
      case 'confirmed':
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-800 dark:bg-blue-950/60 dark:text-blue-300">
            <CheckCircle2 className="h-3 w-3" />
            <span>Confirmed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            <HelpCircle className="h-3 w-3" />
            <span>Uploaded</span>
          </span>
        );
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Top Header */}
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
            Analysis History
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Review past prescription evaluations, reopen results, and download clinical PDF reports.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={loadAnalyses}
            disabled={isLoading}
            className="inline-flex items-center space-x-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition-colors disabled:opacity-50"
            aria-label="Refresh analyses"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            type="button"
            onClick={() => navigate('/')}
            className="inline-flex items-center space-x-1.5 rounded-lg bg-teal-600 px-3.5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-teal-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-600 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>New Analysis</span>
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-200">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4 text-rose-600 dark:text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="flex h-64 flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white p-8 text-center dark:border-slate-800 dark:bg-slate-900">
          <RefreshCw className="h-8 w-8 animate-spin text-teal-600 mb-3" />
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
            Loading past analyses...
          </p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && analyses.length === 0 && (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center dark:border-slate-800 dark:bg-slate-900">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500 mb-4">
            <Clock className="h-7 w-7" />
          </div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-white">
            No analyses found
          </h3>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
            Upload and analyze a prescription in the dashboard to build your verified history.
          </p>
          <div className="mt-6">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="inline-flex items-center rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-teal-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-600 transition-colors"
            >
              Start First Analysis
            </button>
          </div>
        </div>
      )}

      {/* Analyses Table / Card List */}
      {!isLoading && analyses.length > 0 && (
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs dark:divide-slate-800">
              <thead className="bg-slate-50 font-semibold text-slate-700 dark:bg-slate-800/60 dark:text-slate-300">
                <tr>
                  <th className="px-5 py-3.5">Analysis Name / Document</th>
                  <th className="px-4 py-3.5">Date Created</th>
                  <th className="px-4 py-3.5">Status</th>
                  <th className="px-4 py-3.5">File Type & Text Source</th>
                  <th className="px-5 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {analyses.map((item) => {
                  const createdDate = new Date(item.created_at);
                  const formattedDate = createdDate.toLocaleDateString(undefined, {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                  });
                  const formattedTime = createdDate.toLocaleTimeString(undefined, {
                    hour: '2-digit',
                    minute: '2-digit',
                  });

                  return (
                    <tr
                      key={item.id}
                      className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors"
                    >
                      <td className="px-5 py-4 font-semibold text-slate-900 dark:text-white">
                        <div className="flex items-center space-x-2.5">
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300">
                            <FileText className="h-4 w-4" />
                          </div>
                          <div>
                            <span className="block truncate max-w-xs">{item.original_name}</span>
                            <span className="text-[10px] text-slate-400 font-mono">ID: {item.id.slice(0, 8)}...</span>
                          </div>
                        </div>
                      </td>

                      <td className="px-4 py-4 text-slate-600 dark:text-slate-300">
                        <div>{formattedDate}</div>
                        <div className="text-[11px] text-slate-400">{formattedTime}</div>
                      </td>

                      <td className="px-4 py-4">
                        {getStatusBadge(item.status)}
                      </td>

                      <td className="px-4 py-4 text-slate-600 dark:text-slate-300">
                        <div className="flex items-center space-x-1.5 uppercase font-medium">
                          <span>{item.file_kind || 'doc'}</span>
                          <span>•</span>
                          <span>{item.text_source === 'ocr' ? 'OCR' : 'PDF Text'}</span>
                          <span>•</span>
                          <span>{item.page_count || 1}p</span>
                        </div>
                      </td>

                      <td className="px-5 py-4 text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            type="button"
                            onClick={() => handleOpenAnalysis(item.id)}
                            className="inline-flex items-center space-x-1 rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition-colors"
                            aria-label={`Open analysis for ${item.original_name}`}
                          >
                            <FolderOpen className="h-3.5 w-3.5 text-teal-600 dark:text-teal-400" />
                            <span>Open</span>
                          </button>

                          <a
                            href={getReportDownloadUrl(item.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center space-x-1 rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition-colors"
                            aria-label={`Download PDF report for ${item.original_name}`}
                            title="Download PDF Report"
                          >
                            <Download className="h-3.5 w-3.5 text-slate-500 dark:text-slate-400" />
                            <span className="hidden sm:inline">PDF</span>
                          </a>

                          <button
                            type="button"
                            onClick={() => setAnalysisToDelete(item)}
                            className="inline-flex items-center rounded-lg border border-rose-200 bg-white p-1.5 text-rose-600 shadow-sm hover:bg-rose-50 dark:border-rose-900/60 dark:bg-slate-800 dark:text-rose-400 dark:hover:bg-rose-950/40 transition-colors"
                            aria-label={`Delete analysis for ${item.original_name}`}
                            title="Delete Analysis"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {analysisToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-800 dark:bg-slate-900 space-y-4">
            <div className="flex items-center space-x-3 text-rose-600 dark:text-rose-400">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-100 dark:bg-rose-950/60">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Delete Analysis Record?
              </h3>
            </div>

            <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              Are you sure you want to delete the analysis for{' '}
              <strong className="font-semibold text-slate-900 dark:text-white">
                {analysisToDelete.original_name}
              </strong>
              ? This action will permanently remove its database records, uploaded document, and generated PDF report.
            </p>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                type="button"
                onClick={() => setAnalysisToDelete(null)}
                disabled={isDeleting}
                className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 transition-colors"
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={handleConfirmDelete}
                disabled={isDeleting}
                className="inline-flex items-center space-x-1.5 rounded-xl bg-rose-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-rose-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rose-600 transition-colors disabled:opacity-50"
              >
                {isDeleting && <RefreshCw className="h-3.5 w-3.5 animate-spin" />}
                <span>{isDeleting ? 'Deleting...' : 'Delete Permanently'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
