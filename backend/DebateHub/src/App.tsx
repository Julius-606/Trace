
import React, { useState, useEffect, useCallback } from 'react';
import {
  Member,
  DebateSession,
  FinancialTransaction,
  AgendaItem,
  Announcement,
  CalendarEvent,
  AlumniMentorshipNote,
} from './types';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { liveSync } from './services/liveSync';
import { Header } from './components/common/Header';
import { AuthModal } from './components/auth/AuthModal';
import { ExecutiveDashboard } from './components/executive/ExecutiveDashboard';
import { MemberDashboard } from './components/member/MemberDashboard';
import { LiveDebateSuite } from './components/debate/LiveDebateSuite';
import { FinancialLedger } from './components/executive/FinancialLedger';
import { MeetingAgendasLogistics } from './components/executive/MeetingAgendasLogistics';
import { MemberDirectoryPool } from './components/member/MemberDirectoryPool';
import { MotionVault } from './components/member/MotionVault';
import { CalendarActivities } from './components/member/CalendarActivities';
import { AnnouncementsFeed } from './components/member/AnnouncementsFeed';
import { DrillsPractice } from './components/debate/DrillsPractice';
import { GlukDebateLogo } from './components/common/GlukDebateLogo';
import { NeonConnectionModal } from './components/common/NeonConnectionModal';
import {
  QrCode,
  Download,
  Zap,
  Bell,
  Lock,
  Eye,
  ShieldCheck,
  Database,
  LogIn,
  Radio,
  CheckCircle2,
  Server,
} from 'lucide-react';

function AppContent() {
  const {
    currentUser,
    allMembers,
    isLoggedIn,
    isFreshDatabase,
    reinitializeDatabase,
    refreshAllData,
  } = useAuth();

  // Core collections synced from server database.json & Neon
  const [agendas, setAgendas] = useState<AgendaItem[]>([]);
  const [transactions, setTransactions] = useState<FinancialTransaction[]>([]);
  const [debates, setDebates] = useState<DebateSession[]>([]);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [mentorshipNotes, setMentorshipNotes] = useState<AlumniMentorshipNote[]>([]);
  const [isLoadingData, setIsLoadingData] = useState<boolean>(true);

  // Navigation
  const isExecutiveUser = currentUser?.role === 'executive';
  const [isExecutiveMode, setIsExecutiveMode] = useState<boolean>(true);
  const [currentTab, setCurrentTab] = useState<string>('member-home');

  // Modals
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showMemberPassModal, setShowMemberPassModal] = useState(false);
  const [showNeonModal, setShowNeonModal] = useState(false);
  const [liveToast, setLiveToast] = useState<{ title: string; message: string } | null>(null);

  // Sync mode based on logged-in user
  useEffect(() => {
    if (currentUser) {
      if (currentUser.role === 'executive') {
        setIsExecutiveMode(true);
        setCurrentTab('executive');
      } else {
        setIsExecutiveMode(false);
        setCurrentTab('member-home');
      }
    } else {
      setIsExecutiveMode(false);
      setCurrentTab('member-home');
    }
  }, [currentUser?.id, currentUser?.role]);

  // Open auth modal if database is fresh or user not logged in
  useEffect(() => {
    if (isFreshDatabase || !isLoggedIn) {
      setShowAuthModal(true);
    }
  }, [isFreshDatabase, isLoggedIn]);

  // Fetch all live collections from server
  const fetchAllCollections = useCallback(async () => {
    setIsLoadingData(true);
    try {
      const [agRes, txRes, debRes, annRes, evRes, menRes] = await Promise.all([
        fetch('/api/agendas').then((r) => (r.ok ? r.json() : [])).catch(() => []),
        fetch('/api/transactions').then((r) => (r.ok ? r.json() : [])).catch(() => []),
        fetch('/api/debates').then((r) => (r.ok ? r.json() : [])).catch(() => []),
        fetch('/api/announcements').then((r) => (r.ok ? r.json() : [])).catch(() => []),
        fetch('/api/events').then((r) => (r.ok ? r.json() : [])).catch(() => []),
        fetch('/api/mentorship').then((r) => (r.ok ? r.json() : [])).catch(() => []),
      ]);

      setAgendas(Array.isArray(agRes) ? agRes : []);
      setTransactions(Array.isArray(txRes) ? txRes : []);
      setDebates(Array.isArray(debRes) ? debRes : []);
      setAnnouncements(Array.isArray(annRes) ? annRes : []);
      setEvents(Array.isArray(evRes) ? evRes : []);
      setMentorshipNotes(Array.isArray(menRes) ? menRes : []);
    } catch (err) {
      console.warn('Error fetching live data:', err);
    } finally {
      setIsLoadingData(false);
    }
  }, []);

  useEffect(() => {
    fetchAllCollections();
  }, [fetchAllCollections]);

  // Listen to live Server-Sent Events (SSE) across the entire system!
  useEffect(() => {
    const unsubscribe = liveSync.subscribe((event) => {
      if (event.type === 'AGENDA_UPDATED') {
        fetch('/api/agendas').then((r) => r.json()).then(setAgendas).catch(() => {});
      }
      if (event.type === 'TRANSACTION_CREATED' || event.type === 'DUES_VERIFIED') {
        fetch('/api/transactions').then((r) => r.json()).then(setTransactions).catch(() => {});
      }
      if (event.type === 'DEBATE_UPDATED') {
        fetch('/api/debates').then((r) => r.json()).then(setDebates).catch(() => {});
      }
      if (event.type === 'ANNOUNCEMENT_CREATED') {
        fetch('/api/announcements').then((r) => r.json()).then(setAnnouncements).catch(() => {});
      }
      if (event.type === 'EVENT_CREATED') {
        fetch('/api/events').then((r) => r.json()).then(setEvents).catch(() => {});
      }
      if (event.type === 'MENTORSHIP_UPDATED') {
        fetch('/api/mentorship').then((r) => r.json()).then(setMentorshipNotes).catch(() => {});
      }

      // Show live toast banner when notifications arrive
      if (event.type === 'NOTIFICATION_NEW') {
        const notif = event.payload;
        setLiveToast({ title: notif.title, message: notif.message });
        setTimeout(() => setLiveToast(null), 5000);
      }

      if (event.type === 'SYSTEM_REINITIALIZED') {
        fetchAllCollections();
      }
    });

    return () => unsubscribe();
  }, [fetchAllCollections]);

  const handleToggleExecutiveMode = () => {
    if (!isExecutiveUser) return;
    const nextMode = !isExecutiveMode;
    setIsExecutiveMode(nextMode);
    setCurrentTab(nextMode ? 'executive' : 'member-home');
  };

  // Operations that write to Express backend & Neon/JSON database
  const handleAddTransaction = async (txn: FinancialTransaction) => {
    setTransactions((prev) => [txn, ...prev]);
    try {
      await fetch('/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(txn),
      });
    } catch (err) {
      console.error('Failed to post transaction:', err);
    }
  };

  const handleVerifyMemberPayment = async (memberId: string, mpesaRef: string) => {
    try {
      const res = await fetch('/api/members/verify-dues', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          memberId,
          mpesaRef,
          verifiedBy: currentUser?.fullName || 'Finance Secretary',
        }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.transaction) {
          setTransactions((prev) => [data.transaction, ...prev]);
        }
      }
    } catch (err) {
      console.error('Failed to verify dues:', err);
    }
    await refreshAllData();
  };

  const handleSubmitDuesMpesa = async (mpesaCode: string) => {
    if (!currentUser) return;
    try {
      await fetch('/api/members/submit-mpesa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          memberId: currentUser.id,
          mpesaCode,
        }),
      });
    } catch (err) {
      console.error('Failed to submit M-Pesa code:', err);
    }
    await refreshAllData();
  };

  const handleUpdateAgendas = async (updatedAgendas: AgendaItem[]) => {
    setAgendas(updatedAgendas);
    try {
      for (const ag of updatedAgendas) {
        await fetch(`/api/agendas/${ag.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(ag),
        });
      }
    } catch (err) {
      console.error('Failed to update agenda:', err);
    }
  };

  const handleUpdateLiveSession = async (updatedSession: DebateSession) => {
    setDebates((prev) =>
      prev.map((d) => (d.id === updatedSession.id ? updatedSession : d))
    );
    try {
      await fetch(`/api/debates/${updatedSession.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedSession),
      });
    } catch (err) {
      console.error('Failed to update live session:', err);
    }
  };

  const handleSaveSessionToArchive = async (session: DebateSession) => {
    setDebates((prev) =>
      prev.map((d) => (d.id === session.id ? session : d))
    );
    try {
      await fetch(`/api/debates/${session.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(session),
      });
    } catch (err) {
      console.error('Failed to archive session:', err);
    }
    await refreshAllData();
    setCurrentTab('motion-vault');
  };

  const handleAddAnnouncement = async (ann: Announcement) => {
    setAnnouncements((prev) => [ann, ...prev]);
    try {
      await fetch('/api/announcements', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ann),
      });
    } catch (err) {
      console.error('Failed to add announcement:', err);
    }
  };

  const handleAddEvent = async (ev: CalendarEvent) => {
    setEvents((prev) => [ev, ...prev]);
    try {
      await fetch('/api/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ev),
      });
    } catch (err) {
      console.error('Failed to add event:', err);
    }
  };

  const handleAddMentorshipNote = async (note: AlumniMentorshipNote) => {
    setMentorshipNotes((prev) => [note, ...prev]);
    try {
      await fetch('/api/mentorship', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(note),
      });
    } catch (err) {
      console.error('Failed to save mentorship note:', err);
    }
  };

  const handleExportDatabase = () => {
    const fullDb = {
      users: allMembers,
      agendas,
      transactions,
      debates,
      announcements,
      events,
      mentorshipNotes,
      exportedAt: new Date().toISOString(),
      institution: 'Great Lakes University of Kisumu Debate Club',
    };
    const jsonStr = JSON.stringify(fullDb, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `GLUK_Debate_Database_Export_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
  };

  const handleResetFresh = async () => {
    if (window.confirm('Reinitialize database completely fresh? This will reset the database so you can start from scratch with brand new accounts.')) {
      await reinitializeDatabase(false);
      setShowAuthModal(true);
    }
  };

  const liveSession = debates.find((d) => d.status === 'Live Now') || debates[0];

  const isExecutiveTab = currentTab === 'executive' || currentTab === 'finances' || currentTab === 'agendas';
  const showAccessDenied = isExecutiveTab && !isExecutiveMode;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-amber-500/20 selection:text-amber-200">
      
      {/* Live Push Notification Toast Banner */}
      {liveToast && (
        <div className="fixed top-20 right-6 z-50 max-w-sm p-4 rounded-xl bg-slate-900 border border-amber-500/40 text-xs shadow-2xl space-y-1 animate-bounce">
          <div className="flex items-center gap-2 font-bold text-amber-300">
            <Bell className="w-4 h-4 text-amber-400" />
            <span>{liveToast.title}</span>
          </div>
          <p className="text-slate-300 leading-relaxed text-[11px]">{liveToast.message}</p>
        </div>
      )}

      {/* Top Header */}
      <Header
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        currentUser={currentUser}
        allMembers={allMembers}
        isLiveDebateActive={debates.some((d) => d.status === 'Live Now')}
        isExecutiveMode={isExecutiveMode}
        onToggleExecutiveMode={isExecutiveUser ? handleToggleExecutiveMode : undefined}
        onOpenAuthModal={() => setShowAuthModal(true)}
      />

      {/* Sub-bar showing contextual portal mode & database state */}
      <div className="border-b border-slate-900 bg-slate-950/70 px-4 sm:px-6 lg:px-8 py-2">
        <div className="mx-auto max-w-7xl flex flex-wrap items-center justify-between gap-3 text-xs">
          
          <div className="flex items-center gap-3">
            {isExecutiveMode ? (
              <span className="inline-flex items-center gap-1.5 text-amber-400 font-semibold">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Executive Operations Center</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-blue-300 font-semibold">
                <span>Member Portal</span>
              </span>
            )}

            <span className="text-slate-700">·</span>

            <button
              onClick={() => setCurrentTab('announcements')}
              className={`inline-flex items-center gap-1 transition-colors ${
                currentTab === 'announcements'
                  ? 'text-amber-400 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Bell className="w-3.5 h-3.5" />
              <span>Announcements ({announcements.length})</span>
            </button>

            <span className="text-slate-700">·</span>

            <button
              onClick={() => setCurrentTab('drills')}
              className={`inline-flex items-center gap-1 transition-colors ${
                currentTab === 'drills'
                  ? 'text-amber-400 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              <span>Speaking Drills</span>
            </button>
          </div>

          <div className="flex items-center gap-3 text-[11px] text-slate-500">
            <button
              onClick={() => setShowNeonModal(true)}
              className="flex items-center gap-1.5 font-mono text-emerald-400 hover:underline"
              title="Click to check database health and schema status"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>Live DB & Neon Status</span>
            </button>

            <span>·</span>

            {currentUser ? (
              <>
                <span>
                  Signed in: <strong className="text-slate-300">{currentUser.fullName}</strong> ({currentUser.executivePosition || currentUser.role})
                </span>
                <button
                  onClick={() => setShowMemberPassModal(true)}
                  className="text-amber-400 hover:text-amber-300 font-medium underline underline-offset-2"
                >
                  My ID Pass
                </button>
              </>
            ) : (
              <button
                onClick={() => setShowAuthModal(true)}
                className="text-amber-400 hover:text-amber-300 font-bold"
              >
                Sign In to Account
              </button>
            )}
          </div>

        </div>
      </div>

      {/* Main Viewport Container */}
      <main className="flex-1 mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-6">
        
        {/* Access Denied Shield if a member somehow reaches executive tabs */}
        {showAccessDenied ? (
          <div className="py-16 text-center max-w-md mx-auto space-y-4">
            <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/30 flex items-center justify-center mx-auto text-rose-400">
              <Lock className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-bold text-white">
              Executive Committee Privilege Required
            </h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              Treasury ledgers, financial statements, and meeting action delegations are confidential and reserved strictly for the executive committee.
            </p>
            <button
              onClick={() => setCurrentTab('member-home')}
              className="px-4 py-2 bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold rounded-lg text-xs"
            >
              Return to Member Dashboard
            </button>
          </div>
        ) : (
          <>
            {/* 1. MEMBER DASHBOARD (Personal standing only) */}
            {currentTab === 'member-home' && currentUser && (
              <MemberDashboard
                currentUser={currentUser}
                announcements={announcements}
                upcomingEvents={events}
                activeDebateSession={liveSession}
                mentorshipNotes={mentorshipNotes}
                onNavigate={setCurrentTab}
                onSubmitDuesMpesa={handleSubmitDuesMpesa}
                onOpenPassModal={() => setShowMemberPassModal(true)}
              />
            )}

            {/* If user is not logged in on home screen */}
            {currentTab === 'member-home' && !currentUser && (
              <div className="py-16 text-center max-w-md mx-auto space-y-4">
                <GlukDebateLogo size={64} className="justify-center" />
                <h2 className="text-xl font-bold text-white">
                  Welcome to GLUK Debate Club
                </h2>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Sign in or create a student member account to participate in rounds, track your attendance, and access past debate archives.
                </p>
                <button
                  onClick={() => setShowAuthModal(true)}
                  className="px-5 py-2.5 bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold rounded-lg text-xs"
                >
                  Sign In / Create Account
                </button>
              </div>
            )}

            {/* 2. EXECUTIVE DASHBOARD */}
            {currentTab === 'executive' && (
              <ExecutiveDashboard
                members={allMembers}
                debates={debates}
                transactions={transactions}
                agendas={agendas}
                announcements={announcements}
                onNavigate={setCurrentTab}
                onExportData={handleExportDatabase}
              />
            )}

            {/* 3. EXECUTIVE-ONLY: FINANCIAL LEDGER */}
            {currentTab === 'finances' && (
              <FinancialLedger
                transactions={transactions}
                members={allMembers}
                onAddTransaction={handleAddTransaction}
                onVerifyMemberPayment={handleVerifyMemberPayment}
              />
            )}

            {/* 4. EXECUTIVE-ONLY: MEETING AGENDAS & DELEGATED DUTIES */}
            {currentTab === 'agendas' && (
              <MeetingAgendasLogistics
                agendas={agendas}
                members={allMembers}
                onUpdateAgendas={handleUpdateAgendas}
              />
            )}

            {/* 5. SHARED: LIVE DEBATE & MEET COMPANION */}
            {currentTab === 'live-debate' && liveSession && (
              <LiveDebateSuite
                session={liveSession}
                allMembers={allMembers}
                onUpdateSession={handleUpdateLiveSession}
                onSaveSessionToArchive={handleSaveSessionToArchive}
              />
            )}

            {/* 6. SHARED: MOTION VAULT & ARCHIVES */}
            {currentTab === 'motion-vault' && (
              <MotionVault debates={debates} />
            )}

            {/* 7. SHARED: CALENDAR OF ACTIVITIES */}
            {currentTab === 'calendar' && (
              <CalendarActivities
                events={events}
                currentUser={currentUser || allMembers[0]}
                onAddEvent={handleAddEvent}
              />
            )}

            {/* 8. SHARED: MEMBERS POOL & ALUMNI NETWORK */}
            {currentTab === 'members' && (
              <MemberDirectoryPool
                members={allMembers}
                currentUser={currentUser || allMembers[0]}
                mentorshipNotes={mentorshipNotes}
                onAddMentorshipNote={handleAddMentorshipNote}
              />
            )}

            {/* 9. SHARED: ANNOUNCEMENTS */}
            {currentTab === 'announcements' && (
              <AnnouncementsFeed
                announcements={announcements}
                currentUser={currentUser || allMembers[0]}
                onAddAnnouncement={handleAddAnnouncement}
                onSubmitDuesMpesa={handleSubmitDuesMpesa}
                onOpenPassModal={() => setShowMemberPassModal(true)}
              />
            )}

            {/* 10. SHARED: SPEAKING DRILLS */}
            {currentTab === 'drills' && (
              <DrillsPractice />
            )}
          </>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 px-4 sm:px-6 lg:px-8 text-xs text-slate-500">
        <div className="mx-auto max-w-7xl flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <GlukDebateLogo size={24} />
            <span>
              Great Lakes University of Kisumu Debate Club · Kibos Main Campus, Kisumu, Kenya
            </span>
          </div>

          <div className="flex items-center gap-4 text-slate-400">
            <button
              onClick={() => setShowNeonModal(true)}
              className="hover:text-amber-400 transition-colors flex items-center gap-1"
            >
              <Server className="w-3.5 h-3.5" />
              <span>Database Status</span>
            </button>
            <span>·</span>
            <button
              onClick={handleExportDatabase}
              className="hover:text-white transition-colors"
            >
              Export JSON Database
            </button>
            <span>·</span>
            <button
              onClick={handleResetFresh}
              className="hover:text-amber-400 transition-colors"
            >
              Start Afresh (Clear Database)
            </button>
          </div>
        </div>
      </footer>

      {/* Auth Modal (Sign Up & Login) */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        isFreshDatabase={isFreshDatabase}
        onSeedTemplates={async () => {
          await reinitializeDatabase(true);
          setShowAuthModal(false);
          fetchAllCollections();
        }}
      />

      {/* Database & Neon Status Modal */}
      <NeonConnectionModal
        isOpen={showNeonModal}
        onClose={() => setShowNeonModal(false)}
      />

      {/* Digital Member Pass Modal */}
      {showMemberPassModal && currentUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-amber-500/30 p-6 shadow-2xl space-y-5 text-center relative overflow-hidden">
            <div className="absolute -top-12 left-1/2 -translate-x-1/2 w-40 h-40 bg-amber-500/10 rounded-full blur-2xl pointer-events-none" />

            <div className="flex justify-center">
              <GlukDebateLogo size={64} />
            </div>

            <div>
              <span className="text-[10px] uppercase font-bold tracking-widest text-amber-400 block">
                Great Lakes University of Kisumu
              </span>
              <h3 className="text-lg font-bold text-white mt-0.5">
                {currentUser.fullName}
              </h3>
              <p className="text-xs font-mono text-slate-400">
                {currentUser.studentId}
              </p>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-left space-y-1.5">
              <div className="flex justify-between">
                <span className="text-slate-400">Portfolio:</span>
                <span className="font-semibold text-slate-200 capitalize">
                  {currentUser.executivePosition || currentUser.role}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Faculty:</span>
                <span className="font-semibold text-slate-200 truncate max-w-[170px]">
                  {currentUser.faculty}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Semester Dues:</span>
                <span
                  className={`font-bold ${
                    currentUser.membershipStatus === 'Paid'
                      ? 'text-emerald-400'
                      : 'text-amber-400'
                  }`}
                >
                  {currentUser.membershipStatus} (AY 2026/2027)
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Attendance:</span>
                <span className="font-mono text-slate-200">
                  {currentUser.attendanceRate}% ({currentUser.debatesAttendedCount} Sessions)
                </span>
              </div>
            </div>

            <div className="flex flex-col items-center justify-center p-3 rounded-xl bg-white text-slate-950 space-y-1">
              <div className="w-24 h-24 border-2 border-slate-950 p-1 flex items-center justify-center bg-slate-100">
                <QrCode className="w-20 h-20 text-slate-950" />
              </div>
              <span className="text-[9px] font-mono tracking-widest uppercase font-bold text-slate-700">
                GLUK-DC-OFFICIAL-DEBATER
              </span>
            </div>

            <button
              onClick={() => setShowMemberPassModal(false)}
              className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold transition-colors"
            >
              Close Pass
            </button>
          </div>
        </div>
      )}

    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}


