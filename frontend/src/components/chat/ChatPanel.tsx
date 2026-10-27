import React, { useState } from 'react';
import { sendChatMessage } from '../../services/api';
import { ChatMessage } from '../../types';
import {
  Send,
  Loader2,
  Bot,
  User,
  AlertTriangle,
  Sparkles,
  ShieldCheck,
  Info,
  Languages
} from 'lucide-react';

interface ChatPanelProps {
  analysisId: string;
}

const QUICK_QUESTIONS = [
  { text: 'Explain these results simply', label: 'Explain simply' },
  { text: 'Hindi mein samjhao', label: 'हिंदी में समझाओ' },
  { text: 'Iske side effects kya hain?', label: 'Side effects (Hinglish)' },
  { text: 'What cautions should I discuss with my doctor?', label: 'Doctor cautions' },
  { text: 'Are there any duplicate ingredients?', label: 'Duplicates' }
];

export const ChatPanel: React.FC<ChatPanelProps> = ({ analysisId }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        'Hello! I can explain your confirmed medication summary, interaction warnings, and research findings in English, Hindi (हिंदी), or Hinglish.\n\n' +
        'How can I help you understand this report?'
    }
  ]);
  const [input, setInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [recentFlags, setRecentFlags] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [lastPrompt, setLastPrompt] = useState<string>('');

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || input).trim();
    if (!text || isLoading) return;

    setInput('');
    setError(null);
    setRecentFlags([]);
    setLastPrompt(text);

    const newMessages: ChatMessage[] = [
      ...messages,
      { role: 'user', content: text }
    ];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const history = newMessages.slice(-10).map((m) => ({
        role: m.role,
        content: m.content
      }));

      const res = await sendChatMessage(analysisId, text, history);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: res.reply }
      ]);
      if (res.flags && res.flags.length > 0) {
        setRecentFlags(res.flags);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[520px] rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/50 px-4 py-3 dark:border-slate-800 dark:bg-slate-800/40">
        <div className="flex items-center space-x-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-teal-100 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300">
            <Bot className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-xs font-bold text-slate-900 dark:text-white">
                Medication Assistant (Chat Helper)
              </h3>
              <span className="inline-flex items-center space-x-1 rounded bg-teal-50 px-1.5 py-0.5 text-[9px] font-semibold text-teal-700 dark:bg-teal-950/60 dark:text-teal-300">
                <Languages className="h-2.5 w-2.5" />
                <span>Multilingual</span>
              </span>
            </div>
            <p className="text-[10px] text-slate-500 dark:text-slate-400">
              Safe educational explanation in English, हिंदी, or Hinglish.
            </p>
          </div>
        </div>

        <span className="inline-flex items-center space-x-1 rounded-md bg-teal-50 px-2 py-0.5 text-[10px] font-semibold text-teal-700 dark:bg-teal-950/60 dark:text-teal-300">
          <ShieldCheck className="h-3 w-3" />
          <span>Safety Filter Active</span>
        </span>
      </div>

      {/* Safety Notice Banner */}
      <div className="flex items-center space-x-2 border-b border-amber-100 bg-amber-50/60 px-4 py-2 text-[11px] text-amber-800 dark:border-amber-900/40 dark:bg-amber-950/30 dark:text-amber-200">
        <Info className="h-3.5 w-3.5 shrink-0 text-amber-600 dark:text-amber-400" />
        <span>
          Educational only. Never alter medications based on AI chat. Emergency symptoms bypass AI.
        </span>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex items-start space-x-2.5 ${
              m.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {m.role === 'assistant' && (
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-teal-100 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300 mt-0.5">
                <Bot className="h-4 w-4" />
              </div>
            )}

            <div
              className={`rounded-2xl px-4 py-2.5 max-w-[85%] text-xs leading-relaxed ${
                m.role === 'user'
                  ? 'bg-teal-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200'
              }`}
            >
              <p className="whitespace-pre-wrap">{m.content}</p>
            </div>

            {m.role === 'user' && (
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300 mt-0.5">
                <User className="h-4 w-4" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <Loader2 className="h-3.5 w-3.5 animate-spin text-teal-600" />
            <span>Helper is researching...</span>
          </div>
        )}

        {recentFlags.length > 0 && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-[11px] text-rose-800 dark:border-rose-900/40 dark:bg-rose-950/30 dark:text-rose-200">
            <div className="flex items-center space-x-1.5 font-semibold mb-1">
              <AlertTriangle className="h-3.5 w-3.5 text-rose-600 dark:text-rose-400" />
              <span>Safety Gate Notification:</span>
            </div>
            <ul className="list-disc pl-4 space-y-0.5">
              {recentFlags.map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-2.5 text-xs text-rose-800 dark:border-rose-900/40 dark:bg-rose-950/40 dark:text-rose-200 flex items-center justify-between">
            <span>{error}</span>
            {lastPrompt && (
              <button
                type="button"
                onClick={() => handleSend(lastPrompt)}
                className="ml-2 inline-flex items-center space-x-1 rounded-md bg-rose-600 px-2 py-0.5 text-[10px] font-semibold text-white hover:bg-rose-500 transition-colors"
              >
                <span>Retry</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Quick Prompts */}
      <div className="border-t border-slate-100 bg-slate-50/50 p-2.5 dark:border-slate-800 dark:bg-slate-900/50">
        <div className="flex flex-wrap gap-1.5">
          {QUICK_QUESTIONS.map((q, idx) => (
            <button
              key={idx}
              type="button"
              disabled={isLoading}
              onClick={() => handleSend(q.text)}
              className="inline-flex items-center space-x-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-600 shadow-sm hover:border-teal-300 hover:text-teal-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:border-teal-500 transition-colors disabled:opacity-50"
            >
              <Sparkles className="h-3 w-3 text-teal-500" />
              <span>{q.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Input Form */}
      <div className="border-t border-slate-100 p-2.5 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div className="flex items-end space-x-2">
          <textarea
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Ask in English, हिंदी, or Hinglish (Enter to send, Shift+Enter for new line)..."
            className="flex-1 resize-none rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 focus:border-teal-500 focus:bg-white focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-teal-400"
          />
          <button
            type="button"
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className={`inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-xl p-2 text-white shadow-sm transition-all ${
              input.trim() && !isLoading
                ? 'bg-teal-600 hover:bg-teal-500'
                : 'bg-slate-300 dark:bg-slate-800 cursor-not-allowed opacity-60'
            }`}
          >
            {isLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>
    </div>
  );
};
