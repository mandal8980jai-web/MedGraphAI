import React, { useEffect, useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Header } from './components/Header';
import { MissingKeyBanner } from './components/MissingKeyBanner';
import { SafetyNotice } from './components/SafetyNotice';
import { DashboardPage } from './pages/DashboardPage';
import { HistoryPage } from './pages/HistoryPage';
import { fetchHealth, HealthResponse } from './services/api';
import { AssistantProvider, useAssistant } from './context/AssistantContext';
import { MedicineAssistantDrawer } from './components/chat/MedicineAssistantDrawer';

const AppContent: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(true);
  const [healthError, setHealthError] = useState<boolean>(false);

  const { isAssistantOpen, toggleAssistant, closeAssistant, activeMedicines } = useAssistant();

  const checkHealth = async () => {
    try {
      const data = await fetchHealth();
      setHealth(data);
      setHealthError(false);
    } catch (err) {
      setHealthError(true);
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    // Poll health status periodically
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  const isKeyMissing = !healthLoading && (!health || !health.llm_key_set);

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 transition-colors">
      <Header
        health={health}
        healthLoading={healthLoading}
        healthError={healthError}
        onOpenAssistant={toggleAssistant}
        isAssistantOpen={isAssistantOpen}
      />
      <MissingKeyBanner show={isKeyMissing} />

      <main className="flex-1">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </main>

      <SafetyNotice />

      {/* Global Top-Right / Responsive Medicine Assistant Drawer */}
      <MedicineAssistantDrawer
        isOpen={isAssistantOpen}
        onClose={closeAssistant}
        activeMedicines={activeMedicines}
      />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AssistantProvider>
      <AppContent />
    </AssistantProvider>
  );
};

export default App;
