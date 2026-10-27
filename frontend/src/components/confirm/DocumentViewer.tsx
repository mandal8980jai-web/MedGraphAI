import React from 'react';
import { FileText, ExternalLink } from 'lucide-react';
import { getDocumentFileUrl } from '../../services/api';

interface DocumentViewerProps {
  analysisId: string;
  fileKind: 'image' | 'pdf';
  originalName: string;
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({
  analysisId,
  fileKind,
  originalName,
}) => {
  const fileUrl = getDocumentFileUrl(analysisId);

  return (
    <div className="flex h-full flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-3 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
        <div className="flex items-center space-x-2 truncate">
          <FileText className="h-5 w-5 text-teal-600 dark:text-teal-400 shrink-0" />
          <span className="text-sm font-semibold text-slate-800 dark:text-slate-200 truncate">
            {originalName}
          </span>
        </div>
        <a
          href={fileUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center space-x-1 text-xs font-medium text-teal-600 hover:text-teal-700 dark:text-teal-400 dark:hover:text-teal-300"
        >
          <span>Open raw file</span>
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </div>

      <div className="flex-1 overflow-auto rounded-xl bg-slate-50 dark:bg-slate-950 p-2 min-h-[420px] max-h-[680px] flex items-center justify-center border border-slate-100 dark:border-slate-800/60">
        {fileKind === 'pdf' ? (
          <iframe
            src={`${fileUrl}#toolbar=0&navpanes=0`}
            title="Prescription PDF Preview"
            className="h-full w-full rounded-lg border-0 min-h-[500px]"
          />
        ) : (
          <img
            src={fileUrl}
            alt="Prescription Document"
            className="max-h-full max-w-full rounded-lg object-contain shadow-sm"
          />
        )}
      </div>
      <p className="mt-2 text-center text-xs text-slate-500 dark:text-slate-400">
        Inspect the original handwriting or print to verify medicine names and doses.
      </p>
    </div>
  );
};
