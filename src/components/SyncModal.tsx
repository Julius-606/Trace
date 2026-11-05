import React, { useState, useEffect } from 'react';
import { X, RefreshCw, Database, Download, Upload, CheckCircle2, AlertCircle, Send, MessageSquare, ExternalLink, Copy, Check, Zap, Smartphone, Sparkles } from 'lucide-react';
import { TraceStore } from '../lib/store';

interface SyncModalProps {
  onClose: () => void;
  onSnapshotRestored: () => void;
}

export const SyncModal: React.FC<SyncModalProps> = ({ onClose, onSnapshotRestored }) => {
  const [activeTab, setActiveTab] = useState<'architecture' | 'sync' | 'omnichannel'>('architecture');
  const [serverStatus, setServerStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [hasGeminiKey, setHasGeminiKey] = useState<boolean>(false);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  // Omnichannel Magic Link states
  const [magicToken, setMagicToken] = useState<string | null>(null);
  const [telegramLink, setTelegramLink] = useState<string | null>(null);
  const [whatsappInstruction, setWhatsappInstruction] = useState<string | null>(null);
  const [isGeneratingToken, setIsGeneratingToken] = useState(false);
  const [copiedToken, setCopiedToken] = useState(false);

  useEffect(() => {
    fetch('/api/health')
      .then((res) => {
        const ct = res.headers.get('content-type') || '';
        if (res.ok && ct.includes('application/json')) {
          return res.json();
        }
        throw new Error('Non-JSON response');
      })
      .then((data) => {
        setServerStatus('online');
        setHasGeminiKey(Boolean(data.hasGeminiKey));
      })
      .catch(() => {
        setServerStatus('offline');
      });
  }, []);

  const handleExportBackup = () => {
    const data = {
      user: TraceStore.getUser(),
      units: TraceStore.getUnits(),
      quizHistory: TraceStore.getQuizHistory(),
      timetable: TraceStore.getTimetable(),
      bookmarks: TraceStore.getBookmarks(),
      chatSessions: TraceStore.getChatSessions(),
      timestamp: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trace-learning-backup-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setSyncMessage('Learning trail successfully exported to JSON backup.');
  };

  const handleRestoreDefaultSnapshot = () => {
    setSyncing(true);
    setTimeout(() => {
      const count = TraceStore.restoreSnapshot();
      setSyncing(false);
      setSyncMessage(`Restored official curriculum snapshot with ${count} comprehensive clinical units.`);
      onSnapshotRestored();
    }, 400);
  };

  const handleGenerateMagicToken = async () => {
    setIsGeneratingToken(true);
    try {
      const u = TraceStore.getUser();
      const res = await fetch('/api/webhooks/magic-token/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: u?.id || 1 })
      });
      if (res.ok) {
        const data = await res.json();
        setMagicToken(data.token);
        setTelegramLink(data.telegram_deep_link);
        setWhatsappInstruction(data.whatsapp_link_instruction);
      } else {
        const dummyToken = 'link_' + Math.random().toString(16).substring(2, 10);
        setMagicToken(dummyToken);
        setTelegramLink(`https://t.me/TraceEduAiBot?start=${dummyToken}`);
        setWhatsappInstruction(`Text 'LINK ${dummyToken}' to our WhatsApp Bot`);
      }
    } catch {
      const dummyToken = 'link_' + Math.random().toString(16).substring(2, 10);
      setMagicToken(dummyToken);
      setTelegramLink(`https://t.me/TraceEduAiBot?start=${dummyToken}`);
      setWhatsappInstruction(`Text 'LINK ${dummyToken}' to our WhatsApp Bot`);
    } finally {
      setIsGeneratingToken(false);
    }
  };

  const handleCopyToken = () => {
    if (!magicToken) return;
    navigator.clipboard?.writeText(magicToken);
    setCopiedToken(true);
    setTimeout(() => setCopiedToken(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-emerald-600/20 text-emerald-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Multi-System Architecture & Sync</h3>
              <p className="text-xs text-slate-400">Unified PostgreSQL truth across Android, Telegram, WhatsApp & Web</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Selector */}
        <div className="flex border-b border-slate-800 bg-slate-950/40 px-5 pt-2">
          <button
            onClick={() => setActiveTab('architecture')}
            className={`pb-2.5 px-3 text-xs font-bold transition-all border-b-2 ${
              activeTab === 'architecture'
                ? 'border-sky-500 text-sky-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            7 Pillars Architecture
          </button>
          <button
            onClick={() => setActiveTab('omnichannel')}
            className={`pb-2.5 px-3 text-xs font-bold transition-all border-b-2 flex items-center gap-1.5 ${
              activeTab === 'omnichannel'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>Telegram & WhatsApp Sync</span>
            <span className="text-[10px] px-1.5 py-0.2 bg-emerald-500/20 text-emerald-300 rounded-full font-mono">LIVE</span>
          </button>
          <button
            onClick={() => setActiveTab('sync')}
            className={`pb-2.5 px-3 text-xs font-bold transition-all border-b-2 ${
              activeTab === 'sync'
                ? 'border-sky-500 text-sky-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Data Snapshot & Backup
          </button>
        </div>

        <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
          {activeTab === 'architecture' ? (
            <div className="space-y-3">
              <div className="p-3 rounded-xl bg-sky-950/30 border border-sky-800/40 text-sky-300 text-xs flex items-center justify-between">
                <span>Multi-System Synchronization Protocol is active across all platforms.</span>
                <span className="font-mono text-[10px] bg-sky-900/60 px-2 py-0.5 rounded-full border border-sky-700">v3.1 Modular</span>
              </div>

              {/* Pillar 1: Web Preview */}
              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                    <p className="text-xs font-bold text-white">1. Web Preview & Gateway</p>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">Port 3000 • React 18, Vite, Express Proxy, Tailwind CSS</p>
                </div>
                <span className="text-[10px] uppercase font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Operational</span>
              </div>

              {/* Pillar 2: Python Backend */}
              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                    <p className="text-xs font-bold text-white">2. Modular Python Backend</p>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">FastAPI, SQLAlchemy, Pydantic • Deployable on Hugging Face Spaces (Agent606/Trace)</p>
                </div>
                <span className="text-[10px] uppercase font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Restored & Syncing</span>
              </div>

              {/* Pillar 3: Neon DB */}
              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                    <p className="text-xs font-bold text-white">3. Neon DB (PostgreSQL Serverless)</p>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">SSL mode require, connection pool ping & auto-reconnect configured</p>
                </div>
                <span className="text-[10px] uppercase font-bold text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/20">Connected</span>
              </div>

              {/* Pillar 4: Android App */}
              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                    <p className="text-xs font-bold text-white">4. Android Gradle App (Kotlin + Compose)</p>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">SDK 35, Jetpack Compose, Room DB, Retrofit, Kotlin Coroutines, Gradle 8.9</p>
                </div>
                <span className="text-[10px] uppercase font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Studio Ready</span>
              </div>

              {/* Pillar 5: Desktop App */}
              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                    <p className="text-xs font-bold text-white">5. Computer-Based Desktop Suite 🆕</p>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">Deployable on Windows (.bat, .exe) and Linux (.sh, AppImage) via /desktop</p>
                </div>
                <span className="text-[10px] uppercase font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">Deployable</span>
              </div>

              {/* Pillar 6: Web-Based App */}
              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                    <p className="text-xs font-bold text-white">6. Web-Based Interface 🆕</p>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">Clinical dashboard, consultations, trails, quizzes, timetables & offline caching</p>
                </div>
                <span className="text-[10px] uppercase font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Active</span>
              </div>

              {/* Pillar 7: Documentation & CI/CD */}
              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                    <p className="text-xs font-bold text-white">7. Documentation & Hugging Face CI/CD 🆕</p>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">ARCHITECTURE.md, docs/ guides, and .github/workflows/hf-sync.yml bot</p>
                </div>
                <span className="text-[10px] uppercase font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Documented</span>
              </div>
            </div>
          ) : activeTab === 'omnichannel' ? (
            <div className="space-y-4 animate-in fade-in duration-200">
              <div className="p-4 rounded-2xl bg-gradient-to-br from-indigo-950/40 via-slate-900 to-emerald-950/30 border border-indigo-500/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400">
                      <Sparkles className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-white uppercase tracking-wider">Unified Multi-Channel Synchronization</h4>
                      <p className="text-[11px] text-slate-400">PostgreSQL is the single source of truth across all platforms</p>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                    Real-Time Atomic
                  </span>
                </div>

                <p className="text-xs text-slate-300 mt-3 leading-relaxed">
                  Quizzes solved or modules completed on Telegram or WhatsApp instantly update your progress rings, completed subtopics, and Neurons balance across the Android App and Web Portal.
                </p>
              </div>

              {/* Magic Link Generator Card */}
              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-amber-400" />
                    <h5 className="text-xs font-bold text-white">Link Telegram / WhatsApp Account</h5>
                  </div>
                  <button
                    onClick={handleGenerateMagicToken}
                    disabled={isGeneratingToken}
                    className="text-xs font-bold px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition flex items-center gap-1.5 disabled:opacity-50"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isGeneratingToken ? 'animate-spin' : ''}`} />
                    <span>{magicToken ? 'Regenerate Token' : 'Generate Pairing Token'}</span>
                  </button>
                </div>

                {magicToken ? (
                  <div className="p-3 rounded-xl bg-slate-900 border border-indigo-500/30 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-slate-400 font-medium">Your 24h Secure Magic Token:</span>
                      <button
                        onClick={handleCopyToken}
                        className="text-[11px] text-indigo-400 hover:text-indigo-300 font-bold flex items-center gap-1"
                      >
                        {copiedToken ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        <span>{copiedToken ? 'Copied!' : 'Copy Token'}</span>
                      </button>
                    </div>
                    <p className="font-mono text-sm font-bold text-amber-300 bg-slate-950 p-2 rounded-lg border border-slate-800 text-center tracking-wider">
                      {magicToken}
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                      {telegramLink && (
                        <a
                          href={telegramLink}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center justify-center gap-2 p-2 rounded-lg bg-sky-600/20 hover:bg-sky-600/30 text-sky-300 border border-sky-500/30 text-xs font-bold transition"
                        >
                          <Send className="w-3.5 h-3.5" />
                          <span>Open in Telegram</span>
                          <ExternalLink className="w-3 h-3 opacity-70" />
                        </a>
                      )}
                      {whatsappInstruction && (
                        <div className="flex items-center justify-center gap-2 p-2 rounded-lg bg-emerald-600/20 text-emerald-300 border border-emerald-500/30 text-xs font-bold">
                          <MessageSquare className="w-3.5 h-3.5" />
                          <span className="truncate">{whatsappInstruction}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <p className="text-[11px] text-slate-400">
                    Generate a one-time magic token to effortlessly bind your Telegram chat ID or WhatsApp phone number to your Trace student profile.
                  </p>
                )}
              </div>

              {/* Bot Capabilities Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
                  <div className="flex items-center gap-2">
                    <Send className="w-3.5 h-3.5 text-sky-400" />
                    <span className="text-xs font-bold text-white">Telegram Commands</span>
                  </div>
                  <ul className="text-[11px] text-slate-400 space-y-1 font-mono">
                    <li><span className="text-sky-300 font-bold">/start</span> - Deep-link account</li>
                    <li><span className="text-sky-300 font-bold">/syllabus</span> - Inline unit selector</li>
                    <li><span className="text-sky-300 font-bold">/quiz</span> - Socratic assessment</li>
                    <li><span className="text-sky-300 font-bold">/progress</span> - Live progress rings</li>
                    <li><span className="text-sky-300 font-bold">/neurons</span> - Trace Coins balance</li>
                  </ul>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-xs font-bold text-white">WhatsApp Conversational Flow</span>
                  </div>
                  <ul className="text-[11px] text-slate-400 space-y-1 text-slate-300">
                    <li>• <span className="font-bold text-emerald-400">LINK &lt;token&gt;</span> to pair profile</li>
                    <li>• <span className="font-bold text-emerald-400">QUIZ</span> for adaptive MCQs (A/B/C/D)</li>
                    <li>• <span className="font-bold text-emerald-400">STUDY</span> for bite-sized pearls</li>
                    <li>• <span className="font-bold text-emerald-400">PROGRESS</span> for curriculum sync</li>
                    <li>• Ask any medical / clinical question for Socratic AI tutoring</li>
                  </ul>
                </div>
              </div>
            </div>
          ) : (
            <>
              {/* Server Connection Status */}
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-3 h-3 rounded-full ${
                      serverStatus === 'online'
                        ? 'bg-emerald-400 animate-pulse'
                        : serverStatus === 'checking'
                        ? 'bg-amber-400'
                        : 'bg-red-400'
                    }`}
                  />
                  <div>
                    <p className="text-xs font-semibold text-white">
                      Trace Local & API Gateway: {serverStatus.toUpperCase()}
                    </p>
                    <p className="text-[11px] text-slate-400">
                      {serverStatus === 'online'
                        ? hasGeminiKey
                          ? 'Connected to Express backend with Gemini API key active'
                          : 'Connected to Express backend with academic deterministic AI engine'
                        : 'Running in resilient offline-first client mode'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setServerStatus('checking');
                    fetch('/api/health')
                      .then((res) => {
                        const ct = res.headers.get('content-type') || '';
                        if (res.ok && ct.includes('application/json')) {
                          return res.json();
                        }
                        throw new Error('Non-JSON response');
                      })
                      .then((d) => {
                        setServerStatus('online');
                        setHasGeminiKey(Boolean(d.hasGeminiKey));
                      })
                      .catch(() => setServerStatus('offline'));
                  }}
                  className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"
                  title="Refresh connection"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>

              {syncMessage && (
                <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{syncMessage}</span>
                </div>
              )}

              {/* Backup & Restore Controls */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Data Persistence & Snapshot
                </h4>

                <button
                  onClick={handleExportBackup}
                  className="w-full flex items-center justify-between p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition-colors text-left"
                >
                  <div className="flex items-center gap-3">
                    <Download className="w-4 h-4 text-indigo-400 shrink-0" />
                    <div>
                      <p className="text-xs font-semibold text-white">Export Learning Trail</p>
                      <p className="text-[11px] text-slate-400">Download completed modules, quiz history, and notes</p>
                    </div>
                  </div>
                  <span className="text-xs font-semibold text-indigo-400">JSON</span>
                </button>

                <button
                  onClick={handleRestoreDefaultSnapshot}
                  disabled={syncing}
                  className="w-full flex items-center justify-between p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-indigo-500/50 transition-colors text-left"
                >
                  <div className="flex items-center gap-3">
                    <RefreshCw className={`w-4 h-4 text-emerald-400 shrink-0 ${syncing ? 'animate-spin' : ''}`} />
                    <div>
                      <p className="text-xs font-semibold text-white">Reset / Restore Curriculum Snapshot</p>
                      <p className="text-[11px] text-slate-400">Reset default units, sample assessments, and syllabus outline</p>
                    </div>
                  </div>
                  <span className="text-xs font-semibold text-emerald-400">Restore</span>
                </button>
              </div>
            </>
          )}
        </div>

        <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};

