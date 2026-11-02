import React, { useState } from 'react';
import { X, Check, Sparkles, User as UserIcon, Coins } from 'lucide-react';
import { User } from '../types';

interface AccountModalProps {
  user: User;
  onClose: () => void;
  onSave: (updated: User) => void;
}

export const AccountModal: React.FC<AccountModalProps> = ({ user, onClose, onSave }) => {
  const [username, setUsername] = useState(user.username);
  const [email, setEmail] = useState(user.email);
  const [semesterStatus, setSemesterStatus] = useState(user.semesterStatus);
  const [difficulty, setDifficulty] = useState(user.difficulty);
  const [aiPersona, setAiPersona] = useState(user.aiPersona);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      ...user,
      username,
      email,
      semesterStatus,
      difficulty,
      aiPersona
    });
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      onClose();
    }, 600);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-600/20 text-indigo-400">
              <UserIcon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Account & Academic Profile</h3>
              <p className="text-xs text-slate-400">Manage learning credentials and AI tutor behavior</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Trace Coin Wallet Display */}
          <div className="p-3.5 rounded-xl bg-gradient-to-r from-amber-500/10 via-amber-600/10 to-amber-700/10 border border-amber-500/25 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30">
                <Coins className="w-5 h-5" />
              </div>
              <div>
                <div className="text-[11px] font-bold uppercase tracking-wider text-amber-400/80">Trace Coin Balance</div>
                <div className="text-xs text-slate-300">Used for unit ingestion & premium unlocks</div>
              </div>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="font-mono text-xl font-black text-amber-300">{user.traceCoins ?? 200}</span>
              <span className="text-xs font-bold text-amber-400">T</span>
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Full Name
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-white focus:border-indigo-500 outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-white focus:border-indigo-500 outline-none"
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Academic Level
              </label>
              <select
                value={semesterStatus}
                onChange={(e) => setSemesterStatus(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:border-indigo-500 outline-none"
              >
                <option value="Year 1 - Pre-Clinical">Year 1 - Pre-Clinical</option>
                <option value="Year 2 - Foundations">Year 2 - Foundations</option>
                <option value="Year 3 - Core Clerkships">Year 3 - Core Clerkships</option>
                <option value="Year 4 - Clinical Rotations">Year 4 - Clinical Rotations</option>
                <option value="Postgraduate / Residency">Postgraduate / Residency</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Target Difficulty
              </label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:border-indigo-500 outline-none"
              >
                <option value="Standard (Foundational)">Standard (Foundational)</option>
                <option value="Medium (Standard)">Medium (Standard)</option>
                <option value="Rigorous (Clinical Boards)">Rigorous (Clinical Boards)</option>
                <option value="Advanced (Honors / Mastery)">Advanced (Honors / Mastery)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              <span>Default AI Consultant Persona</span>
            </label>
            <select
              value={aiPersona}
              onChange={(e) => setAiPersona(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-200 focus:border-indigo-500 outline-none"
            >
              <option value="Socratic Tutor">Socratic Tutor (Guides through questioning)</option>
              <option value="Clinical Attending">Clinical Attending (Bedside rounds rigor)</option>
              <option value="Exam Drillmaster">Exam Drillmaster (High-yield board pearls)</option>
              <option value="Feynman Explainer">Feynman Explainer (Radical intuition & analogies)</option>
            </select>
          </div>

          <div className="pt-3 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-sm font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex items-center gap-2 px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition-colors shadow-lg shadow-indigo-600/30"
            >
              {savedSuccess ? <Check className="w-4 h-4" /> : null}
              <span>{savedSuccess ? 'Saved' : 'Save Changes'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
