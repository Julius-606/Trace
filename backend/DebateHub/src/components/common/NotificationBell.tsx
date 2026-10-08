
import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { ClubNotification } from '../../types';
import {
  Bell,
  CheckCircle,
  Clock,
  ShieldAlert,
  CreditCard,
  Radio,
  ExternalLink,
  X,
} from 'lucide-react';

interface NotificationBellProps {
  onNavigateTab: (tab: string) => void;
}

export const NotificationBell: React.FC<NotificationBellProps> = ({ onNavigateTab }) => {
  const { notifications, unreadCount, markNotificationRead } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  const getIcon = (type: string) => {
    switch (type) {
      case 'duty_delegated':
        return <Clock className="w-4 h-4 text-amber-400" />;
      case 'dues_verified':
        return <CreditCard className="w-4 h-4 text-emerald-400" />;
      case 'debate_round':
        return <Radio className="w-4 h-4 text-blue-400" />;
      default:
        return <Bell className="w-4 h-4 text-amber-300" />;
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition-colors"
        title="Club Notifications"
      >
        <Bell className="w-4 h-4" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-amber-400 text-[10px] font-bold text-slate-950">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-xl bg-slate-900 border border-slate-800 shadow-2xl p-3 z-50 space-y-2">
            
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <div className="flex items-center gap-1.5">
                <Bell className="w-3.5 h-3.5 text-amber-400" />
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Live Notifications ({notifications.length})
                </span>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-white p-0.5"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="max-h-80 overflow-y-auto space-y-2 pr-1">
              {notifications.length === 0 ? (
                <div className="py-8 text-center text-xs text-slate-500">
                  No notifications yet. You're completely up to date!
                </div>
              ) : (
                notifications.map((n) => (
                  <div
                    key={n.id}
                    className={`p-3 rounded-lg border text-xs space-y-1.5 transition-all ${
                      n.isRead
                        ? 'bg-slate-950/40 border-slate-800/60 opacity-70'
                        : 'bg-slate-950/90 border-slate-700 shadow-sm'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        {getIcon(n.type)}
                        <span className="font-bold text-white text-xs">
                          {n.title}
                        </span>
                      </div>
                      {!n.isRead && (
                        <button
                          onClick={() => markNotificationRead(n.id)}
                          className="text-[10px] text-amber-400 hover:text-amber-300 whitespace-nowrap font-medium"
                        >
                          Mark read
                        </button>
                      )}
                    </div>

                    <p className="text-slate-300 text-[11px] leading-relaxed">
                      {n.message}
                    </p>

                    <div className="flex items-center justify-between pt-1 border-t border-slate-800/60 text-[10px] text-slate-500">
                      <span>{new Date(n.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      {n.linkTab && (
                        <button
                          onClick={() => {
                            onNavigateTab(n.linkTab!);
                            setIsOpen(false);
                            if (!n.isRead) markNotificationRead(n.id);
                          }}
                          className="text-amber-400 hover:text-amber-300 font-semibold flex items-center gap-1"
                        >
                          <span>Open Section</span>
                          <ExternalLink className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

          </div>
        </>
      )}
    </div>
  );
};


