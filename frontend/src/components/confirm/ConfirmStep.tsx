import React, { useState } from 'react';
import { AnalysisResponse, Medicine, PatientContext } from '../../types';
import { DocumentViewer } from './DocumentViewer';
import { MedicineTable } from './MedicineTable';
import { PatientContextForm } from './PatientContextForm';
import { saveConfirmedMedicines } from '../../services/api';
import { ArrowLeft, ArrowRight, Loader2, AlertCircle } from 'lucide-react';

interface ConfirmStepProps {
  analysis: AnalysisResponse;
  onConfirmSuccess: (updated: AnalysisResponse) => void;
  onBackToUpload: () => void;
}

export const ConfirmStep: React.FC<ConfirmStepProps> = ({
  analysis,
  onConfirmSuccess,
  onBackToUpload,
}) => {
  const [medicines, setMedicines] = useState<Medicine[]>(analysis.medicines || []);
  const [context, setContext] = useState<PatientContext>(
    analysis.context || {
      age: null,
      reason: '',
      allergies: '',
      pregnancy: 'not_applicable',
      kidney_liver: '',
    }
  );
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const confirmedCount = medicines.filter((m) => m.confirmed).length;
  const canContinue = medicines.length > 0 && confirmedCount === medicines.length;

  const handleContinue = async () => {
    if (!canContinue) return;
    setIsSaving(true);
    setSaveError(null);

    try {
      const updated = await saveConfirmedMedicines(analysis.id, medicines, context);
      onConfirmSuccess(updated);
    } catch (err: any) {
      setSaveError(err.message || 'Failed to save confirmed medicines.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl">
      {saveError && (
        <div className="mb-6 flex items-center space-x-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-200">
          <AlertCircle className="h-5 w-5 shrink-0 text-rose-600 dark:text-rose-400" />
          <p>{saveError}</p>
        </div>
      )}

      {/* Main Grid: Document Viewer on left, Editable Table on right */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 items-start">
        {/* Left Column: Original Document */}
        <div className="lg:col-span-5 sticky top-20">
          <DocumentViewer
            analysisId={analysis.id}
            fileKind={analysis.file_kind}
            originalName={analysis.original_name}
          />
        </div>

        {/* Right Column: Editable Medicine Table & Patient Context */}
        <div className="lg:col-span-7 space-y-6">
          <MedicineTable medicines={medicines} onChange={setMedicines} />
          <PatientContextForm context={context} onChange={setContext} />

          {/* Action Footer */}
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <button
              type="button"
              onClick={onBackToUpload}
              disabled={isSaving}
              className="inline-flex items-center space-x-2 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Upload</span>
            </button>

            <div className="flex items-center space-x-3">
              {!canContinue && (
                <span className="text-xs text-amber-700 dark:text-amber-400">
                  Please check every row to continue ({confirmedCount}/{medicines.length})
                </span>
              )}

              <button
                type="button"
                onClick={handleContinue}
                disabled={!canContinue || isSaving}
                className={`inline-flex items-center space-x-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-all ${
                  canContinue && !isSaving
                    ? 'bg-teal-600 hover:bg-teal-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-600'
                    : 'bg-slate-300 dark:bg-slate-800 cursor-not-allowed opacity-60'
                }`}
              >
                {isSaving ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <span>Continue to Analysis</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
