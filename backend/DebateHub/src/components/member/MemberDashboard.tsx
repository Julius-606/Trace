
import React, { useState } from 'react';
import {
  Member,
  DebateSession,
  Announcement,
  CalendarEvent,
  AlumniMentorshipNote,
} from '../../types';
import { GlukDebateLogo } from '../common/GlukDebateLogo';
import {
  Award,
  Calendar,
  CheckCircle,
  Clock,
  ExternalLink,
  GraduationCap,
  Pin,
  QrCode,
  Radio,
  Send,
  Sparkles,
  TrendingUp,
  User,
  Zap,
  ArrowRight,
  ShieldCheck,
  BookOpen,
} from 'lucide-react';

interface MemberDashboardProps {
  currentUser: Member;
  announcements: Announcement[];
  upcomingEvents: CalendarEvent[];
  activeDebateSession?: DebateSession;
  mentorshipNotes: AlumniMentorshipNote[];
  onNavigate: (tab: string) => void;
  onSubmitDuesMpesa: (code: string) => void;
  onOpenPassModal: () => void;
}

export const MemberDashboard: React.FC<MemberDashboardProps> = ({
  currentUser,
  announcements,
  upcomingEvents,
  activeDebateSession,
  mentorshipNotes,
  onNavigate,
  onSubmitDuesMpesa,
  onOpenPassModal,
}) => {
  const [mpesaCodeInput, setMpesaCodeInput] = useState('');
  const [mpesaSubmitted, setMpesaSubmitted] = useState(false);

  const handleMpesaSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!mpesaCodeInput) return;
    onSubmitDuesMpesa(mpesaCodeInput.toUpperCase().trim());
    setMpesaSubmitted(true);
    setMpesaCodeInput('');
    setTimeout(() => setMpesaSubmitted(false), 4000);
  };

  const nextEvent = upcomingEvents[0];
  const myMentorship = mentorshipNotes.find((n) => n.menteeId === currentUser.id);
  const pinnedAnnouncements = announcements.filter((a) => a.pinned);

  return (
    <div className="space-y-6">

      {/* Member Welcome Banner */}
      <div className="rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 p-6 shadow-xl relative overflow-hidden">
        {/* Subtle accent glow */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-blue-500/15 text-blue-300 border border-blue-500/30 rounded">
                Member Portal
              </span>
              <span className="text-slate-600">·</span>
              <span className="text-xs text-slate-400 font-mono">
                {currentUser.studentId}
              </span>
            </div>

            <h1 className="text-2xl font-extrabold text-white tracking-tight">
              Welcome back, {currentUser.fullName}
            </h1>

            <p className="text-xs text-slate-300">
              {currentUser.faculty} · <span className="text-amber-400 font-medium">{currentUser.yearOfStudy}</span> · Great Lakes University of Kisumu Debate Club
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={onOpenPassModal}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-all shadow-md"
            >
              <QrCode className="w-4 h-4 text-amber-400" />
              <span>Digital Member Pass</span>
            </button>

            {activeDebateSession && (
              <button
                onClick={() => onNavigate('live-debate')}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold text-slate-950 bg-amber-400 hover:bg-amber-300 transition-all shadow-md shadow-amber-500/10"
              >
                <Radio className="w-4 h-4 text-slate-950 animate-pulse" />
                <span>Join Live Meet Companion</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 4 Personal Standing Metric Cards (Strictly Member's Own Data) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Metric 1: My Attendance */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>My Attendance Standing</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-3xl font-bold text-white tabular-nums">
              {currentUser.attendanceRate}%
            </span>
            <span className="text-[11px] text-emerald-400 font-medium">
              {currentUser.attendanceRate >= 75 ? 'Tournament Eligible' : 'Requires Catchup'}
            </span>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                currentUser.attendanceRate >= 75 ? 'bg-emerald-400' : 'bg-amber-400'
              }`}
              style={{ width: `${currentUser.attendanceRate}%` }}
            />
          </div>
          <div className="text-[10px] text-slate-500 font-mono">
            {currentUser.debatesAttendedCount} attended of {currentUser.totalDebatesCount} total club rounds
          </div>
        </div>

        {/* Metric 2: Semester Dues Clearance */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Semester 1 Dues (KES 500)</span>
            <ShieldCheck className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span
              className={`text-2xl font-bold uppercase tracking-tight ${
                currentUser.membershipStatus === 'Paid'
                  ? 'text-emerald-400'
                  : 'text-amber-400'
              }`}
            >
              {currentUser.membershipStatus}
            </span>
            {currentUser.membershipStatus === 'Paid' && (
              <span className="text-[11px] text-emerald-400">Verified</span>
            )}
          </div>
          <p className="text-[11px] text-slate-400">
            {currentUser.membershipStatus === 'Paid'
              ? `Ref: ${currentUser.mpesaRef}`
              : 'Submit M-Pesa receipt code below'}
          </p>
        </div>

        {/* Metric 3: Speaker Rating Average */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Average Speaker Points</span>
            <Award className="w-4 h-4 text-purple-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-3xl font-bold text-white tabular-nums">
              {currentUser.speakerPointsAvg}
            </span>
            <span className="text-[11px] text-purple-400 font-mono">
              / 100 PAUDC
            </span>
          </div>
          <p className="text-[11px] text-slate-400">
            Cumulative ballot average across competitive rounds
          </p>
        </div>

        {/* Metric 4: Debater Portfolio Tier */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Debate Track & Tier</span>
            <GraduationCap className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-xl font-bold text-white">
            {currentUser.yearOfStudy === 'Year 1'
              ? 'Novice Debater'
              : currentUser.yearOfStudy === 'Year 2'
              ? 'Junior Speaker'
              : 'Senior Debater'}
          </div>
          <p className="text-[11px] text-slate-400">
            Track: British Parliamentary (BP) & Public Speaking
          </p>
        </div>

      </div>

      {/* Main Grid: Upcoming Schedule & Dues / Mentorship Action */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Left Column: Next Session & Announcements (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          
          {/* Next Scheduled Activity Spotlight */}
          {nextEvent && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400">
                  Next Scheduled Club Activity
                </span>
                <span className="text-xs font-mono text-slate-400">
                  {nextEvent.date} · {nextEvent.startTime} EAT
                </span>
              </div>

              <h3 className="text-base font-bold text-white leading-snug">
                {nextEvent.title}
              </h3>

              <p className="text-xs text-slate-300 leading-relaxed">
                {nextEvent.description}
              </p>

              <div className="pt-2 flex flex-wrap items-center justify-between gap-3 text-xs border-t border-slate-800">
                <span className="text-slate-400">
                  Location: <strong className="text-slate-200">{nextEvent.location}</strong>
                </span>

                <div className="flex items-center gap-2">
                  {nextEvent.googleMeetUrl && (
                    <a
                      href={nextEvent.googleMeetUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>Meet Link</span>
                    </a>
                  )}
                  <button
                    onClick={() => onNavigate('calendar')}
                    className="text-xs text-amber-400 hover:text-amber-300 font-medium"
                  >
                    View Full Calendar →
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Official Announcements Feed Snippet */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                <Pin className="w-3.5 h-3.5 text-amber-400" />
                <span>Executive Notices for Members</span>
              </h3>
              <button
                onClick={() => onNavigate('announcements')}
                className="text-xs text-amber-400 hover:text-amber-300 font-medium"
              >
                All Notices ({announcements.length}) →
              </button>
            </div>

            <div className="space-y-3">
              {pinnedAnnouncements.slice(0, 2).map((ann) => (
                <div
                  key={ann.id}
                  className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800/80 space-y-1.5 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white text-sm">
                      {ann.title}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">
                      {ann.publishDate}
                    </span>
                  </div>
                  <p className="text-slate-300 leading-relaxed font-sans">
                    {ann.content}
                  </p>
                  <div className="text-[10px] text-slate-500 pt-1">
                    Issued by: {ann.author} ({ann.authorRole})
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Practice & Rebuttal Drills Shortcut */}
          <div className="p-4 rounded-xl border border-amber-500/20 bg-amber-500/5 flex items-center justify-between gap-4">
            <div className="space-y-1">
              <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                <span>60-Second POI & Rebuttal Training</span>
              </h4>
              <p className="text-xs text-slate-300">
                Practice spontaneous opposition refutations under official debate timing.
              </p>
            </div>
            <button
              onClick={() => onNavigate('drills')}
              className="px-3.5 py-1.5 bg-amber-400 hover:bg-amber-300 text-slate-950 text-xs font-bold rounded-lg transition-colors whitespace-nowrap"
            >
              Start Drill
            </button>
          </div>

        </div>

        {/* Right Column: Dues Submission & Alumni Mentorship (5 cols) */}
        <div className="lg:col-span-5 space-y-5">
          
          {/* Semester Dues Clearance Form */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3.5">
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              Semester Dues Clearance
            </h3>

            {currentUser.membershipStatus === 'Paid' ? (
              <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/30 text-xs space-y-2">
                <div className="flex items-center gap-2 text-emerald-300 font-bold">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <span>Dues Cleared (KES 500)</span>
                </div>
                <p className="text-slate-300 text-[11px] leading-relaxed">
                  Your semester registration is in good standing. You hold active voting rights and national tournament travel eligibility.
                </p>
                <div className="font-mono text-[10px] text-emerald-400 pt-1">
                  M-Pesa Verification: {currentUser.mpesaRef}
                </div>
              </div>
            ) : (
              <div className="space-y-3 text-xs">
                <p className="text-slate-300 leading-normal">
                  Pay your KES 500 semester dues to the club treasury via M-Pesa, then submit the confirmation code below for executive sign-off:
                </p>

                <form onSubmit={handleMpesaSubmit} className="space-y-2">
                  <div>
                    <label className="text-[10px] text-slate-400 block mb-1 uppercase font-semibold">
                      M-Pesa Transaction Code
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. QRT892ZZ19"
                      value={mpesaCodeInput}
                      onChange={(e) => setMpesaCodeInput(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-amber-300 font-mono text-xs uppercase"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={!mpesaCodeInput}
                    className="w-full py-2 bg-amber-400 hover:bg-amber-300 disabled:opacity-40 text-slate-950 font-bold rounded-lg text-xs transition-colors flex items-center justify-center gap-1.5"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Submit for Verification</span>
                  </button>

                  {mpesaSubmitted && (
                    <p className="text-[11px] text-emerald-400 text-center font-medium pt-1">
                      ✓ Submitted! The Treasury Secretary has been notified.
                    </p>
                  )}
                </form>
              </div>
            )}
          </div>

          {/* Mentorship Connection */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5 text-purple-400" />
                <span>Alumni Mentorship Advisory</span>
              </h3>
              <button
                onClick={() => onNavigate('members')}
                className="text-xs text-amber-400 hover:text-amber-300 font-medium"
              >
                Find Mentor →
              </button>
            </div>

            {myMentorship ? (
              <div className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800 space-y-2 text-xs">
                <span className="font-semibold text-purple-300 block">
                  {myMentorship.topic}
                </span>
                <p className="text-slate-300 italic text-[11px] leading-relaxed">
                  "{myMentorship.adviceSummary}"
                </p>
                <div className="text-[10px] text-slate-400 pt-1 border-t border-slate-800/80">
                  Mentor: <strong className="text-white">{myMentorship.alumniName}</strong>
                </div>
              </div>
            ) : (
              <div className="text-center py-4 space-y-2 text-xs">
                <p className="text-slate-400">
                  Connect with GLUK alumni practicing in law, health policy, and commerce for 1-on-1 rebuttal coaching.
                </p>
                <button
                  onClick={() => onNavigate('members')}
                  className="px-3 py-1.5 bg-purple-500/20 hover:bg-purple-500/30 text-purple-200 border border-purple-500/30 rounded-lg text-xs font-semibold"
                >
                  Browse Alumni Mentors
                </button>
              </div>
            )}
          </div>

        </div>

      </div>

    </div>
  );
};


