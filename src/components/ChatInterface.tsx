import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Send,
  Clock,
  Plus,
  Trash2,
  Play,
  Pause,
  RotateCcw,
  Bot,
  User as UserIcon,
  MessageSquare,
  ChevronDown,
  PanelLeftClose,
  PanelLeft,
  Maximize2
} from 'lucide-react';
import { ChatSession, ChatMessage, User } from '../types';
import { TraceStore } from '../lib/store';
import { FormattedText } from './FormattedText';

interface ChatInterfaceProps {
  user: User;
  onOpenBrowser: (url?: string) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ user, onOpenBrowser }) => {
  const [sessions, setSessions] = useState<ChatSession[]>(TraceStore.getChatSessions(user.id));
  const [activeSessionId, setActiveSessionId] = useState<string>(sessions[0]?.id || '');
  const [activePersona, setActivePersona] = useState<string>(user.aiPersona || 'Socratic Tutor');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(false);

  // Input & message state
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Focus Study Timer (Pomodoro 25m)
  const [timerSeconds, setTimerSeconds] = useState(25 * 60);
  const [isTimerRunning, setIsTimerRunning] = useState(false);

  useEffect(() => {
    let interval: any = null;
    if (isTimerRunning && timerSeconds > 0) {
      interval = setInterval(() => setTimerSeconds((s) => s - 1), 1000);
    } else if (timerSeconds === 0) {
      setIsTimerRunning(false);
    }
    return () => clearInterval(interval);
  }, [isTimerRunning, timerSeconds]);

  const activeSession = sessions.find((s) => s.id === activeSessionId) || sessions[0];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeSession?.messages, isLoading]);

  const handleCreateNewSession = () => {
    const newSession: ChatSession = {
      id: `session-${Date.now()}`,
      userId: user.id,
      title: 'New Clinical Consultation',
      timestamp: Date.now(),
      messages: [
        {
          id: `msg-${Date.now()}`,
          sender: 'assistant',
          text: `Greetings! I am your **${activePersona}**. How can I support your clinical or scientific inquiry today? You can pose complex case vignettes, explore physiological mechanisms, or practice diagnostic differentials.`,
          timestamp: Date.now()
        }
      ]
    };
    TraceStore.saveChatSession(newSession);
    setSessions(TraceStore.getChatSessions(user.id));
    setActiveSessionId(newSession.id);
  };

  const handleDeleteSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = TraceStore.deleteChatSession(id);
    setSessions(updated);
    if (activeSessionId === id) {
      setActiveSessionId(updated[0]?.id || '');
    }
  };

  const handleSendMessage = async (customPrompt?: string) => {
    const textToSend = customPrompt || inputMessage;
    if (!textToSend.trim() || !activeSession) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: textToSend.trim(),
      timestamp: Date.now()
    };

    const updatedMessages = [...activeSession.messages, userMsg];
    const updatedSession: ChatSession = {
      ...activeSession,
      title: activeSession.messages.length <= 1 ? textToSend.slice(0, 32) + '...' : activeSession.title,
      messages: updatedMessages
    };

    TraceStore.saveChatSession(updatedSession);
    setSessions(TraceStore.getChatSessions(user.id));
    setInputMessage('');
    setIsLoading(true);

    try {
      const mappedHistory = updatedMessages.slice(-6).map((m) => ({
        role: m.sender === 'user' ? 'user' : 'model',
        content: m.text
      }));

      const res = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: textToSend,
          user_id: user.id,
          history: mappedHistory
        })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || `AI request failed (${res.status})`);
      }

      if (!data.response) {
        throw new Error('The AI service returned an empty response');
      }

      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        sender: 'assistant',
        text: data.response || 'I have analyzed your inquiry.',
        timestamp: Date.now()
      };

      const finalSession: ChatSession = {
        ...updatedSession,
        messages: [...updatedMessages, aiMsg]
      };

      TraceStore.saveChatSession(finalSession);
      setSessions(TraceStore.getChatSessions(user.id));
    } catch {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        text: 'Consultation service offline. Please verify network or API configuration.',
        timestamp: Date.now()
      };
      TraceStore.saveChatSession({
        ...updatedSession,
        messages: [...updatedMessages, errorMsg]
      });
      setSessions(TraceStore.getChatSessions(user.id));
    } finally {
      setIsLoading(false);
    }
  };

  const formatTimer = (totalSec: number) => {
    const m = Math.floor(totalSec / 60);
    const s = totalSec % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const samplePrompts = [
    'Explain the physiology of High Anion Gap vs Normal Anion Gap Metabolic Acidosis.',
    'Walk through an acute abdomen differential workup for a 24-year-old with RLQ pain.',
    'Compare the effects of competitive vs uncompetitive inhibitors on Lineweaver-Burk plots.'
  ];

  return (
    <div className="h-[calc(100vh-140px)] flex flex-col sm:flex-row gap-4 pb-4 animate-in fade-in duration-200">
      {/* Sessions & Focus Timer Sidebar */}
      {!isSidebarCollapsed && (
        <div className="w-full sm:w-72 bg-slate-900/80 border border-slate-800 rounded-3xl p-4 flex flex-col justify-between shadow-xl animate-in slide-in-from-left-4 duration-200">
          <div>
            {/* Top New Consultation Button & Collapse */}
            <div className="flex items-center gap-2 mb-4">
              <button
                onClick={handleCreateNewSession}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md shadow-indigo-600/20 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span>New Consultation</span>
              </button>
              <button
                onClick={() => setIsSidebarCollapsed(true)}
                className="p-2.5 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
                title="Collapse sidebar to maximize chat width"
              >
                <PanelLeftClose className="w-4 h-4" />
              </button>
            </div>

            {/* Persona Dropdown */}
            <div className="mb-4">
              <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                Consultant Persona
              </label>
              <select
                value={activePersona}
                onChange={(e) => setActivePersona(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-indigo-300 font-medium outline-none focus:border-indigo-500"
              >
                <option value="Socratic Tutor">Socratic Tutor (Guides through questions)</option>
                <option value="Clinical Attending">Clinical Attending (Rounds rigor)</option>
                <option value="Exam Drillmaster">Exam Drillmaster (High-yield pearls)</option>
                <option value="Feynman Explainer">Feynman Explainer (Radical intuition)</option>
              </select>
            </div>

            {/* Session List */}
            <div className="space-y-1 max-h-[35vh] overflow-y-auto pr-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block px-2 mb-1">
                Recent Consultations
              </span>
              {sessions.map((s) => (
                <div
                  key={s.id}
                  onClick={() => setActiveSessionId(s.id)}
                  className={`p-2.5 rounded-xl text-xs flex items-center justify-between cursor-pointer transition-colors ${
                    activeSessionId === s.id
                      ? 'bg-indigo-600/20 text-indigo-200 border border-indigo-500/30'
                      : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                  }`}
                >
                  <div className="truncate flex-1 pr-2">
                    <p className="font-semibold truncate">{s.title || 'Consultation'}</p>
                    <p className="text-[10px] text-slate-500">
                      {new Date(s.timestamp).toLocaleDateString()}
                    </p>
                  </div>
                  {sessions.length > 1 && (
                    <button
                      onClick={(e) => handleDeleteSession(s.id, e)}
                      className="p-1 text-slate-500 hover:text-red-400 opacity-0 hover:opacity-100 group-hover:opacity-100 transition-opacity"
                      title="Delete session"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Integrated Study Focus Timer (Pomodoro) */}
          <div className="pt-3 border-t border-slate-800/80 bg-slate-950/60 -mx-4 -mb-4 p-4 rounded-b-3xl">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-indigo-400" />
                <span>Focus Timer</span>
              </span>
              <span className="font-mono font-bold text-white text-sm">{formatTimer(timerSeconds)}</span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsTimerRunning(!isTimerRunning)}
                className={`flex-1 py-1.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors ${
                  isTimerRunning
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'bg-indigo-600 hover:bg-indigo-500 text-white'
                }`}
              >
                {isTimerRunning ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                <span>{isTimerRunning ? 'Pause' : 'Start Focus'}</span>
              </button>
              <button
                onClick={() => {
                  setIsTimerRunning(false);
                  setTimerSeconds(25 * 60);
                }}
                className="p-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white"
                title="Reset timer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Conversation Stream - Maximized to full width */}
      <div className="flex-1 w-full bg-slate-900/80 border border-slate-800 rounded-3xl flex flex-col shadow-xl overflow-hidden backdrop-blur-md">
        {/* Active Session Header */}
        <div className="px-5 py-3.5 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {isSidebarCollapsed && (
              <button
                onClick={() => setIsSidebarCollapsed(false)}
                className="p-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-indigo-300 transition-colors mr-1"
                title="Show consultations sidebar"
              >
                <PanelLeft className="w-4 h-4" />
              </button>
            )}
            <div className="w-9 h-9 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">{activeSession?.title || 'Consultation Vault'}</h2>
              <p className="text-[11px] text-indigo-400 font-medium">{activePersona} Active</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
              className="px-2.5 py-1 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition-colors"
              title={isSidebarCollapsed ? "Show side panel" : "Maximize chat width"}
            >
              <Maximize2 className="w-3.5 h-3.5 text-indigo-400" />
              <span className="hidden sm:inline">{isSidebarCollapsed ? "Show Sessions" : "Maximize Width"}</span>
            </button>
            <span className="text-[11px] text-slate-500 hidden md:block">
              Socratic Diagnostic Gateway
            </span>
          </div>
        </div>

        {/* Message Log */}
        <div className="flex-1 w-full overflow-y-auto p-4 sm:p-6 space-y-4">
          {activeSession?.messages.map((m) => {
            const isUser = m.sender === 'user';
            return (
              <div
                key={m.id}
                className={`flex gap-3 w-full ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div className="w-8 h-8 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0 mt-0.5">
                    <Sparkles className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`rounded-2xl text-xs sm:text-sm leading-relaxed ${
                    isUser
                      ? 'max-w-[85%] sm:max-w-[70%] bg-indigo-600 text-white shadow-md shadow-indigo-600/20 p-4'
                      : 'w-full flex-1 text-slate-200 py-1 px-1'
                  }`}
                >
                  {isUser ? (
                    <p className="whitespace-pre-wrap">{m.text}</p>
                  ) : (
                    <div className="w-full max-w-none">
                      <FormattedText text={m.text} onLinkClick={onOpenBrowser} />
                    </div>
                  )}
                  <span className="text-[9px] text-slate-400 block text-right mt-1.5 opacity-70">
                    {new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                {isUser && (
                  <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0 mt-0.5">
                    <UserIcon className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })}

          {isLoading && (
            <div className="flex items-center gap-3 text-xs text-indigo-400 py-1 px-1">
              <Sparkles className="w-4 h-4 animate-spin text-indigo-400" />
              <span>Consultant analyzing clinical pathophysiological matrix...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestion Chips (if few messages) */}
        {activeSession && activeSession.messages.length <= 2 && (
          <div className="px-6 py-2 border-t border-slate-800/60 bg-slate-950/30 flex items-center gap-2 overflow-x-auto text-[11px]">
            <span className="text-slate-500 shrink-0">Prompts:</span>
            {samplePrompts.map((p, i) => (
              <button
                key={i}
                onClick={() => handleSendMessage(p)}
                className="px-3 py-1 rounded-full bg-slate-800/80 hover:bg-indigo-950 hover:text-indigo-300 text-slate-300 border border-slate-700/60 transition-colors whitespace-nowrap"
              >
                {p}
              </button>
            ))}
          </div>
        )}

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/80">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={`Ask your ${activePersona} anything...`}
              className="flex-1 bg-slate-900 border border-slate-800 rounded-2xl px-4 py-3 text-xs text-white placeholder-slate-500 outline-none focus:border-indigo-500 transition-colors"
            />
            <button
              type="submit"
              disabled={isLoading || !inputMessage.trim()}
              className="p-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-40 transition-colors shadow-md shadow-indigo-600/30"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
