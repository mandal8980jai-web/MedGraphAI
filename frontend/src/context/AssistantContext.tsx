import React, { createContext, useContext, useState } from 'react';
import { Medicine } from '../types';

interface AssistantContextType {
  isAssistantOpen: boolean;
  openAssistant: (initialQuery?: string) => void;
  closeAssistant: () => void;
  toggleAssistant: () => void;
  activeMedicines: Medicine[];
  setActiveMedicines: (medicines: Medicine[]) => void;
  initialQuery?: string;
}

const AssistantContext = createContext<AssistantContextType | undefined>(undefined);

export const AssistantProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAssistantOpen, setIsAssistantOpen] = useState<boolean>(false);
  const [activeMedicines, setActiveMedicines] = useState<Medicine[]>([]);
  const [initialQuery, setInitialQuery] = useState<string | undefined>(undefined);

  const openAssistant = (query?: string) => {
    if (query) {
      setInitialQuery(query);
    }
    setIsAssistantOpen(true);
  };

  const closeAssistant = () => {
    setIsAssistantOpen(false);
  };

  const toggleAssistant = () => {
    setIsAssistantOpen((prev) => !prev);
  };

  return (
    <AssistantContext.Provider
      value={{
        isAssistantOpen,
        openAssistant,
        closeAssistant,
        toggleAssistant,
        activeMedicines,
        setActiveMedicines,
        initialQuery
      }}
    >
      {children}
    </AssistantContext.Provider>
  );
};

export const useAssistant = (): AssistantContextType => {
  const context = useContext(AssistantContext);
  if (!context) {
    throw new Error('useAssistant must be used within an AssistantProvider');
  }
  return context;
};
