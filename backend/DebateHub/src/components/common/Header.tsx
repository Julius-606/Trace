
import React, { useState } from 'react';
import { GlukDebateLogo } from './GlukDebateLogo';
import { Member } from '../../types';
import { useAuth } from '../../contexts/AuthContext';
import { NotificationBell } from './NotificationBell';
import {
  Radio,
  Users,
  ChevronDown,
  Eye,
  ShieldCheck,
  Database,
  LogOut,
  LogIn,
  UserPlus,
} from 'lucide-react';

interface HeaderProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  currentUser: Member | null;
  allMembers: Member[];
  isLiveDebateActive: boolean;
  isExecutiveMode: boolean;
  onToggleExecutiveMode?: () => void;
  onOpenAuthModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  onSelectTab,
  currentUser,
  allMembers,
  isLiveDebateActive,
  isExecutiveMode,
  onToggleExecutiveMode,
  onOpenAuthModal,
}) => {
  const { logout, isLoggedIn } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Executive Navigation Items
  const executiveNavItems = [
    { id: 'executive', label: 'Executive Suite' },
    { id: 'finances', label: 'Treasury Ledger' },
    { id: 'agendas', label: 'Agendas & Duties' },
    { id: 'live-debate', label: 'Live Debate & Meet' },
    { id: 'members', label: 'Members Pool' },
    { id: 'motion-vault', label: 'Motion Vault' },
    { id: 'calendar', label: 'Calendar' },
  ];

  // Member Navigation Items
  const memberNavItems = [
    { id: 'member-home', label: 'My Member Hub' },
    { id: 'announcements', label: 'Announcements' },
    { id: 'live-debate', label: 'Live Debate & Meet' },
    { id: 'motion-vault', label: 'Motion Vault' },
    { id: 'calendar', label: 'Club Calendar' },
    { id: 'members', label: 'Alumni & Members' },
    { id: 'drills', label: 'Speaking Drills' },
  ];

  const activeNavItems = isExecutiveMode ? executiveNavItems : memberNavItems;

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/95 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        
        {/* Zone 1: Single Brand element */}
        <div className="flex items-center gap-3">
          <GlukDebateLogo size={36} />
          <a
            href="#dashboard"
            onClick={(e) => {
              e.preventDefault();
              onSelectTab(isExecutiveMode ? 'executive' : 'member-home');
            }}
            className="text-base font-bold tracking-tight text-white hover:text-amber-300 transition-colors whitespace-nowrap"
          >
            GLUK Debate Club
          </a>

          {/* Portal badge */}
          {currentUser && (
            <span
              className={`hidden sm:inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                isExecutiveMode
                  ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                  : 'bg-blue-500/15 text-blue-300 border border-blue-500/30'
              }`}
            >
              {isExecutiveMode ? 'Executive Suite' : 'Member Portal'}
            </span>
          )}
        </div>

        {/* Zone 2: Nav Links, single line */}
        <nav className="hidden lg:flex items-center gap-5 text-xs font-medium tracking-wide">
          {activeNavItems.map((item) => {
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`relative py-1 whitespace-nowrap transition-colors ${
                  isActive
                    ? 'text-amber-400 font-semibold'
                    : 'text-slate-400 hover:text-slate-100'
                }`}
              >
                {item.label}
                {isActive && (
                  <span className="absolute inset-x-0 -bottom-3.5 h-0.5 bg-amber-400 rounded-full" />
                )}
                {item.id === 'live-debate' && isLiveDebateActive && (
                  <span className="ml-1.5 inline-flex items-center gap-1 text-[10px] text-emerald-400 font-bold">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    LIVE
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Zone 3: Actions (Notifications, Toggle, User Login/Account) */}
        <div className="flex items-center gap-2.5">
          
          {/* Live Notification Bell */}
          {isLoggedIn && <NotificationBell onNavigateTab={onSelectTab} />}

          {/* Executive toggle to preview member view if user is executive */}
          {currentUser?.role === 'executive' && onToggleExecutiveMode && (
            <button
              onClick={onToggleExecutiveMode}
              className={`hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                isExecutiveMode
                  ? 'bg-slate-900 text-slate-300 border-slate-800 hover:text-white'
                  : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
              }`}
              title="Toggle between Executive Suite and Member View"
            >
              <Eye className="w-3.5 h-3.5 text-amber-400" />
              <span>{isExecutiveMode ? 'View as Member' : 'Return to Executive'}</span>
            </button>
          )}

          {/* User Account / Auth Button */}
          {isLoggedIn && currentUser ? (
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 p-1.5 pl-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-left transition-colors whitespace-nowrap"
              >
                <div className="flex flex-col text-right">
                  <span className="text-xs font-semibold text-slate-200 max-w-[110px] sm:max-w-[130px] truncate">
                    {currentUser.fullName}
                  </span>
                  <span className="text-[10px] text-amber-400 font-medium capitalize truncate">
                    {currentUser.executivePosition || currentUser.role}
                  </span>
                </div>
                <div className="w-7 h-7 rounded-md bg-gradient-to-br from-amber-500/30 to-blue-600/30 border border-amber-500/40 flex items-center justify-center text-amber-200 text-xs font-bold shrink-0">
                  {currentUser.fullName.charAt(0)}
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
              </button>

              {showUserMenu && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setShowUserMenu(false)}
                  />
                  <div className="absolute right-0 mt-2 w-64 rounded-xl bg-slate-900 border border-slate-800 shadow-2xl p-2 z-50 space-y-1">
                    <div className="px-3 py-2 border-b border-slate-800 mb-1">
                      <p className="text-xs font-bold text-white truncate">{currentUser.fullName}</p>
                      <p className="text-[11px] text-slate-400 truncate">{currentUser.email}</p>
                      <span className="mt-1 inline-block text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-amber-300">
                        {currentUser.executivePosition || currentUser.role}
                      </span>
                    </div>

                    <button
                      onClick={() => {
                        onSelectTab(isExecutiveMode ? 'executive' : 'member-home');
                        setShowUserMenu(false);
                      }}
                      className="w-full text-left px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800 hover:text-white rounded-lg transition-colors"
                    >
                      My Portal Dashboard
                    </button>

                    <button
                      onClick={() => {
                        logout();
                        setShowUserMenu(false);
                      }}
                      className="w-full text-left px-3 py-1.5 text-xs text-rose-400 hover:bg-rose-500/10 rounded-lg flex items-center gap-1.5 transition-colors"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : (
            <button
              onClick={onOpenAuthModal}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold rounded-lg text-xs transition-colors shadow-sm"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Log In / Sign Up</span>
            </button>
          )}

        </div>

      </div>

      {/* Mobile nav drawer row */}
      <div className="lg:hidden flex items-center gap-2 overflow-x-auto px-4 py-2 border-t border-slate-900 bg-slate-950 no-scrollbar">
        {activeNavItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onSelectTab(item.id)}
            className={`px-3 py-1 text-xs rounded-md whitespace-nowrap transition-colors ${
              currentTab === item.id
                ? 'bg-amber-400/20 text-amber-300 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>
    </header>
  );
};


