
import React from 'react';
import {
  Member,
  DebateSession,
  FinancialTransaction,
  AgendaItem,
  Announcement,
} from '../../types';
import {
  Users,
  Wallet,
  Calendar,
  Award,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  TrendingUp,
  Download,
  AlertCircle,
  Plus,
  ShieldCheck,
  Radio,
} from 'lucide-react';

interface ExecutiveDashboardProps {
  members: Member[];
  debates: DebateSession[];
  transactions: FinancialTransaction[];
  agendas: AgendaItem[];
  announcements: Announcement[];
  onNavigate: (tab: string) => void;
  onExportData: () => void;
}

export const ExecutiveDashboard: React.FC<ExecutiveDashboardProps> = ({
  members,
  debates,
  transactions,
  agendas,
  announcements,
  onNavigate,
  onExportData,
}) => {
  // Calculations
  const totalMembers = members.length;
  const paidMembersCount = members.filter((m) => m.membershipStatus === 'Paid').length;
  const pendingMembersCount = members.filter((m) => m.membershipStatus === 'Pending').length;
  
  const totalIncome = transactions
    .filter((t) => t.type === 'Income' && t.status === 'Verified')
    .reduce((sum, t) => sum + t.amountKes, 0);

  const totalExpense = transactions
    .filter((t) => t.type === 'Expense' && t.status === 'Verified')
    .reduce((sum, t) => sum + t.amountKes, 0);

  const netTreasury = totalIncome - totalExpense;

  const avgAttendance = Math.round(
    members.reduce((sum, m) => sum + m.attendanceRate, 0) / (members.length || 1)
  );

  const activeDebate = debates.find((d) => d.status === 'Live Now');
  const upcomingAgendas = agendas.filter((a) => a.status === 'Upcoming');

  return (
    <div className="space-y-6">

      {/* Header & Quick Handover Backup Export */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Executive Command Center</span>
            <span className="px-2 py-0.5 text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded">
              Academic Year 2026/2027
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Great Lakes University of Kisumu Debate Club · Executive Oversight & Intelligence
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={onExportData}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-900 border border-slate-800 hover:bg-slate-800 hover:text-white transition-colors"
            title="Download full JSON snapshot for committee handover"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Handover Data</span>
          </button>

          <button
            onClick={() => onNavigate('agendas')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-950 bg-amber-400 hover:bg-amber-300 transition-colors shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Agenda</span>
          </button>
        </div>
      </div>

      {/* 4 Core Quantitative Metrics (Strict Tabular Figures & Units) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Metric 1: Club Membership */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Registered Members</span>
            <Users className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-2xl font-bold text-white tabular-nums">
              {totalMembers}
            </span>
            <span className="text-[11px] text-emerald-400 font-medium">
              {paidMembersCount} Dues Cleared
            </span>
          </div>
          <div className="mt-2 text-[11px] text-slate-500 flex items-center gap-1">
            <span>{pendingMembersCount} awaiting M-Pesa approval</span>
          </div>
        </div>

        {/* Metric 2: Net Treasury Balance (KES) */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Net Treasury Reserve</span>
            <Wallet className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-1">
            <span className="font-mono text-xs font-bold text-amber-400">KES</span>
            <span className="font-mono text-2xl font-bold text-white tabular-nums">
              {netTreasury.toLocaleString()}
            </span>
          </div>
          <div className="mt-2 text-[11px] text-slate-500 flex items-center justify-between">
            <span>In: KES {totalIncome.toLocaleString()}</span>
            <span>Out: KES {totalExpense.toLocaleString()}</span>
          </div>
        </div>

        {/* Metric 3: Average Attendance Rate */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Average Session Attendance</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-2xl font-bold text-white tabular-nums">
              {avgAttendance}%
            </span>
            <span className="text-[11px] text-emerald-400 font-medium">
              High Engagement
            </span>
          </div>
          <div className="mt-2 text-[11px] text-slate-500">
            Across 25 weekly training & competitive rounds
          </div>
        </div>

        {/* Metric 4: Debates Tracked & Tournament Status */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Debate Rounds Tracked</span>
            <Award className="w-4 h-4 text-purple-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-2xl font-bold text-white tabular-nums">
              {debates.length}
            </span>
            <span className="text-[11px] text-purple-400 font-medium">
              KUDC Prep: Round 14
            </span>
          </div>
          <div className="mt-2 text-[11px] text-slate-500">
            BP & AP formats · Western Circuit
          </div>
        </div>

      </div>

      {/* Live Now Alert Banner (if debate is active) */}
      {activeDebate && (
        <div className="rounded-xl border border-amber-500/30 bg-gradient-to-r from-amber-500/10 via-slate-900 to-slate-900 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400 shrink-0 mt-0.5">
              <Radio className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold text-amber-400 uppercase tracking-wider">
                  Live Debate in Progress
                </span>
                <span className="text-slate-600">·</span>
                <span className="text-xs text-slate-400">{activeDebate.format}</span>
              </div>
              <h3 className="text-sm font-semibold text-white mt-0.5">
                {activeDebate.title}
              </h3>
              <p className="text-xs text-slate-300 italic mt-0.5">
                "{activeDebate.motion}"
              </p>
            </div>
          </div>

          <button
            onClick={() => onNavigate('live-debate')}
            className="inline-flex items-center gap-2 px-4 py-2 bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold text-xs rounded-lg transition-colors whitespace-nowrap shrink-0 shadow-md"
          >
            <span>Open Companion Suite</span>
            <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Grid: Executive Action Queue & Recent Debates */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Executive Action Queue & Role Delegation (7 cols) */}
        <div className="lg:col-span-7 rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Executive Action Delegation & Deadlines
              </h3>
              <p className="text-xs text-slate-400">
                Action items assigned across Executive Committee positions
              </p>
            </div>
            <button
              onClick={() => onNavigate('agendas')}
              className="text-xs text-amber-400 hover:text-amber-300 font-medium"
            >
              View All Agendas →
            </button>
          </div>

          {upcomingAgendas.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500">
              No pending executive tasks. All delegations up to date.
            </div>
          ) : (
            <div className="space-y-3">
              {upcomingAgendas.flatMap((a) => a.agendaItems).slice(0, 4).map((item) => (
                <div
                  key={item.id}
                  className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-start justify-between gap-3 text-xs"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          item.isCompleted ? 'bg-emerald-400' : 'bg-amber-400'
                        }`}
                      />
                      <span className="font-semibold text-slate-200">
                        {item.title}
                      </span>
                    </div>
                    {item.notes && (
                      <p className="text-[11px] text-slate-400 pl-3.5">
                        {item.notes}
                      </p>
                    )}
                    <div className="flex items-center gap-3 pl-3.5 text-[10px] text-slate-500 font-mono">
                      <span>Assigned: {item.assignedTo}</span>
                      <span>·</span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-400" />
                        Due: {item.deadline}
                      </span>
                    </div>
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-semibold shrink-0 ${
                      item.isCompleted
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                    }`}
                  >
                    {item.isCompleted ? 'Done' : 'In Progress'}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Quick Logistics Status Check */}
          <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
            <span className="text-slate-400">Chamber Logistics readiness:</span>
            <span className="font-medium text-emerald-400 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              Bells, Stopwatches & Ballots Prepped
            </span>
          </div>
        </div>

        {/* Financial Flow & Quick Health (5 cols) */}
        <div className="lg:col-span-5 rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Treasury Flow & Dues Compliance
              </h3>
              <p className="text-xs text-slate-400">
                Semester 1 membership fees (KES 500/member)
              </p>
            </div>
            <button
              onClick={() => onNavigate('finances')}
              className="text-xs text-amber-400 hover:text-amber-300 font-medium"
            >
              Ledger →
            </button>
          </div>

          {/* Progress bar of dues collected */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">Dues Collected vs. Semester Target</span>
              <span className="font-mono text-slate-200 font-semibold">
                {Math.round((paidMembersCount / (totalMembers || 1)) * 100)}%
              </span>
            </div>
            <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
              <div
                className="bg-amber-400 h-full rounded-full transition-all"
                style={{
                  width: `${Math.min(100, (paidMembersCount / (totalMembers || 1)) * 100)}%`,
                }}
              />
            </div>
            <div className="flex justify-between text-[11px] text-slate-500 font-mono">
              <span>{paidMembersCount} Paid</span>
              <span>{totalMembers - paidMembersCount} Pending / Unpaid</span>
            </div>
          </div>

          {/* Recent Verified Transactions */}
          <div className="space-y-2 mt-4">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Recent Transactions
            </div>
            {transactions.slice(0, 3).map((t) => (
              <div
                key={t.id}
                className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs"
              >
                <div className="truncate pr-2">
                  <div className="font-medium text-slate-200 truncate">{t.description}</div>
                  <div className="text-[10px] text-slate-500 font-mono">
                    Ref: {t.referenceCode} · {t.date}
                  </div>
                </div>
                <div
                  className={`font-mono font-bold whitespace-nowrap tabular-nums ${
                    t.type === 'Income' ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {t.type === 'Income' ? '+' : '-'} KES {t.amountKes.toLocaleString()}
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2">
            <button
              onClick={() => onNavigate('finances')}
              className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 transition-colors"
            >
              + Record Treasury Transaction / Receipt
            </button>
          </div>
        </div>

      </div>

    </div>
  );
};


