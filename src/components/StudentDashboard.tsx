import React, { useState } from 'react';
import {
  Sparkles,
  RefreshCw,
  BookOpen,
  ArrowRight,
  Calendar,
  Award,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  BrainCircuit,
  MessageSquare
} from 'lucide-react';
import { User, Unit, TimetableSlot } from '../types';
import { ProgressRings } from './ProgressRings';
import { TraceStore } from '../lib/store';

interface StudentDashboardProps {
  user: User;
  units: Unit[];
  timetable: TimetableSlot[];
  onOpenUnit: (unitId: number) => void;
  onOpenConsultation: () => void;
  onOpenQuizzes: () => void;
  onOpenTimetable: () => void;
  onOpenLibrary: () => void;
}

export const StudentDashboard: React.FC<StudentDashboardProps> = ({
  user,
  units,
  timetable,
  onOpenUnit,
  onOpenConsultation,
  onOpenQuizzes,
  onOpenTimetable,
  onOpenLibrary
}) => {
  const [zenithInsight, setZenithInsight] = useState<string>(TraceStore.getZenithInsight());
  const [refreshingInsight, setRefreshingInsight] = useState(false);
  const [isUnitsExpanded, setIsUnitsExpanded] = useState<boolean>(false);

  // Active units
  const activeUnits = units.filter((u) => u.isActive);

  // Calculate hierarchical progress
  const allSubtopics = units.flatMap((u) => u.modules.flatMap((m) => m.topics.flatMap((t) => t.subtopics)));
  const completedSubtopics = allSubtopics.filter((s) => s.isCompleted);
  const totalSubtopics = allSubtopics.length || 1;

  const unitProgress = Math.round((completedSubtopics.length / totalSubtopics) * 100);

  // Module progress: proportion of modules with at least 1 completed subtopic
  const allModules = units.flatMap((u) => u.modules);
  const modulesWithCompletion = allModules.filter((m) =>
    m.topics.some((t) => t.subtopics.some((s) => s.isCompleted))
  );
  const moduleProgress = Math.round((modulesWithCompletion.length / (allModules.length || 1)) * 100);

  // Topic progress
  const allTopics = allModules.flatMap((m) => m.topics);
  const topicsWithCompletion = allTopics.filter((t) => t.subtopics.some((s) => s.isCompleted));
  const topicProgress = Math.round((topicsWithCompletion.length / (allTopics.length || 1)) * 100);

  // Recent assessment PnL
  const quizHistory = TraceStore.getQuizHistory(user.id);
  const avgPnl = quizHistory.length > 0
    ? Math.round(quizHistory.reduce((acc, cur) => acc + cur.pnlScore, 0) / quizHistory.length)
    : 85;

  // Upcoming slot
  const nextSlot = timetable[0];

  const handleRefreshInsight = async () => {
    setRefreshingInsight(true);
    try {
      const res = await fetch('/api/zenith/insight', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: user.username,
          activeUnits: activeUnits.map((u) => u.unitName),
          recentScores: quizHistory.map((q) => q.pnlScore)
        })
      });
      const data = await res.json();
      if (data.insight) {
        setZenithInsight(data.insight);
        TraceStore.setZenithInsight(data.insight);
      }
    } catch {
      // Fallback
      const refreshed = `**Zenith Trajectory Update**: Dynamic review active. You have maintained a **${avgPnl}% accuracy** across clinical modules. Suggested immediate focus: consolidate surgical shock classifications and differential diagnoses before the scheduled retrieval assessment.`;
      setZenithInsight(refreshed);
      TraceStore.setZenithInsight(refreshed);
    } finally {
      setRefreshingInsight(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Welcome Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800/80 rounded-3xl p-6 backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">
              Personalized Learning Matrix
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
            <span className="text-xs text-slate-400 font-medium">{user.semesterStatus}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Welcome back, {user.username}
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-xl">
            Adaptive Socratic guidance, high-yield retrieval assessments, and dynamic clinical scheduling.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-slate-950/80 border border-slate-800 rounded-2xl px-4 py-2.5 text-center min-w-[100px]">
            <span className="text-xs font-semibold text-slate-400 block">Avg PnL</span>
            <span className="text-xl font-extrabold text-emerald-400">{avgPnl}%</span>
          </div>
          <div className="bg-slate-950/80 border border-slate-800 rounded-2xl px-4 py-2.5 text-center min-w-[100px]">
            <span className="text-xs font-semibold text-slate-400 block">Assessments</span>
            <span className="text-xl font-extrabold text-indigo-400">{quizHistory.length}</span>
          </div>
        </div>
      </div>

      {/* Zenith Insights Card */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-950/50 via-slate-900 to-slate-900 border border-indigo-500/30 p-6 shadow-xl shadow-indigo-950/20">
        <div className="flex items-start justify-between gap-4 mb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white tracking-wide uppercase">
                Zenith Insights & Trajectory Advisory
              </h2>
              <p className="text-xs text-indigo-300">Continuous AI curriculum optimization</p>
            </div>
          </div>

          <button
            onClick={handleRefreshInsight}
            disabled={refreshingInsight}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 text-xs font-semibold transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshingInsight ? 'animate-spin' : ''}`} />
            <span>{refreshingInsight ? 'Analyzing...' : 'Refresh'}</span>
          </button>
        </div>

        <div className="text-sm text-slate-200 leading-relaxed pt-1 prose-invert">
          <div dangerouslySetInnerHTML={{ __html: zenithInsight.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>').replace(/\*(.*?)\*/g, '<em class="text-indigo-200">$1</em>') }} />
        </div>
      </div>

      {/* Learning Progress & Concentric Rings */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Concentric Progress Rings Panel */}
        <div className="bg-slate-900/70 border border-slate-800/90 rounded-3xl p-6 flex flex-col sm:flex-row lg:flex-col items-center justify-between gap-6 shadow-lg">
          <div className="w-full">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-1">
              Curriculum Mastery
            </h3>
            <p className="text-xs text-slate-400">Hierarchical completion progress</p>
          </div>

          <div className="py-2">
            <ProgressRings
              unitProgress={unitProgress}
              moduleProgress={moduleProgress}
              topicProgress={topicProgress}
              size={150}
            />
          </div>

          {/* Ring Legend */}
          <div className="w-full space-y-2 text-xs">
            <div className="flex items-center justify-between p-2 rounded-xl bg-slate-950/60 border border-slate-800/60">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
                <span className="text-slate-300 font-medium">Subtopic Mastery</span>
              </div>
              <span className="font-bold text-white">{unitProgress}%</span>
            </div>

            <div className="flex items-center justify-between p-2 rounded-xl bg-slate-950/60 border border-slate-800/60">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <span className="text-slate-300 font-medium">Module Engagement</span>
              </div>
              <span className="font-bold text-white">{moduleProgress}%</span>
            </div>

            <div className="flex items-center justify-between p-2 rounded-xl bg-slate-950/60 border border-slate-800/60">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                <span className="text-slate-300 font-medium">Topic Penetration</span>
              </div>
              <span className="font-bold text-white">{topicProgress}%</span>
            </div>
          </div>
        </div>

        {/* Dynamic Schedule Preview */}
        <div className="lg:col-span-2 bg-slate-900/70 border border-slate-800/90 rounded-3xl p-6 flex flex-col justify-between shadow-lg">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-emerald-600/20 text-emerald-400">
                  <Calendar className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                    Today's Study Trail & Schedule
                  </h3>
                  <p className="text-xs text-slate-400">Optimized spaced retrieval plan</p>
                </div>
              </div>

              <button
                onClick={onOpenTimetable}
                className="text-xs font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
              >
                <span>Full Timetable</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {nextSlot ? (
              <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                      {nextSlot.type}
                    </span>
                    <span className="text-xs text-slate-400">
                      {nextSlot.day} • {nextSlot.startTime} - {nextSlot.endTime}
                    </span>
                  </div>
                  <h4 className="text-base font-bold text-white">{nextSlot.title}</h4>
                  {nextSlot.unitName && (
                    <p className="text-xs text-indigo-400 font-medium mt-0.5">{nextSlot.unitName}</p>
                  )}
                  {nextSlot.notes && (
                    <p className="text-xs text-slate-400 mt-1 italic">{nextSlot.notes}</p>
                  )}
                </div>

                <button
                  onClick={onOpenTimetable}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors shrink-0 flex items-center justify-center gap-1.5"
                >
                  <span>Launch Session</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <p className="text-xs text-slate-500">No scheduled sessions for today.</p>
            )}
          </div>

          {/* Quick Action Matrix */}
          <div className="mt-6 pt-5 border-t border-slate-800/80 grid grid-cols-2 sm:grid-cols-3 gap-3">
            <button
              onClick={onOpenConsultation}
              className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-950 transition-all text-left group"
            >
              <MessageSquare className="w-4 h-4 text-indigo-400 mb-2 group-hover:scale-110 transition-transform" />
              <p className="text-xs font-bold text-white">AI Consultation</p>
              <p className="text-[10px] text-slate-400">Socratic guidance</p>
            </button>

            <button
              onClick={onOpenQuizzes}
              className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800 hover:border-amber-500/50 hover:bg-slate-950 transition-all text-left group"
            >
              <Sparkles className="w-4 h-4 text-amber-400 mb-2 group-hover:scale-110 transition-transform" />
              <p className="text-xs font-bold text-white">Knowledge Retrieval</p>
              <p className="text-[10px] text-slate-400">Clinical quizzes</p>
            </button>

            <button
              onClick={onOpenLibrary}
              className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800 hover:border-emerald-500/50 hover:bg-slate-950 transition-all text-left group col-span-2 sm:col-span-1"
            >
              <BookOpen className="w-4 h-4 text-emerald-400 mb-2 group-hover:scale-110 transition-transform" />
              <p className="text-xs font-bold text-white">Unit Library</p>
              <p className="text-[10px] text-slate-400">Browse & enroll</p>
            </button>
          </div>
        </div>
      </div>

      {/* Enrolled Clinical Units Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div
            onClick={() => setIsUnitsExpanded(!isUnitsExpanded)}
            className="cursor-pointer group flex items-center gap-3 select-none"
          >
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white tracking-tight group-hover:text-indigo-300 transition-colors">
                  Active Curriculum Units ({activeUnits.length})
                </h2>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700/60">
                  {isUnitsExpanded ? 'Expanded' : 'Collapsed'}
                </span>
              </div>
              <p className="text-xs text-slate-400">Enrolled disciplines & study pathways • Click to {isUnitsExpanded ? 'collapse' : 'expand'}</p>
            </div>
            <div className="p-1.5 rounded-xl bg-slate-800/80 text-slate-300 group-hover:bg-slate-700 transition">
              {isUnitsExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsUnitsExpanded(!isUnitsExpanded)}
              className="text-xs font-semibold text-slate-400 hover:text-white px-3 py-1.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 transition flex items-center gap-1.5"
            >
              <span>{isUnitsExpanded ? 'Collapse' : 'Expand'}</span>
              {isUnitsExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
            <button
              onClick={onOpenLibrary}
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
            >
              <span>Explore All</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {isUnitsExpanded ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {activeUnits.map((unit) => {
              const unitSubtopics = unit.modules.flatMap((m) => m.topics.flatMap((t) => t.subtopics));
              const completedCount = unitSubtopics.filter((s) => s.isCompleted).length;
              const progress = Math.round((completedCount / (unitSubtopics.length || 1)) * 100);

              return (
                <div
                  key={unit.id}
                  className="bg-slate-900/80 border border-slate-800 rounded-3xl p-5 flex flex-col justify-between hover:border-slate-700 transition-all shadow-md group"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/60">
                        {unit.category}
                      </span>
                      <span className="text-xs font-extrabold text-indigo-400">{progress}%</span>
                    </div>

                    <h3 className="text-base font-bold text-white group-hover:text-indigo-300 transition-colors">
                      {unit.unitName}
                    </h3>
                    <p className="text-xs text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                      {unit.description}
                    </p>

                    <div className="mt-4 space-y-1.5">
                      <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium">
                        <span>{completedCount} of {unitSubtopics.length} subtopics completed</span>
                      </div>
                      <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className="h-full bg-indigo-500 rounded-full transition-all duration-500"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="mt-5 pt-4 border-t border-slate-800/80 flex items-center justify-between">
                    <span className="text-[11px] text-slate-500">
                      {unit.modules.length} Modules • {unit.modules.flatMap(m => m.topics).length} Topics
                    </span>
                    <button
                      onClick={() => onOpenUnit(unit.id)}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors"
                    >
                      <span>Enter Trail</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div
            onClick={() => setIsUnitsExpanded(true)}
            className="cursor-pointer p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-indigo-500/40 hover:bg-slate-900/90 transition flex items-center justify-between text-xs text-slate-400 select-none group"
          >
            <div className="flex items-center gap-2.5">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 group-hover:scale-125 transition-transform" />
              <span className="text-slate-300 font-medium">
                {activeUnits.length} active curriculum units enrolled. Units collapsed by default.
              </span>
            </div>
            <span className="text-indigo-400 font-bold flex items-center gap-1 group-hover:text-indigo-300 transition-colors">
              <span>Expand Units ({activeUnits.length})</span>
              <ChevronDown className="w-4 h-4" />
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
