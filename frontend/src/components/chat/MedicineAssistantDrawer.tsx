import React, { useState, useRef, useEffect } from 'react';
import {
  Bot,
  X,
  Send,
  Loader2,
  Trash2,
  AlertCircle,
  ExternalLink,
  Sparkles,
  Maximize2,
  Minimize2,
  Languages,
  ShieldCheck,
  RefreshCw,
  ShoppingBag
} from 'lucide-react';
import { sendAssistantChat } from '../../services/api';
import { AssistantMessage, Medicine } from '../../types';
import { PriceComparisonCard } from './PriceComparisonCard';
import { AlternativesCard } from './AlternativesCard';

interface MedicineAssistantDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  activeMedicines?: Medicine[];
}

const QUICK_PROMPTS = [
  { label: 'Dolo 650 kis liye khate hain?', lang: 'Hinglish' },
  { label: 'डोलो 650 किस काम आती है?', lang: 'हिंदी' },
  { label: 'Find cheapest paracetamol 650', lang: 'English' },
  { label: 'Augmentin 625 price & alternatives', lang: 'English' },
  { label: 'Pan 40 sasti kahan milegi?', lang: 'Hinglish' }
];

export const MedicineAssistantDrawer: React.FC<MedicineAssistantDrawerProps> = ({
  isOpen,
  onClose,
  activeMedicines = []
}) => {
  const [messages, setMessages] = useState<AssistantMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Namaste! I am your Multilingual Medicine Information & Pharmacy Price Comparison Assistant.\n\n' +
        'You can ask me questions about any medicine in English, Hindi (हिंदी), or Hinglish:\n' +
        '• "What is Dolo 650 used for?"\n' +
        '• "डोलो 650 किस काम आती है?"\n' +
        '• "Dolo 650 sasti kahan milegi aur alternatives kya hain?"\n' +
        '• "Explain in English" / "Hindi mein samjhao"\n\n' +
        'How can I help you today?',
      timestamp: 'Just now',
      language: 'en'
    }
  ]);

  const [input, setInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [lastUserPrompt, setLastUserPrompt] = useState<string>('');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  }, [isOpen, messages]);

  if (!isOpen) return null;

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || input).trim();
    if (!text || isLoading) return;

    setInput('');
    setError(null);
    setLastUserPrompt(text);

    const userMessage: AssistantMessage = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const historyPayload = newMessages.slice(-10).map((m) => ({
        role: m.role,
        content: m.content
      }));

      const prescriptionPayload = activeMedicines.map((m) => ({
        name_text: m.name_text,
        strength: m.strength || null
      }));

      const res = await sendAssistantChat(text, historyPayload, prescriptionPayload);

      const botMessage: AssistantMessage = {
        id: `b-${Date.now()}`,
        role: 'assistant',
        content: res.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        language: res.language,
        price_comparison: res.price_comparison,
        alternatives: res.alternatives,
        sources: res.sources,
        flags: res.flags
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err: any) {
      setError(err.message || 'Failed to connect with Medicine Assistant. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearHistory = () => {
    setMessages([
      {
        id: 'reset',
        role: 'assistant',
        content:
          'Chat history cleared. How can I help you with medicine information, pharmacy search, or affordable alternatives?',
        timestamp: 'Just now'
      }
    ]);
    setError(null);
  };

  const handleRetry = () => {
    if (lastUserPrompt) {
      handleSendMessage(lastUserPrompt);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Multilingual Medicine Assistant"
      className={`fixed z-50 transition-all duration-300 ease-in-out shadow-2xl flex flex-col bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 ${
        isExpanded
          ? 'inset-3 sm:inset-6 md:inset-10 rounded-2xl'
          : 'bottom-0 right-0 sm:bottom-4 sm:right-4 w-full h-[85vh] sm:h-[650px] sm:max-w-lg sm:rounded-2xl rounded-t-2xl'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-200 bg-gradient-to-r from-teal-600 to-teal-700 px-4 py-3 text-white sm:rounded-t-2xl">
        <div className="flex items-center space-x-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-white/20 backdrop-blur shadow-inner">
            <Bot className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold tracking-tight">Medicine Assistant</h3>
              <span className="inline-flex items-center space-x-1 rounded-full bg-white/20 px-2 py-0.5 text-[10px] font-medium backdrop-blur">
                <Languages className="h-3 w-3" />
                <span>EN • हिंदी • Hinglish</span>
              </span>
            </div>
            <p className="text-[11px] text-teal-100">
              Information, Pharmacy Search & Generic Alternatives
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-1">
          {/* Clear history */}
          <button
            type="button"
            onClick={handleClearHistory}
            title="Clear conversation"
            className="rounded-lg p-1.5 text-teal-100 hover:bg-white/10 hover:text-white transition-colors"
          >
            <Trash2 className="h-4 w-4" />
          </button>

          {/* Expand / Minimize */}
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            title={isExpanded ? 'Minimize drawer' : 'Maximize drawer'}
            className="hidden sm:inline-flex rounded-lg p-1.5 text-teal-100 hover:bg-white/10 hover:text-white transition-colors"
          >
            {isExpanded ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </button>

          {/* Close */}
          <button
            type="button"
            onClick={onClose}
            title="Close Assistant"
            className="rounded-lg p-1.5 text-teal-100 hover:bg-white/10 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Prescription Context Banner (if active prescription medicines exist) */}
      {activeMedicines.length > 0 && (
        <div className="border-b border-teal-100 bg-teal-50/70 px-4 py-2 text-[11px] text-teal-900 dark:border-teal-900/40 dark:bg-teal-950/40 dark:text-teal-200">
          <div className="flex items-center space-x-1.5 mb-1.5 font-semibold">
            <ShoppingBag className="h-3.5 w-3.5 text-teal-600 dark:text-teal-400" />
            <span>Medicines in Current Prescription:</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {activeMedicines.map((m, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSendMessage(`Where can I buy ${m.name_text} and what is the price?`)}
                className="inline-flex items-center space-x-1 rounded-lg border border-teal-200 bg-white px-2 py-0.5 text-[10px] font-medium text-teal-800 hover:bg-teal-100 dark:border-teal-800 dark:bg-slate-800 dark:text-teal-300 dark:hover:bg-slate-700 transition-colors shadow-2xs"
              >
                <span>{m.name_text}</span>
                <span className="text-teal-500 font-bold">Compare</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Safety Notice Strip */}
      <div className="border-b border-slate-200 bg-slate-50 px-4 py-1.5 text-[10px] text-slate-500 dark:border-slate-800 dark:bg-slate-850 dark:text-slate-400 flex items-center justify-between">
        <div className="flex items-center space-x-1.5">
          <ShieldCheck className="h-3.5 w-3.5 text-teal-600 dark:text-teal-400 shrink-0" />
          <span>Educational decision-support only. Always consult a licensed doctor or pharmacist.</span>
        </div>
        <span className="hidden sm:inline-block text-[9px] uppercase tracking-wider text-teal-600 dark:text-teal-400 font-semibold">
          Safety Filter Active
        </span>
      </div>

      {/* Chat Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex items-start space-x-2.5 ${
              m.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {m.role === 'assistant' && (
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-teal-100 text-teal-700 dark:bg-teal-950/70 dark:text-teal-300 mt-0.5">
                <Bot className="h-4 w-4" />
              </div>
            )}

            <div className={`max-w-[88%] sm:max-w-[82%] space-y-2`}>
              <div
                className={`rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-teal-600 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200'
                }`}
              >
                <p className="whitespace-pre-wrap">{m.content}</p>
                <div
                  className={`mt-1.5 text-[9px] text-right ${
                    m.role === 'user' ? 'text-teal-100' : 'text-slate-400 dark:text-slate-500'
                  }`}
                >
                  {m.timestamp}
                </div>
              </div>

              {/* Price Comparison Card (if returned) */}
              {m.price_comparison && <PriceComparisonCard data={m.price_comparison} />}

              {/* Affordable Alternatives Card (if returned) */}
              {m.alternatives && <AlternativesCard data={m.alternatives} />}

              {/* Grounded Web Sources */}
              {m.sources && m.sources.length > 0 && (
                <div className="rounded-xl border border-slate-200/80 bg-white p-2.5 text-[10px] dark:border-slate-800 dark:bg-slate-900 shadow-2xs">
                  <span className="font-semibold text-slate-700 dark:text-slate-300">
                    Medical Reference Sources:
                  </span>
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {m.sources.map((s, idx) => (
                      <a
                        key={idx}
                        href={s.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center space-x-1 rounded-md bg-slate-50 px-2 py-0.5 text-teal-600 hover:text-teal-700 dark:bg-slate-800 dark:text-teal-400"
                      >
                        <span className="truncate max-w-[200px]">{s.title}</span>
                        <ExternalLink className="h-2.5 w-2.5" />
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Safety Gate Warning Flags */}
              {m.flags && m.flags.length > 0 && (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-2 text-[10px] text-amber-800 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-amber-300">
                  <div className="flex items-center space-x-1 font-semibold">
                    <ShieldCheck className="h-3 w-3 text-amber-600" />
                    <span>Safety Gate Notice:</span>
                  </div>
                  <ul className="list-disc pl-4 mt-0.5 space-y-0.5">
                    {m.flags.map((f, i) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex items-center space-x-2 rounded-xl bg-slate-50 p-3 text-xs text-slate-500 dark:bg-slate-800/60 dark:text-slate-400 w-fit">
            <Loader2 className="h-4 w-4 animate-spin text-teal-600 dark:text-teal-400" />
            <span>Assistant is researching medicine information & pharmacy search...</span>
          </div>
        )}

        {/* Error and Retry */}
        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-200 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
            {lastUserPrompt && (
              <button
                type="button"
                onClick={handleRetry}
                className="inline-flex items-center space-x-1 rounded-lg bg-rose-600 px-2.5 py-1 text-[11px] font-semibold text-white shadow-sm hover:bg-rose-500 transition-colors ml-2"
              >
                <RefreshCw className="h-3 w-3" />
                <span>Retry</span>
              </button>
            )}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompts */}
      <div className="border-t border-slate-100 bg-slate-50/70 p-2.5 dark:border-slate-800 dark:bg-slate-850">
        <div className="flex items-center space-x-1 text-[10px] font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">
          <Sparkles className="h-3 w-3 text-teal-500" />
          <span>Quick Suggestions:</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {QUICK_PROMPTS.map((q, idx) => (
            <button
              key={idx}
              type="button"
              disabled={isLoading}
              onClick={() => handleSendMessage(q.label)}
              className="inline-flex items-center space-x-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-700 shadow-2xs hover:border-teal-300 hover:text-teal-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:border-teal-500 transition-colors disabled:opacity-50"
            >
              <span className="text-[9px] rounded px-1 bg-slate-100 dark:bg-slate-700 text-slate-500">
                {q.lang}
              </span>
              <span>{q.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Message Input Box */}
      <div className="border-t border-slate-200 p-3 bg-white dark:border-slate-800 dark:bg-slate-900 sm:rounded-b-2xl">
        <div className="flex items-end space-x-2">
          <textarea
            ref={textareaRef}
            rows={2}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Ask anything in English, हिंदी, or Hinglish (e.g. 'Dolo 650 kis kaam aati hai aur sasti kahan milegi?')..."
            className="flex-1 resize-none rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 focus:border-teal-500 focus:bg-white focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-teal-400"
          />
          <button
            type="button"
            onClick={() => handleSendMessage()}
            disabled={!input.trim() || isLoading}
            className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-white shadow-sm transition-all ${
              input.trim() && !isLoading
                ? 'bg-teal-600 hover:bg-teal-500 shadow-teal-600/30'
                : 'bg-slate-300 dark:bg-slate-800 cursor-not-allowed opacity-60'
            }`}
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </button>
        </div>
        <p className="mt-1 text-[10px] text-slate-400 dark:text-slate-500 text-right">
          Press <strong>Enter</strong> to send • <strong>Shift+Enter</strong> for new line
        </p>
      </div>
    </div>
  );
};
