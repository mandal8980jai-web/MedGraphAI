import React, { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { Upload, FileUp, AlertCircle, Loader2, FileText, Image as ImageIcon } from 'lucide-react';
import { uploadDocument } from '../../services/api';
import { AnalysisResponse } from '../../types';

interface UploadZoneProps {
  onUploadSuccess: (analysis: AnalysisResponse) => void;
}

export const UploadZone: React.FC<UploadZoneProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const processFile = async (file: File) => {
    setErrorMessage(null);

    // Frontend validation
    const allowed = ['image/png', 'image/jpeg', 'image/webp', 'application/pdf'];
    const ext = file.name.split('.').pop()?.toLowerCase();
    const validExts = ['png', 'jpg', 'jpeg', 'webp', 'pdf'];

    if (!validExts.includes(ext || '')) {
      setErrorMessage(`Unsupported file format (.${ext}). Please upload a PNG, JPG, WebP, or PDF file.`);
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      setErrorMessage('File size exceeds the 15 MB limit. Please upload a smaller file.');
      return;
    }

    setIsLoading(true);
    try {
      const response = await uploadDocument(file);
      onUploadSuccess(response);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to read document. Please check the file and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  return (
    <div className="mx-auto max-w-3xl">
      {errorMessage && (
        <div className="mb-6 flex items-start space-x-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-200">
          <AlertCircle className="h-5 w-5 shrink-0 text-rose-600 dark:text-rose-400 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Upload Error</p>
            <p className="mt-0.5">{errorMessage}</p>
          </div>
        </div>
      )}

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-12 text-center transition-all ${
          isDragging
            ? 'border-teal-500 bg-teal-50/70 dark:border-teal-400 dark:bg-teal-950/40'
            : 'border-slate-300 bg-white hover:border-teal-400 hover:bg-slate-50/50 dark:border-slate-700 dark:bg-slate-900 dark:hover:border-teal-500/70'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileInput}
          accept=".png,.jpg,.jpeg,.webp,.pdf,image/png,image/jpeg,image/webp,application/pdf"
          className="hidden"
          id="prescription-file-upload"
          disabled={isLoading}
        />

        {isLoading ? (
          <div className="flex flex-col items-center py-6">
            <Loader2 className="h-12 w-12 animate-spin text-teal-600 dark:text-teal-400" />
            <p className="mt-4 text-base font-semibold text-slate-800 dark:text-slate-100">
              Reading your document...
            </p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Extracting digital text, running local OCR, and finding candidate medicines.
            </p>
          </div>
        ) : (
          <>
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-teal-50 text-teal-600 dark:bg-teal-950/60 dark:text-teal-400 mb-4 shadow-sm">
              <FileUp className="h-8 w-8" />
            </div>

            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
              Upload prescription image or PDF
            </h3>
            <p className="mt-1.5 text-sm text-slate-600 dark:text-slate-400 max-w-md">
              Drag and drop your document here, or browse your device to select a prescription.
            </p>

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="mt-6 inline-flex items-center space-x-2 rounded-xl bg-teal-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-teal-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-600 transition-colors"
            >
              <Upload className="h-4 w-4" />
              <span>Choose File</span>
            </button>

            {/* Badges / Hints */}
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3 text-xs text-slate-500 dark:text-slate-400">
              <span className="inline-flex items-center space-x-1 rounded-md bg-slate-100 dark:bg-slate-800 px-2.5 py-1">
                <ImageIcon className="h-3.5 w-3.5 text-slate-400" />
                <span>PNG, JPG, WebP</span>
              </span>
              <span className="inline-flex items-center space-x-1 rounded-md bg-slate-100 dark:bg-slate-800 px-2.5 py-1">
                <FileText className="h-3.5 w-3.5 text-slate-400" />
                <span>Digital or Scanned PDF (up to 10 pages)</span>
              </span>
              <span className="rounded-md bg-slate-100 dark:bg-slate-800 px-2.5 py-1">
                Max 15 MB
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
