import React, { useState, useEffect } from 'react';
import {
  Menu,
  Sparkles,
  BookOpen,
  MessageSquare,
  Calendar,
  Globe,
  Settings,
  Archive,
  User as UserIcon,
  Bookmark,
  Users,
  Search,
  Bell,
  ShieldAlert,
  Smartphone,
  Tablet,
  Wifi,
  Battery,
  Home,
  CheckCircle2,
  RefreshCw,
  Coins
} from 'lucide-react';
import { User, Unit, UserRole } from './types';
import { TraceStore } from './lib/store';
import { DynamicBackground } from './components/DynamicBackground';
import { NavigationDrawer } from './components/NavigationDrawer';
import { LoginScreen } from './components/LoginScreen';
import { StudentDashboard } from './components/StudentDashboard';
import { LearnScreen } from './components/LearnScreen';
import { QuizInterface } from './components/QuizInterface';
import { ChatInterface } from './components/ChatInterface';
import { TimetableTab } from './components/TimetableTab';
import { LibraryScreen } from './components/LibraryScreen';
import { UnitOutlineScreen } from './components/UnitOutlineScreen';
import { LearningRepositoryScreen } from './components/LearningRepositoryScreen';
import { ConnectTab } from './components/ConnectTab';
import { AdminDashboard } from './components/AdminDashboard';
import { TeacherDashboard } from './components/TeacherDashboard';
import { ParentDashboard } from './components/ParentDashboard';
import { InAppBrowser } from './components/InAppBrowser';
import { AccountModal } from './components/AccountModal';
import { ArchivesModal } from './components/ArchivesModal';
import { ManageUnitsModal } from './components/ManageUnitsModal';
import { SyncModal } from './components/SyncModal';
import { BookmarksScreen } from './components/BookmarksScreen';
import { SettingsModal, applyAppearance, getSavedAppearance } from './components/SettingsModal';

export const App: React.FC = () => {
  const [user, setUser] = useState<User>(TraceStore.getUser());
  const [isLoggedIn, setIsLoggedIn] = useState(true);
  const [units, setUnits] = useState<Unit[]>(TraceStore.getUnits());

  useEffect(() => {
    applyAppearance(getSavedAppearance());
  }, []);

  // Preview Mode: 'mobile' (Android phone mockup preview) or 'responsive' (full-width)
  const [previewMode, setPreviewMode] = useState<'mobile' | 'responsive'>('mobile');

  // Screen Routing
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [activeUnitId, setActiveUnitId] = useState<number>(1);
  const [activeSubtopicId, setActiveSubtopicId] = useState<number | undefined>(undefined);
  const [quizUnitName, setQuizUnitName] = useState<string>('');
  const [quizTopicName, setQuizTopicName] = useState<string>('');

  // Modals
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isAccountOpen, setIsAccountOpen] = useState(false);
  const [isArchivesOpen, setIsArchivesOpen] = useState(false);
  const [isManageUnitsOpen, setIsManageUnitsOpen] = useState(false);
  const [isSyncOpen, setIsSyncOpen] = useState(false);
  const [browserUrl, setBrowserUrl] = useState<string | null>(null);

  const timetable = TraceStore.getTimetable();

  const triggerCloudSync = async (userId: string) => {
    try {
      const res = await fetch(`/api/user/${userId}/sync`);
      if (res.ok) {
        const contentType = res.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
          return;
        }
        let data: any;
        try {
          data = await res.json();
        } catch {
          return;
        }
        if (!data) return;
        
        if (data.progress && data.progress.length > 0) {
          const localUnits = TraceStore.getUnits();
          for (const p of data.progress) {
            if (p.node_type === 'subtopic' && p.status === 'Completed') {
              for (const unit of localUnits) {
                for (const mod of unit.modules) {
                  for (const topic of mod.topics) {
                    for (const sub of topic.subtopics) {
                      if (sub.id === p.node_id) {
                        sub.isCompleted = true;
                      }
                    }
                  }
                }
              }
            }
          }
          TraceStore.saveUnits(localUnits);
          setUnits([...localUnits]);
        }

        if (data.bookmarks && data.bookmarks.length > 0) {
          const localBookmarks = TraceStore.getBookmarks();
          for (const b of data.bookmarks) {
            const exists = localBookmarks.some((lb) => lb.target === b.target || (lb.subtopicId === b.subtopicId && lb.objectiveDescription === b.objectiveDescription));
            if (!exists) {
              localBookmarks.unshift({
                id: b.id ? String(b.id) : `bm-${Date.now()}-${Math.random()}`,
                userId: userId,
                subtopicId: b.subtopicId || 0,
                subtopicName: b.subtopicName || b.title || 'Saved Item',
                objectiveDescription: b.objectiveDescription || '',
                excerpt: b.excerpt || b.context || '',
                timestamp: b.timestamp * 1000 || Date.now(),
                notes: b.notes || '',
                type: b.type,
                title: b.title,
                target: b.target
              } as any);
            }
          }
          localStorage.setItem('trace_bookmarks', JSON.stringify(localBookmarks));
        }

        if (data.quizzes && data.quizzes.length > 0) {
          const localHistory = TraceStore.getQuizHistory();
          for (const q of data.quizzes) {
            const exists = localHistory.some((lh) => lh.timestamp === q.timestamp || lh.id === String(q.id));
            if (!exists) {
              localHistory.unshift({
                id: String(q.id),
                userId: userId,
                unitName: q.unit_name,
                score: q.score,
                total: q.total,
                pnlScore: Math.round(q.pnl * 100) || Math.round((q.score / q.total) * 100),
                timestamp: typeof q.timestamp === 'number' ? q.timestamp : Date.now()
              });
            }
          }
          localStorage.setItem('trace_quiz_history', JSON.stringify(localHistory));
        }

        if (data.chats && data.chats.length > 0) {
          const localSessions = TraceStore.getChatSessions();
          for (const s of data.chats) {
            const exists = localSessions.some((ls) => ls.id === String(s.id));
            if (!exists) {
              localSessions.unshift({
                id: String(s.id),
                userId: userId,
                title: s.title,
                description: s.description || '',
                timestamp: s.timestamp * 1000 || Date.now(),
                messages: (s.messages || []).map((m: any) => ({
                  id: String(m.id),
                  sender: m.role === 'user' ? 'user' : 'assistant',
                  text: m.content,
                  timestamp: typeof m.timestamp === 'number' ? m.timestamp : Date.now()
                }))
              });
            }
          }
          localStorage.setItem('trace_chat_sessions', JSON.stringify(localSessions));
        }

        if (data.user) {
          const updatedUser: User = {
            id: String(data.user.id),
            username: data.user.username || 'Student',
            email: data.user.email || '',
            role: data.user.role as any || 'Student',
            difficulty: data.user.difficulty || 'Medium (Standard)',
            semesterStatus: data.user.semesterStatus || 'Active',
            aiPersona: data.user.aiPersona || 'Helper',
            sensoryMode: data.user.sensoryMode || 'Standard',
            activeUnits: data.user.activeUnits || [],
            traceCoins: data.user.trace_coins ?? data.user.traceCoins ?? (data.user.role === 'Admin' ? 500 : 200)
          };
          setUser(updatedUser);
          TraceStore.setUser(updatedUser);
        }
      }

      // 2. Post merged client state back to the FastAPI cloud backend
      const localUnits = TraceStore.getUnits();
      const progressItems: any[] = [];
      for (const unit of localUnits) {
        for (const mod of unit.modules) {
          for (const topic of mod.topics) {
            for (const sub of topic.subtopics) {
              if (sub.isCompleted) {
                progressItems.push({
                  node_id: sub.id,
                  node_type: 'subtopic',
                  status: 'Completed',
                  last_studied_at: Date.now() / 1000
                });
              }
            }
          }
        }
      }

      const localBookmarks = TraceStore.getBookmarks();
      const bookmarksItems = localBookmarks.map((b) => ({
        type: b.type || 'learn',
        title: b.title || b.subtopicName || 'Saved Item',
        target: b.target || String(b.subtopicId || ''),
        context: b.excerpt || b.objectiveDescription || '',
        timestamp: b.timestamp / 1000 || Date.now() / 1000
      }));

      try {
        await fetch(`/api/user/${userId}/sync`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            progress: progressItems,
            bookmarks: bookmarksItems
          })
        });
      } catch {
        // Offline or sandbox note - local state already saved
      }

    } catch (err) {
      console.warn("Cloud synchronization fallback notice (running offline-first):", err);
    }
  };

  useEffect(() => {
    if (isLoggedIn && user && user.id) {
      triggerCloudSync(user.id);
    }
  }, [isLoggedIn, user]);

  const handleSelectUnitToLearn = (unitId: number, subtopicId?: number) => {
    setActiveUnitId(unitId);
    setActiveSubtopicId(subtopicId);
    setCurrentTab('learn');
  };

  const handleLaunchQuiz = (unitName: string, topicName?: string) => {
    setQuizUnitName(unitName);
    setQuizTopicName(topicName || '');
    setCurrentTab('quizzes');
  };

  const handleToggleActiveUnit = (unitId: number, isActive: boolean) => {
    const updated = TraceStore.toggleUnitActive(unitId, isActive);
    setUnits(updated);
  };

  const handleDeleteUnit = async (unitId: number) => {
    try {
      await fetch(`/api/units/${unitId}`, { method: 'DELETE' });
    } catch (err) {
      console.warn('Backend unit delete note:', err);
    }
    const updated = TraceStore.deleteUnit(unitId);
    setUnits(updated);
  };

  const handleRestoreArchivedUnit = (unitId: number) => {
    const updated = TraceStore.toggleUnitActive(unitId, true);
    setUnits(updated);
  };

  const handleChangeRole = (role: UserRole) => {
    const all = TraceStore.getAllUsers();
    let matched = all.find((u) => u.role === role);
    if (!matched && role === 'Admin') {
      matched = {
        id: '4',
        username: 'Admin Root',
        email: 'admin@trace.edu',
        role: 'Admin',
        difficulty: 'Superuser',
        semesterStatus: 'System Administration & Oversight',
        aiPersona: 'System Architect & Lead Consultant',
        sensoryMode: 'Standard',
        activeUnits: ['Biochemistry II', 'General Surgery', 'Internal Medicine', 'Pathology & Diagnostics']
      };
      TraceStore.setUser(matched);
    }
    if (matched) {
      setUser(matched);
      TraceStore.setUser(matched);
      if (role === 'Admin') {
        setCurrentTab('admin');
      } else {
        setCurrentTab('dashboard');
      }
    }
  };

  const handleSnapshotRestored = () => {
    setUnits(TraceStore.getUnits());
    setUser(TraceStore.getUser());
  };

  const activeUnit = units.find((u) => u.id === activeUnitId) || units[0];

  const adminUser: User = {
    id: '4',
    username: 'Admin Root',
    email: 'admin@trace.edu',
    role: 'Admin',
    difficulty: 'Superuser',
    semesterStatus: 'System Administration & Oversight',
    aiPersona: 'System Architect & Lead Consultant',
    sensoryMode: 'Standard',
    activeUnits: ['Biochemistry II', 'General Surgery', 'Internal Medicine', 'Pathology & Diagnostics']
  };

  // Main screen routing element
  const renderMainScreen = () => {
    if (currentTab === 'admin' || user.role === 'Admin') {
      return (
        <AdminDashboard
          currentUser={user.role === 'Admin' ? user : adminUser}
          onNavigateToTab={(t) => setCurrentTab(t as any)}
          onRefreshData={() => setUnits(TraceStore.getUnits())}
        />
      );
    }

    if (user.role === 'Teacher') {
      return <TeacherDashboard user={user} />;
    }

    if (user.role === 'Parent') {
      return <ParentDashboard user={user} />;
    }

    // Student Role
    return (
      <>
        {currentTab === 'dashboard' && (
          <StudentDashboard
            user={user}
            units={units}
            timetable={timetable}
            onOpenUnit={(unitId) => {
              setActiveUnitId(unitId);
              setCurrentTab('unit-outline');
            }}
            onOpenConsultation={() => setCurrentTab('consultations')}
            onOpenQuizzes={() => setCurrentTab('quizzes')}
            onOpenTimetable={() => setCurrentTab('timetable')}
            onOpenLibrary={() => setCurrentTab('library')}
          />
        )}

        {currentTab === 'learn' && activeUnit && (
          <LearnScreen
            unit={activeUnit}
            subtopicId={activeSubtopicId}
            onBack={() => setCurrentTab('dashboard')}
            onLaunchQuiz={(uName, tName) => handleLaunchQuiz(uName, tName)}
            onOpenBrowser={(url) => setBrowserUrl(url ?? null)}
          />
        )}

        {currentTab === 'quizzes' && (
          <QuizInterface
            units={units}
            initialUnitName={quizUnitName}
            initialTopicName={quizTopicName}
            onBack={() => setCurrentTab('dashboard')}
          />
        )}

        {currentTab === 'consultations' && (
          <ChatInterface user={user} onOpenBrowser={(url) => setBrowserUrl(url ?? null)} />
        )}

        {currentTab === 'timetable' && (
          <TimetableTab
            user={user}
            onOpenUnitByName={(name) => {
              const found = units.find((u) => u.unitName.toLowerCase() === name.toLowerCase());
              if (found) handleSelectUnitToLearn(found.id);
            }}
            onOpenQuizzes={() => setCurrentTab('quizzes')}
          />
        )}

        {currentTab === 'library' && (
          <LibraryScreen
            units={units}
            onToggleEnroll={handleToggleActiveUnit}
            onSelectUnit={(unitId) => {
              setActiveUnitId(unitId);
              setCurrentTab('unit-outline');
            }}
            onBack={() => setCurrentTab('dashboard')}
          />
        )}

        {currentTab === 'unit-outline' && activeUnit && (
          <UnitOutlineScreen
            unit={activeUnit}
            onBack={() => setCurrentTab('dashboard')}
            onOpenSubtopic={(uId, sId) => handleSelectUnitToLearn(uId, sId)}
            onLaunchQuiz={(uName, tName) => handleLaunchQuiz(uName, tName)}
          />
        )}

        {currentTab === 'repository' && (
          <LearningRepositoryScreen
            onBack={() => setCurrentTab('dashboard')}
            onOpenSubtopicByName={(subName) => {
              for (const u of units) {
                for (const m of u.modules) {
                  for (const t of m.topics) {
                    for (const s of t.subtopics) {
                      if (s.name.toLowerCase() === subName.toLowerCase()) {
                        handleSelectUnitToLearn(u.id, s.id);
                        return;
                      }
                    }
                  }
                }
              }
              setCurrentTab('dashboard');
            }}
          />
        )}

        {currentTab === 'bookmarks' && (
          <BookmarksScreen
            onNavigateToLearn={(subtopicId) => {
              const foundUnit = units.find((u) =>
                u.modules.some((m) =>
                  m.topics.some((t) =>
                    t.subtopics.some((s) => s.id === subtopicId)
                  )
                )
              );
              if (foundUnit) {
                handleSelectUnitToLearn(foundUnit.id, subtopicId);
              }
            }}
            onOpenBrowser={(url) => setBrowserUrl(url)}
            onSelectTab={(tab) => setCurrentTab(tab)}
          />
        )}

        {currentTab === 'connect' && <ConnectTab user={user} />}
      </>
    );
  };

  // App Content (Navigation, Header, Screen Content, Bottom Nav)
  const appContent = (
    <div className="flex flex-col h-full text-slate-100 bg-slate-950 font-sans selection:bg-indigo-500/30 selection:text-indigo-200">
      <DynamicBackground />

      {/* Navigation Drawer */}
      <NavigationDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        user={user}
        onSelectTab={(tab) => setCurrentTab(tab)}
        onOpenAccount={() => setIsAccountOpen(true)}
        onOpenArchives={() => setIsArchivesOpen(true)}
        onOpenManageUnits={() => setIsManageUnitsOpen(true)}
        onOpenSync={() => setIsSyncOpen(true)}
        onOpenBrowser={(url) => setBrowserUrl(url || 'https://en.wikipedia.org/wiki/Medicine')}
        onChangeRole={handleChangeRole}
        onLogout={() => setIsLoggedIn(false)}
        onOpenAdminConsole={() => {
          handleChangeRole('Admin');
          setCurrentTab('admin');
        }}
      />

      {/* App Top Bar */}
      <header className="sticky top-0 z-40 bg-slate-950/90 backdrop-blur-xl border-b border-slate-800/80 px-4 h-14 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setIsDrawerOpen(true)}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
            title="Navigation Menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div
            onClick={() => {
              if (user.role === 'Admin') {
                setCurrentTab('admin');
              } else {
                setCurrentTab('dashboard');
              }
            }}
            className="flex items-center gap-2 cursor-pointer select-none"
          >
            <div className="w-7 h-7 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400 font-black text-xs shadow-sm">
              T
            </div>
            <span className="text-sm font-bold text-white tracking-tight">Trace</span>
            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              {user.role}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          {/* Direct Admin Console Switcher */}
          <button
            onClick={() => {
              if (currentTab === 'admin' || user.role === 'Admin') {
                handleChangeRole('Student');
                setCurrentTab('dashboard');
              } else {
                handleChangeRole('Admin');
                setCurrentTab('admin');
              }
            }}
            className={`px-2 py-1 rounded-lg border text-xs font-bold transition-all flex items-center gap-1.5 ${
              currentTab === 'admin' || user.role === 'Admin'
                ? 'bg-red-500/20 text-red-300 border-red-500/40'
                : 'bg-slate-900 text-slate-400 hover:text-red-300 border-slate-800'
            }`}
            title="Toggle Admin Superuser Console"
          >
            <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
            <span className="hidden sm:inline">Admin</span>
          </button>

          {/* Trace Coin Balance Display */}
          <button
            onClick={() => setIsAccountOpen(true)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-gradient-to-r from-amber-500/10 via-amber-500/20 to-amber-600/10 border border-amber-500/30 text-amber-300 font-extrabold text-xs shadow-sm hover:border-amber-400/60 hover:bg-amber-500/20 transition-all select-none cursor-pointer"
            title={`Trace Coin Balance: ${user.traceCoins ?? 200} T Coins. Tap to view profile.`}
          >
            <Coins className="w-3.5 h-3.5 text-amber-400 drop-shadow" />
            <span className="font-mono tracking-tight font-black">{user.traceCoins ?? 200}</span>
            <span className="text-[10px] text-amber-400/80 font-bold">T</span>
          </button>

          <button
            onClick={() => setIsAccountOpen(true)}
            className="w-7 h-7 rounded-lg bg-indigo-600/30 border border-indigo-500/40 text-indigo-200 flex items-center justify-center font-bold text-xs"
            title={user.username}
          >
            {user.username.charAt(0)}
          </button>
        </div>
      </header>

      {/* Main Scrollable View Area */}
      <main className="flex-1 overflow-y-auto px-3.5 py-4 pb-20">
        {renderMainScreen()}
      </main>

      {/* Android Mobile Navigation Bar */}
      <nav className="fixed bottom-0 inset-x-0 z-40 bg-slate-950/95 backdrop-blur-xl border-t border-slate-800/90 py-1.5 px-3 flex items-center justify-around shadow-2xl">
        <button
          onClick={() => setCurrentTab('dashboard')}
          className={`flex flex-col items-center gap-0.5 px-2 py-1 rounded-xl transition-all ${
            currentTab === 'dashboard'
              ? 'text-indigo-400 font-bold'
              : 'text-slate-400 hover:text-slate-200 font-medium'
          }`}
        >
          <Home className="w-4 h-4" />
          <span className="text-[10px]">Home</span>
        </button>

        <button
          onClick={() => setCurrentTab('learn')}
          className={`flex flex-col items-center gap-0.5 px-2 py-1 rounded-xl transition-all ${
            currentTab === 'learn'
              ? 'text-indigo-400 font-bold'
              : 'text-slate-400 hover:text-slate-200 font-medium'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          <span className="text-[10px]">Learn</span>
        </button>

        <button
          onClick={() => setCurrentTab('quizzes')}
          className={`flex flex-col items-center gap-0.5 px-2 py-1 rounded-xl transition-all ${
            currentTab === 'quizzes'
              ? 'text-indigo-400 font-bold'
              : 'text-slate-400 hover:text-slate-200 font-medium'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span className="text-[10px]">Quizzes</span>
        </button>

        <button
          onClick={() => setCurrentTab('consultations')}
          className={`flex flex-col items-center gap-0.5 px-2 py-1 rounded-xl transition-all ${
            currentTab === 'consultations'
              ? 'text-indigo-400 font-bold'
              : 'text-slate-400 hover:text-slate-200 font-medium'
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          <span className="text-[10px]">Consult</span>
        </button>

        <button
          onClick={() => setCurrentTab('timetable')}
          className={`flex flex-col items-center gap-0.5 px-2 py-1 rounded-xl transition-all ${
            currentTab === 'timetable'
              ? 'text-indigo-400 font-bold'
              : 'text-slate-400 hover:text-slate-200 font-medium'
          }`}
        >
          <Calendar className="w-4 h-4" />
          <span className="text-[10px]">Schedule</span>
        </button>

        <button
          onClick={() => {
            handleChangeRole('Admin');
            setCurrentTab('admin');
          }}
          className={`flex flex-col items-center gap-0.5 px-2 py-1 rounded-xl transition-all ${
            currentTab === 'admin' || user.role === 'Admin'
              ? 'text-red-400 font-bold'
              : 'text-slate-400 hover:text-red-300 font-medium'
          }`}
        >
          <ShieldAlert className="w-4 h-4 text-red-400" />
          <span className="text-[10px]">Admin</span>
        </button>
      </nav>

      {/* Modals */}
      {browserUrl && <InAppBrowser url={browserUrl} onClose={() => setBrowserUrl(null)} />}
      {isAccountOpen && (
        <SettingsModal
          user={user}
          units={units}
          initialTab="account"
          onClose={() => setIsAccountOpen(false)}
          onSaveUser={(updated) => {
            setUser(updated);
            TraceStore.setUser(updated);
          }}
          onDeleteUnit={handleDeleteUnit}
          onToggleActiveUnit={handleToggleActiveUnit}
          onSnapshotRestored={handleSnapshotRestored}
        />
      )}
      {isArchivesOpen && (
        <ArchivesModal
          units={units}
          quizHistory={TraceStore.getQuizHistory(user.id)}
          onClose={() => setIsArchivesOpen(false)}
          onRestoreUnit={handleRestoreArchivedUnit}
        />
      )}
      {isManageUnitsOpen && (
        <ManageUnitsModal
          units={units}
          onClose={() => setIsManageUnitsOpen(false)}
          onToggleActive={handleToggleActiveUnit}
          onDeleteUnit={handleDeleteUnit}
        />
      )}
      {isSyncOpen && (
        <SettingsModal
          user={user}
          units={units}
          initialTab="appearance"
          onClose={() => setIsSyncOpen(false)}
          onSaveUser={(updated) => {
            setUser(updated);
            TraceStore.setUser(updated);
          }}
          onDeleteUnit={handleDeleteUnit}
          onToggleActiveUnit={handleToggleActiveUnit}
          onSnapshotRestored={handleSnapshotRestored}
        />
      )}
    </div>
  );

  if (!isLoggedIn) {
    return (
      <div className="relative min-h-screen text-slate-100 bg-slate-950 font-sans">
        <DynamicBackground />
        <LoginScreen
          onLoginSuccess={(u) => {
            setUser(u);
            TraceStore.setUser(u);
            setIsLoggedIn(true);
            setCurrentTab('dashboard');
          }}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500/30 selection:text-indigo-200">
      {appContent}
    </div>
  );
};
