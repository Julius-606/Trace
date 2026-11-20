import React from 'react';
import {
  X,
  User as UserIcon,
  Archive,
  BookOpen,
  MessageSquare,
  Sparkles,
  Calendar,
  Globe,
  Settings,
  LogOut,
  GraduationCap,
  Users,
  ShieldAlert,
  Bookmark as BookmarkIcon
} from 'lucide-react';
import { User, UserRole } from '../types';

interface NavigationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  user: User;
  onSelectTab: (tab: string) => void;
  onOpenAccount: () => void;
  onOpenArchives: () => void;
  onOpenManageUnits: () => void;
  onOpenSync: () => void;
  onOpenBrowser: (url?: string) => void;
  onChangeRole: (role: UserRole) => void;
  onLogout: () => void;
  onOpenAdminConsole?: () => void;
}

export const NavigationDrawer: React.FC<NavigationDrawerProps> = ({
  isOpen,
  onClose,
  user,
  onSelectTab,
  onOpenAccount,
  onOpenArchives,
  onOpenManageUnits,
  onOpenSync,
  onOpenBrowser,
  onChangeRole,
  onLogout,
  onOpenAdminConsole
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex animate-in fade-in duration-200">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Drawer Content */}
      <div className="relative w-80 max-w-[85vw] h-full bg-slate-900 border-r border-slate-800 shadow-2xl flex flex-col z-10 animate-in slide-in-from-left duration-250">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400 font-black">
                T
              </div>
              <div>
                <h2 className="text-base font-bold text-white leading-tight">Trace Learning</h2>
                <p className="text-xs text-indigo-400 font-medium">{user.role} Workspace</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-200">{user.username}</p>
              <p className="text-[11px] text-slate-400">{user.semesterStatus}</p>
            </div>
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              {user.role}
            </span>
          </div>
        </div>

        {/* Menu Items */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1 text-sm">
          <div className="px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-500">
            Learning Trail
          </div>

          <button
            onClick={() => {
              onSelectTab('dashboard');
              onClose();
            }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-200 hover:bg-slate-800 hover:text-indigo-300 transition-colors"
          >
            <GraduationCap className="w-4 h-4 text-indigo-400" />
            <span>Dashboard</span>
          </button>

          <button
            onClick={() => {
              onSelectTab('socratic');
              onClose();
            }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-200 hover:bg-slate-800 hover:text-indigo-300 transition-colors"
          >
            <MessageSquare className="w-4 h-4 text-indigo-400" />
            <span>Consultations (AI Tutor)</span>
          </button>

          <button
            onClick={() => {
              onSelectTab('assessment');
              onClose();
            }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-200 hover:bg-slate-800 hover:text-indigo-300 transition-colors"
          >
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>Assessment Center</span>
          </button>

          <button
            onClick={() => {
              onSelectTab('timetable');
              onClose();
            }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-200 hover:bg-slate-800 hover:text-indigo-300 transition-colors"
          >
            <Calendar className="w-4 h-4 text-emerald-400" />
            <span>Dynamic Schedule</span>
          </button>

          <button
            onClick={() => {
              onSelectTab('connect');
              onClose();
            }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-200 hover:bg-slate-800 hover:text-indigo-300 transition-colors"
          >
            <Users className="w-4 h-4 text-sky-400" />
            <span>Study Connect &amp; Peers</span>
          </button>

          <button
            onClick={() => {
              onSelectTab('bookmarks');
              onClose();
            }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-200 hover:bg-slate-800 hover:text-indigo-300 transition-colors"
          >
            <BookmarkIcon className="w-4 h-4 text-amber-400" />
            <span>Saved Highlights</span>
          </button>

          <button
            onClick={() => {
              onOpenBrowser('https://en.wikipedia.org/wiki/Medicine');
              onClose();
            }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-200 hover:bg-slate-800 hover:text-indigo-300 transition-colors"
          >
            <Globe className="w-4 h-4 text-blue-400" />
            <span>Trace Browser</span>
          </button>

          <button
            onClick={() => {
              if (onOpenAdminConsole) {
                onOpenAdminConsole();
              } else {
                onSelectTab('dashboard');
              }
              onClose();
            }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-red-300 bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 transition-colors font-semibold"
            title="Open Isolated Admin & Backend Telemetry Dashboard"
          >
            <ShieldAlert className="w-4 h-4 text-red-400" />
            <div className="flex flex-col text-left">
              <span className="text-xs font-bold">Admin Telemetry Console</span>
              <span className="text-[10px] text-red-400/80 font-normal">Superuser & Backend Logs</span>
            </div>
          </button>

          <div className="px-3 pt-4 pb-1 text-[11px] font-bold uppercase tracking-wider text-slate-500">
            Account & Curriculum
          </div>

          <button
            onClick={() => {
              onOpenAccount();
              onClose();
            }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-200 hover:bg-slate-800 hover:text-indigo-300 transition-colors"
          >
            <UserIcon className="w-4 h-4 text-slate-400" />
            <span>Account Profile</span>
          </button>

          <button
            onClick={() => {
              onOpenArchives();
              onClose();
            }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-200 hover:bg-slate-800 hover:text-indigo-300 transition-colors"
          >
            <Archive className="w-4 h-4 text-slate-400" />
            <span>Archives & Trail</span>
          </button>

          <button
            onClick={() => {
              onOpenManageUnits();
              onClose();
            }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-200 hover:bg-slate-800 hover:text-indigo-300 transition-colors"
          >
            <BookOpen className="w-4 h-4 text-slate-400" />
            <span>Manage Units</span>
          </button>

          <button
            onClick={() => {
              onOpenSync();
              onClose();
            }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-200 hover:bg-slate-800 hover:text-indigo-300 transition-colors"
          >
            <Settings className="w-4 h-4 text-slate-400" />
            <span>Settings &amp; Version</span>
          </button>

          {/* Role Switcher */}
          <div className="px-3 pt-4 pb-1 text-[11px] font-bold uppercase tracking-wider text-slate-500">
            Switch Perspective
          </div>
          <div className="grid grid-cols-4 gap-1 px-1 py-1">
            {(['Student', 'Teacher', 'Parent', 'Admin'] as UserRole[]).map((r) => (
              <button
                key={r}
                onClick={() => {
                  onChangeRole(r);
                  onClose();
                }}
                className={`py-1.5 px-2 rounded-lg text-xs font-semibold transition-colors ${
                  user.role === r
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        {/* Footer Logout */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60">
          <button
            onClick={() => {
              onLogout();
              onClose();
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-red-950/30 border border-red-800/40 text-red-400 hover:bg-red-900/50 hover:text-red-200 transition-colors font-semibold text-xs tracking-wide"
          >
            <LogOut className="w-4 h-4" />
            <span>SIGN OUT / SWITCH USER</span>
          </button>
        </div>
      </div>
    </div>
  );
};
