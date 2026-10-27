import { Medicine, PatientContext, AnalysisResponse, AnalysisSummary } from '../types';

const rawApiUrl = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000';
export const API_BASE_URL: string = rawApiUrl.replace(/\/+$/, '');

export interface HealthResponse {
  status: string;
  llm_key_set: boolean;
  model: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`, {
    headers: {
      Accept: 'application/json',
    },
  });
  if (!res.ok) {
    throw new Error(`Health check failed with status ${res.status}`);
  }
  return res.json();
}

export async function uploadDocument(file: File): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE_URL}/api/documents`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error || errorData.detail?.error || 'Failed to process document');
  }

  return res.json();
}

export async function fetchAnalysis(id: string): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE_URL}/api/analyses/${id}`, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error || 'Failed to fetch analysis');
  }

  return res.json();
}

export async function fetchAnalyses(): Promise<AnalysisSummary[]> {
  const res = await fetch(`${API_BASE_URL}/api/analyses`, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!res.ok) {
    throw new Error('Failed to fetch analyses');
  }

  return res.json();
}

export async function saveConfirmedMedicines(
  id: string,
  medicines: Medicine[],
  context?: PatientContext
): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE_URL}/api/analyses/${id}/medicines`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({ medicines, context }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error || 'Failed to update medicines');
  }

  return res.json();
}

export function getDocumentFileUrl(analysisId: string): string {
  return `${API_BASE_URL}/api/analyses/${analysisId}/file`;
}

export function getReportDownloadUrl(analysisId: string): string {
  return `${API_BASE_URL}/api/analyses/${analysisId}/report`;
}

export async function deleteAnalysis(id: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/analyses/${id}`, {
    method: 'DELETE',
  });

  if (!res.ok) {
    throw new Error('Failed to delete analysis');
  }
}

export async function runAnalysis(id: string): Promise<{ run_id: string }> {
  const res = await fetch(`${API_BASE_URL}/api/analyses/${id}/run`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
    },
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail?.error || errorData.error || 'Failed to start analysis run');
  }

  return res.json();
}

export function getEventsStreamUrl(analysisId: string): string {
  return `${API_BASE_URL}/api/analyses/${analysisId}/events`;
}

export async function sendChatMessage(
  analysisId: string,
  message: string,
  history: { role: string; content: string }[] = []
): Promise<{ reply: string; flags: string[]; language?: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        analysis_id: analysisId,
        message,
        history,
      }),
    });

    if (!res.ok) {
      if (res.status === 503 || res.status === 502 || res.status === 504) {
        throw new Error('Chat service is unavailable. Please check the backend server.');
      }
      const errorData = await res.json().catch(() => ({}));
      const msg = errorData.detail?.error || errorData.error || errorData.detail;
      throw new Error(msg || 'Unable to complete the request. Please try again.');
    }

    return res.json();
  } catch (err: any) {
    if (
      err.name === 'TypeError' ||
      err.message?.includes('fetch') ||
      err.message?.includes('NetworkError') ||
      err.message?.includes('Failed to fetch') ||
      err.message?.includes('network')
    ) {
      throw new Error('Chat service is unavailable. Please check the backend server.');
    }
    throw err;
  }
}

export async function sendAssistantChat(
  message: string,
  history: { role: string; content: string }[] = [],
  prescriptionMedicines?: { name_text: string; strength?: string | null }[],
  language?: string
): Promise<import('../types').AssistantChatResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/assistant/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        message,
        history,
        prescription_medicines: prescriptionMedicines,
        language,
      }),
    });

    if (!res.ok) {
      if (res.status === 503 || res.status === 502 || res.status === 504) {
        throw new Error('Chat service is unavailable. Please check the backend server.');
      }
      const errorData = await res.json().catch(() => ({}));
      const msg = errorData.detail?.error || errorData.error || errorData.detail;
      throw new Error(msg || 'Unable to complete the request. Please try again.');
    }

    return res.json();
  } catch (err: any) {
    if (
      err.name === 'TypeError' ||
      err.message?.includes('fetch') ||
      err.message?.includes('NetworkError') ||
      err.message?.includes('Failed to fetch') ||
      err.message?.includes('network')
    ) {
      throw new Error('Chat service is unavailable. Please check the backend server.');
    }
    throw err;
  }
}

export async function compareMedicinePrices(
  query: string,
  strength?: string,
  dosageForm?: string,
  packSize?: string
): Promise<import('../types').PriceComparisonData> {
  const params = new URLSearchParams({ query });
  if (strength) params.append('strength', strength);
  if (dosageForm) params.append('dosage_form', dosageForm);
  if (packSize) params.append('pack_size', packSize);

  const res = await fetch(`${API_BASE_URL}/api/medicines/compare-prices?${params.toString()}`, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!res.ok) {
    throw new Error('Failed to retrieve price comparison');
  }

  return res.json();
}

export async function fetchMedicineAlternatives(
  query: string
): Promise<import('../types').AlternativesData> {
  const params = new URLSearchParams({ query });
  const res = await fetch(`${API_BASE_URL}/api/medicines/alternatives?${params.toString()}`, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!res.ok) {
    throw new Error('Failed to retrieve alternatives');
  }

  return res.json();
}

