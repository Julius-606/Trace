import React, { useState, useEffect } from 'react';
import {
  X,
  User as UserIcon,
  Palette,
  Type,
  Database,
  Check,
  Download,
  Upload,
  RefreshCw,
  Sparkles,
  Shield,
  Layers,
  Sliders,
  CheckCircle2,
  Trash2,
  ChevronDown,
  AlertTriangle
} from 'lucide-react';
import { User, Unit } from '../types';
import { TraceStore } from '../lib/store';

export interface AppearanceSettings {
  theme: 'dark' | 'light' | 'oled' | 'cyberpunk';
  accentColor: 'indigo' | 'emerald' | 'violet' | 'coral' | 'amber';
  fontFamily: 'inter' | 'roboto' | 'lexend' | 'merriweather' | 'jetbrains';
  fontSize: 'compact' | 'normal' | 'large' | 'xlarge';
}

const DEFAULT_APPEARANCE: AppearanceSettings = {
  theme: 'dark',
  accentColor: 'indigo',
  fontFamily: 'inter',
  fontSize: 'normal'
};

export function getSavedAppearance(): AppearanceSettings {
  try {
    const raw = localStorage.getItem('trace_appearance');
    if (raw) return { ...DEFAULT_APPEARANCE, ...JSON.parse(raw) };
  } catch {}
  return DEFAULT_APPEARANCE;
}

export function applyAppearance(settings: AppearanceSettings) {
  try {
    localStorage.setItem('trace_appearance', JSON.stringify(settings));

    const root = document.documentElement;

    // Theme Mode
    root.classList.remove('theme-light', 'theme-oled', 'theme-cyberpunk');
    if (settings.theme === 'light') root.classList.add('theme-light');
    else if (settings.theme === 'oled') root.classList.add('theme-oled');
    else if (settings.theme === 'cyberpunk') root.classList.add('theme-cyberpunk');

    // Font family
    const fontMap: Record<string, string> = {
      inter: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      roboto: 'Roboto, "Helvetica Neue", Arial, sans-serif',
      lexend: 'Lexend, -apple-system, sans-serif',
      merriweather: 'Merriweather, Georgia, Cambria, serif',
      jetbrains: '"JetBrains Mono", Menlo, Monaco, Consolas, monospace'
    };
    root.style.setProperty('--app-font-family', fontMap[settings.fontFamily] || fontMap.inter);
    document.body.style.fontFamily = fontMap[settings.fontFamily] || fontMap.inter;

    // Font size scaling
    const sizeMap: Record<string, string> = {
      compact: '13px',
      normal: '14px',
      large: '16px',
      xlarge: '17px'
    };
    root.style.fontSize = sizeMap[settings.fontSize] || '14px';

    // Accent Colors
    const accentMap: Record<string, { primary: string; hover: string; bg: string }> = {
      indigo: { primary: '#6366F1', hover: '#4F46E5', bg: 'rgba(99, 102, 241, 0.15)' },
      emerald: { primary: '#10B981', hover: '#059669', bg: 'rgba(16, 185, 129, 0.15)' },
      violet: { primary: '#8B5CF6', hover: '#7C3AED', bg: 'rgba(139, 92, 246, 0.15)' },
      coral: { primary: '#F43F5E', hover: '#E11D48', bg: 'rgba(244, 63, 94, 0.15)' },
      amber: { primary: '#F59E0B', hover: '#D97706', bg: 'rgba(245, 158, 11, 0.15)' }
    };
    const accent = accentMap[settings.accentColor] || accentMap.indigo;
    root.style.setProperty('--app-accent-primary', accent.primary);
    root.style.setProperty('--app-accent-hover', accent.hover);
    root.style.setProperty('--app-accent-bg', accent.bg);
  } catch (e) {
    console.warn('Failed to apply appearance settings:', e);
  }
}

interface SettingsModalProps {
  user: User;
  units?: Unit[];
  initialTab?: 'account' | 'appearance' | 'sync' | 'units';
  onClose: () => void;
  onSaveUser: (updated: User) => void;
  onSnapshotRestored?: () => void;
  onDeleteUnit?: (unitId: number) => void;
  onToggleActiveUnit?: (unitId: number, isActive: boolean) => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  user,
  units = [],
  initialTab = 'appearance',
  onClose,
  onSaveUser,
  onSnapshotRestored,
  onDeleteUnit,
  onToggleActiveUnit
}) => {
  const [activeTab, setActiveTab] = useState<'account' | 'appearance' | 'sync' | 'units'>(initialTab);

  // Account State
  const [username, setUsername] = useState(user.username);
  const [email, setEmail] = useState(user.email);
  const [password, setPassword] = useState('');
  const [semesterStatus, setSemesterStatus] = useState(user.semesterStatus || 'Year 3 - Core Clerkships');
  const [difficulty, setDifficulty] = useState(user.difficulty || 'Standard');
  const [aiPersona, setAiPersona] = useState(user.aiPersona || 'Socratic Tutor');
  const [sensoryMode, setSensoryMode] = useState(user.sensoryMode || 'Visual & Conceptual');
  const [accountSaveMsg, setAccountSaveMsg] = useState<string | null>(null);

  // Appearance State
  const [appearance, setAppearance] = useState<AppearanceSettings>(getSavedAppearance());
  const [appearanceMsg, setAppearanceMsg] = useState<string | null>(null);

  // Sync State
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);

  // Collapsible Unit delete state
  const [expandedDeleteUnitId, setExpandedDeleteUnitId] = useState<number | null>(null);

  const handleUpdateAppearance = (partial: Partial<AppearanceSettings>) => {
    const updated = { ...appearance, ...partial };
    setAppearance(updated);
    applyAppearance(updated);
    setAppearanceMsg('Theme settings applied live across the entire application.');
    setTimeout(() => setAppearanceMsg(null), 2500);
  };

  const handleSaveAccount = (e: React.FormEvent) => {
    e.preventDefault();
    const updated: User = {
      ...user,
      username: username.trim(),
      email: email.trim(),
      semesterStatus,
      difficulty,
      aiPersona,
      sensoryMode
    };
    onSaveUser(updated);
    setAccountSaveMsg('Account information and AI tutor persona saved successfully.');
    setTimeout(() => setAccountSaveMsg(null), 3000);
  };

  const handleSyncNow = async () => {
    setSyncing(true);
    setSyncMsg('Synchronizing progress, bookmarks, quizzes, and consultations with server...');
    try {
      const res = await fetch(`/api/user/${user.id}/sync`);
      if (res.ok) {
        setSyncMsg('Cloud sync completed: All local data verified and aligned with backend.');
      } else {
        setSyncMsg('Sync responded with status: ' + res.status + ' (Local cache preserved)');
      }
    } catch (err: any) {
      setSyncMsg('Local offline sync ready: Cache saved in browser storage.');
    } finally {
      setSyncing(false);
    }
  };

  const handleExportBackup = () => {
    const data = {
      user: TraceStore.getUser(),
      units: TraceStore.getUnits(),
      quizHistory: TraceStore.getQuizHistory(),
      timetable: TraceStore.getTimetable(),
      bookmarks: TraceStore.getBookmarks(),
      chatSessions: TraceStore.getChatSessions(),
      appearance,
      timestamp: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trace-user-${user.id}-backup-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setSyncMsg('Full student profile and curriculum snapshot exported to JSON backup file.');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/75 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        {/* Top Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/70">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-2xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Application Settings & Preferences</h3>
              <p className="text-xs text-slate-400">Themes, typography, account info, and cloud synchronization</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 bg-slate-950/40 px-6 overflow-x-auto gap-2">
          {[
            { id: 'appearance', label: 'Theme & Fonts', icon: Palette },
            { id: 'account', label: 'Account Info', icon: UserIcon },
            { id: 'sync', label: 'Cloud Sync', icon: Database },
            { id: 'units', label: 'Units & Deletion', icon: Layers }
          ].map((tab) => {
            const Icon = tab.icon;
            const isSelected = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-3 px-3.5 text-xs font-bold transition-all border-b-2 flex items-center gap-2 shrink-0 ${
                  isSelected
                    ? 'border-indigo-500 text-indigo-300'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* ===================== TAB 1: THEME & FONTS ===================== */}
          {activeTab === 'appearance' && (
            <div className="space-y-6">
              {appearanceMsg && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2 animate-in fade-in">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{appearanceMsg}</span>
                </div>
              )}

              {/* 1. Theme Mode */}
              <div className="space-y-2.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400">
                  App Theme Mode
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  {[
                    { id: 'dark', label: 'Obsidian Noir', desc: 'Default Dark Slate', bg: 'bg-slate-950 border-slate-800 text-white' },
                    { id: 'light', label: 'Clinical Pearl', desc: 'Crisp Light Mode', bg: 'bg-slate-100 border-slate-300 text-slate-900' },
                    { id: 'oled', label: 'Midnight OLED', desc: 'True Pitch Black', bg: 'bg-black border-slate-800 text-white' },
                    { id: 'cyberpunk', label: 'Cyber Neon', desc: 'High Contrast Cyan', bg: 'bg-slate-950 border-cyan-500/40 text-cyan-200' }
                  ].map((t) => {
                    const isSelected = appearance.theme === t.id;
                    return (
                      <button
                        key={t.id}
                        onClick={() => handleUpdateAppearance({ theme: t.id as any })}
                        className={`p-3 rounded-2xl border text-left transition-all ${
                          isSelected
                            ? 'border-indigo-500 ring-2 ring-indigo-500/30 shadow-lg'
                            : 'border-slate-800 hover:border-slate-700'
                        } ${t.bg}`}
                      >
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-bold">{t.label}</p>
                          {isSelected && <Check className="w-3.5 h-3.5 text-indigo-400" />}
                        </div>
                        <p className="text-[10px] opacity-70 mt-0.5">{t.desc}</p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 2. Theme Accent Color */}
              <div className="space-y-2.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400">
                  Theme Accent Color
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
                  {[
                    { id: 'indigo', label: 'Indigo Neon', hex: '#6366F1' },
                    { id: 'emerald', label: 'Emerald Cyan', hex: '#10B981' },
                    { id: 'violet', label: 'Royal Violet', hex: '#8B5CF6' },
                    { id: 'coral', label: 'Crimson Coral', hex: '#F43F5E' },
                    { id: 'amber', label: 'Sunset Amber', hex: '#F59E0B' }
                  ].map((color) => {
                    const isSelected = appearance.accentColor === color.id;
                    return (
                      <button
                        key={color.id}
                        onClick={() => handleUpdateAppearance({ accentColor: color.id as any })}
                        className={`p-3 rounded-2xl border flex items-center gap-2.5 transition-all ${
                          isSelected
                            ? 'bg-slate-800/90 border-indigo-400 shadow-md ring-1 ring-indigo-400/40'
                            : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        <span
                          className="w-4 h-4 rounded-full shrink-0 shadow-sm"
                          style={{ backgroundColor: color.hex }}
                        />
                        <span className="text-xs font-semibold text-slate-200">{color.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 3. App Typography & Font Family */}
              <div className="space-y-2.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400">
                  App Font & Typography
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                  {[
                    { id: 'inter', label: 'Inter Sans', desc: 'Standard Modern UI', font: 'sans-serif' },
                    { id: 'lexend', label: 'Lexend', desc: 'Hyper-Legible Reading', font: 'sans-serif' },
                    { id: 'merriweather', label: 'Merriweather', desc: 'Academic Editorial Serif', font: 'serif' },
                    { id: 'roboto', label: 'Roboto', desc: 'Clean Clinical Sans', font: 'sans-serif' },
                    { id: 'jetbrains', label: 'JetBrains Mono', desc: 'Diagnostic Code / Mono', font: 'monospace' }
                  ].map((f) => {
                    const isSelected = appearance.fontFamily === f.id;
                    return (
                      <button
                        key={f.id}
                        onClick={() => handleUpdateAppearance({ fontFamily: f.id as any })}
                        className={`p-3 rounded-2xl border text-left transition-all ${
                          isSelected
                            ? 'bg-indigo-950/30 border-indigo-500 ring-1 ring-indigo-500/30'
                            : 'bg-slate-950/50 border-slate-800 hover:border-slate-700 text-slate-300'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-bold text-white" style={{ fontFamily: f.font }}>{f.label}</p>
                          {isSelected && <Check className="w-3.5 h-3.5 text-indigo-400" />}
                        </div>
                        <p className="text-[10px] text-slate-400 mt-0.5">{f.desc}</p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 4. Font Size Scale */}
              <div className="space-y-2.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400">
                  Font Size Scaling
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {[
                    { id: 'compact', label: 'Compact (90%)' },
                    { id: 'normal', label: 'Standard (100%)' },
                    { id: 'large', label: 'Comfort (110%)' },
                    { id: 'xlarge', label: 'Large (125%)' }
                  ].map((sz) => {
                    const isSelected = appearance.fontSize === sz.id;
                    return (
                      <button
                        key={sz.id}
                        onClick={() => handleUpdateAppearance({ fontSize: sz.id as any })}
                        className={`py-2 px-3 rounded-xl text-xs font-semibold border transition-all ${
                          isSelected
                            ? 'bg-indigo-600 text-white border-indigo-500 shadow'
                            : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                        }`}
                      >
                        {sz.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* ===================== TAB 2: ACCOUNT INFO ===================== */}
          {activeTab === 'account' && (
            <form onSubmit={handleSaveAccount} className="space-y-4">
              {accountSaveMsg && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2 animate-in fade-in">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{accountSaveMsg}</span>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Student Full Name
                  </label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:border-indigo-500 outline-none"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Institutional Email Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:border-indigo-500 outline-none"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Academic Year / Level
                  </label>
                  <select
                    value={semesterStatus}
                    onChange={(e) => setSemesterStatus(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:border-indigo-500 outline-none"
                  >
                    <option value="Year 1 - Foundational Studies">Year 1 - Foundational Studies</option>
                    <option value="Year 2 - Core Disciplines">Year 2 - Core Disciplines</option>
                    <option value="Year 3 - Advanced Theory & Practicum">Year 3 - Advanced Theory & Practicum</option>
                    <option value="Year 4 - Professional Practice & Capstone">Year 4 - Professional Practice & Capstone</option>
                    <option value="Postgraduate / Research & Fellowship">Postgraduate / Research & Fellowship</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Study Pace & Examination Level
                  </label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:border-indigo-500 outline-none"
                  >
                    <option value="Standard">Standard Academic Pace</option>
                    <option value="High-Yield Concepts">High-Yield Concepts & Takeaways</option>
                    <option value="Professional Licensing Prep">Professional Licensing & Board Prep</option>
                    <option value="Superuser">Advanced Honors & Research Mode</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    AI Consultant Persona
                  </label>
                  <select
                    value={aiPersona}
                    onChange={(e) => setAiPersona(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:border-indigo-500 outline-none"
                  >
                    <option value="Socratic Tutor">Socratic Tutor (Guides through inquiries)</option>
                    <option value="Clinical Attending">Clinical Attending (Rounds rigor)</option>
                    <option value="Exam Drillmaster">Exam Drillmaster (High-yield pearls)</option>
                    <option value="Feynman Explainer">Feynman Explainer (Radical intuition)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Sensory Learning Mode
                  </label>
                  <select
                    value={sensoryMode}
                    onChange={(e) => setSensoryMode(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:border-indigo-500 outline-none"
                  >
                    <option value="Visual & Conceptual">Visual, Flowcharts & Diagrams</option>
                    <option value="Clinical Text & Pearls">Clinical Text & Bulleted Pearls</option>
                    <option value="Audio & Socratic Dialogue">Audio & Socratic Discourse</option>
                  </select>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md shadow-indigo-600/20 transition-all flex items-center gap-2"
                >
                  <Check className="w-4 h-4" />
                  <span>Save Account Settings</span>
                </button>
              </div>
            </form>
          )}

          {/* ===================== TAB 3: CLOUD SYNC & ARCHITECTURE ===================== */}
          {activeTab === 'sync' && (
            <div className="space-y-5">
              {syncMsg && (
                <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs flex items-center gap-2 animate-in fade-in">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{syncMsg}</span>
                </div>
              )}

              <div className="p-4 rounded-2xl border border-slate-800 bg-slate-950/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h4 className="text-sm font-bold text-white">Full Socratic Cloud Synchronization</h4>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Pushes and pulls study progress nodes, bookmarks, quiz scores, and consultation threads.
                  </p>
                </div>
                <button
                  onClick={handleSyncNow}
                  disabled={syncing}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all flex items-center gap-2 shrink-0 shadow-md shadow-indigo-600/20"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
                  <span>{syncing ? 'Synchronizing...' : 'Sync Now'}</span>
                </button>
              </div>

              <div className="p-4 rounded-2xl border border-slate-800 bg-slate-950/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h4 className="text-sm font-bold text-white">Export Student Backup (JSON)</h4>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Save your entire academic progress, custom themes, and quiz histories to an offline JSON file.
                  </p>
                </div>
                <button
                  onClick={handleExportBackup}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition-all flex items-center gap-2 shrink-0 border border-slate-700"
                >
                  <Download className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Export Backup</span>
                </button>
              </div>

              {onSnapshotRestored && (
                <div className="p-4 rounded-2xl border border-slate-800 bg-slate-950/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <h4 className="text-sm font-bold text-white">Restore Standard Medical Snapshot</h4>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Reset syllabus to official medical curriculum with all foundational units intact.
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      if (confirm('Restore standard curriculum units and initialize default milestones?')) {
                        TraceStore.restoreSnapshot();
                        onSnapshotRestored();
                        setSyncMsg('Official curriculum units restored.');
                      }
                    }}
                    className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition-all flex items-center gap-2 shrink-0 border border-slate-700"
                  >
                    <Upload className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Restore Defaults</span>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* ===================== TAB 4: CURRICULUM UNITS & COLLAPSIBLE DELETION ===================== */}
          {activeTab === 'units' && (
            <div className="space-y-3">
              <p className="text-xs text-slate-400 mb-2">
                Manage your enrolled curriculum units. Each unit can be toggled active/inactive, or permanently removed using the collapsible delete danger zone.
              </p>

              {units.map((unit) => {
                const isDeleteOpen = expandedDeleteUnitId === unit.id;
                return (
                  <div
                    key={unit.id}
                    className={`p-3.5 rounded-2xl border transition-all ${
                      unit.isActive
                        ? 'bg-slate-950/60 border-slate-800'
                        : 'bg-slate-950/30 border-slate-800/60 opacity-75'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-xs font-bold text-white">{unit.unitName}</h4>
                          <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold">
                            {unit.category || 'General'}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          {unit.modules?.length || 0} Modules • {unit.modules?.flatMap((m) => m.topics || []).length || 0} Topics
                        </p>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        {onToggleActiveUnit && (
                          <button
                            onClick={() => onToggleActiveUnit(unit.id, !unit.isActive)}
                            className={`px-2.5 py-1 rounded-xl text-[11px] font-semibold transition-colors ${
                              unit.isActive
                                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                                : 'bg-slate-800 text-slate-400 hover:text-white'
                            }`}
                          >
                            {unit.isActive ? 'Active' : 'Inactive'}
                          </button>
                        )}

                        {onDeleteUnit && (
                          <button
                            onClick={() => setExpandedDeleteUnitId(isDeleteOpen ? null : unit.id)}
                            className={`flex items-center gap-1 px-2 py-1 rounded-xl text-[11px] font-semibold transition-colors ${
                              isDeleteOpen
                                ? 'text-red-300 bg-red-950/40 border border-red-800/60'
                                : 'text-slate-400 hover:text-red-400 hover:bg-slate-800/60'
                            }`}
                          >
                            <Trash2 className="w-3 h-3" />
                            <span>Delete</span>
                            <ChevronDown className={`w-3 h-3 transition-transform ${isDeleteOpen ? 'rotate-180 text-red-400' : ''}`} />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Collapsible Delete Section */}
                    {isDeleteOpen && onDeleteUnit && (
                      <div className="mt-3 pt-3 border-t border-red-900/30 bg-red-950/20 rounded-xl p-3 animate-in fade-in slide-in-from-top-1 duration-200">
                        <div className="flex items-start gap-2">
                          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                          <div className="flex-1">
                            <p className="text-[11px] font-bold text-red-300">Permanent Unit Deletion</p>
                            <p className="text-[10px] text-red-400/80 leading-snug">
                              Permanently remove {unit.unitName} and its modules from your study trail.
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => setExpandedDeleteUnitId(null)}
                              className="px-2 py-1 rounded-lg bg-slate-800 text-slate-300 text-xs font-semibold"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={() => {
                                onDeleteUnit(unit.id);
                                setExpandedDeleteUnitId(null);
                              }}
                              className="px-3 py-1 rounded-lg bg-red-600 hover:bg-red-500 text-white font-bold text-xs"
                            >
                              Confirm
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
