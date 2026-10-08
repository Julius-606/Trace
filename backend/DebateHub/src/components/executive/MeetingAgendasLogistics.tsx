
import React, { useState } from 'react';
import { AgendaItem, Member } from '../../types';
import {
  Calendar,
  CheckSquare,
  Square,
  Clock,
  User,
  Plus,
  Package,
  MapPin,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
} from 'lucide-react';

interface MeetingAgendasLogisticsProps {
  agendas: AgendaItem[];
  members: Member[];
  onUpdateAgendas: (agendas: AgendaItem[]) => void;
}

export const MeetingAgendasLogistics: React.FC<MeetingAgendasLogisticsProps> = ({
  agendas,
  members,
  onUpdateAgendas,
}) => {
  const [selectedAgendaId, setSelectedAgendaId] = useState<string>(
    agendas[0]?.id || ''
  );
  const [showAddAgendaModal, setShowAddAgendaModal] = useState(false);
  const [showAddActionModal, setShowAddActionModal] = useState(false);
  const [showAddLogisticsModal, setShowAddLogisticsModal] = useState(false);

  // New action form state
  const [actionTitle, setActionTitle] = useState('');
  const [actionAssignee, setActionAssignee] = useState(members[0]?.fullName || '');
  const [actionDeadline, setActionDeadline] = useState('');
  const [actionNotes, setActionNotes] = useState('');

  // New logistics form state
  const [logisticsItem, setLogisticsItem] = useState('');
  const [logisticsQty, setLogisticsQty] = useState(1);
  const [logisticsAssignee, setLogisticsAssignee] = useState(
    'Kevin Otieno (Logistics Sec)'
  );

  const currentAgenda =
    agendas.find((a) => a.id === selectedAgendaId) || agendas[0];

  const handleToggleTask = (agendaId: string, taskId: string) => {
    const updated = agendas.map((ag) => {
      if (ag.id !== agendaId) return ag;
      return {
        ...ag,
        agendaItems: ag.agendaItems.map((item) =>
          item.id === taskId
            ? { ...item, isCompleted: !item.isCompleted }
            : item
        ),
      };
    });
    onUpdateAgendas(updated);
  };

  const handleToggleLogisticsStatus = (agendaId: string, logId: string) => {
    const updated = agendas.map((ag) => {
      if (ag.id !== agendaId) return ag;
      return {
        ...ag,
        logisticsChecklist: ag.logisticsChecklist.map((log) => {
          if (log.id !== logId) return log;
          const nextStatus: 'Ready' | 'Pending' | 'Not Started' =
            log.status === 'Ready'
              ? 'Pending'
              : log.status === 'Pending'
              ? 'Not Started'
              : 'Ready';
          return { ...log, status: nextStatus };
        }),
      };
    });
    onUpdateAgendas(updated);
  };

  const handleCreateActionItem = (e: React.FormEvent) => {
    e.preventDefault();
    if (!actionTitle || !currentAgenda) return;

    const newItem = {
      id: `task-${Date.now()}`,
      title: actionTitle,
      assignedTo: actionAssignee,
      deadline: actionDeadline || '2026-10-15',
      isCompleted: false,
      notes: actionNotes,
    };

    const updated = agendas.map((ag) => {
      if (ag.id !== currentAgenda.id) return ag;
      return {
        ...ag,
        agendaItems: [...ag.agendaItems, newItem],
      };
    });

    onUpdateAgendas(updated);
    setShowAddActionModal(false);
    setActionTitle('');
    setActionNotes('');
  };

  const handleCreateLogisticsItem = (e: React.FormEvent) => {
    e.preventDefault();
    if (!logisticsItem || !currentAgenda) return;

    const newLog = {
      id: `log-${Date.now()}`,
      item: logisticsItem,
      quantity: logisticsQty,
      status: 'Pending' as const,
      assignedTo: logisticsAssignee,
    };

    const updated = agendas.map((ag) => {
      if (ag.id !== currentAgenda.id) return ag;
      return {
        ...ag,
        logisticsChecklist: [...ag.logisticsChecklist, newLog],
      };
    });

    onUpdateAgendas(updated);
    setShowAddLogisticsModal(false);
    setLogisticsItem('');
  };

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Executive Agendas & Logistics Command</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Role delegation, meeting agendas, deadlines, chamber audio logistics, and tournament checklists.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Agenda selector */}
          <select
            value={selectedAgendaId}
            onChange={(e) => setSelectedAgendaId(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white font-medium"
          >
            {agendas.map((a) => (
              <option key={a.id} value={a.id}>
                {a.date} · {a.meetingTitle.slice(0, 35)}...
              </option>
            ))}
          </select>
        </div>
      </div>

      {currentAgenda && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

          {/* Left Column: Meeting Info & Action Delegations (7 cols) */}
          <div className="lg:col-span-7 space-y-5">
            
            {/* Meeting Meta Header */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[11px] font-bold text-amber-400 uppercase tracking-wider">
                    {currentAgenda.status} Executive Assembly
                  </span>
                  <h2 className="text-base font-bold text-white mt-1">
                    {currentAgenda.meetingTitle}
                  </h2>
                </div>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  Chair: {currentAgenda.chairperson}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs text-slate-400 pt-2 border-t border-slate-800">
                <div className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  <span>{currentAgenda.date} · {currentAgenda.time}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-slate-500" />
                  <span className="truncate">{currentAgenda.location}</span>
                </div>
              </div>
            </div>

            {/* Delegated Action Items List */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div>
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                    Role Delegations & Deadlines ({currentAgenda.agendaItems.length})
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    Assignee execution accountability
                  </p>
                </div>
                <button
                  onClick={() => setShowAddActionModal(true)}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-amber-400/20 hover:bg-amber-400/30 text-amber-300 font-semibold rounded text-xs border border-amber-400/30 transition-colors"
                >
                  <Plus className="w-3 h-3" />
                  <span>Delegate Action</span>
                </button>
              </div>

              <div className="space-y-2.5">
                {currentAgenda.agendaItems.map((item) => (
                  <div
                    key={item.id}
                    className={`p-3 rounded-lg border text-xs transition-all ${
                      item.isCompleted
                        ? 'bg-slate-950/40 border-slate-800/60 opacity-75'
                        : 'bg-slate-950/80 border-slate-800'
                    }`}
                  >
                    <div className="flex items-start gap-2.5">
                      <button
                        onClick={() => handleToggleTask(currentAgenda.id, item.id)}
                        className="mt-0.5 text-amber-400 hover:text-amber-300 shrink-0"
                      >
                        {item.isCompleted ? (
                          <CheckSquare className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <Square className="w-4 h-4 text-slate-600" />
                        )}
                      </button>

                      <div className="flex-1 space-y-1">
                        <span
                          className={`font-semibold ${
                            item.isCompleted
                              ? 'line-through text-slate-500'
                              : 'text-slate-100'
                          }`}
                        >
                          {item.title}
                        </span>

                        {item.notes && (
                          <p className="text-[11px] text-slate-400">
                            {item.notes}
                          </p>
                        )}

                        <div className="flex items-center gap-3 text-[10px] text-slate-500 font-mono pt-1">
                          <span className="text-amber-400/90 font-medium">
                            {item.assignedTo}
                          </span>
                          <span>·</span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3 text-slate-400" />
                            Target: {item.deadline}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Minutes Summary */}
            {currentAgenda.minutesSummary && (
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Recorded Assembly Minutes & Decisions:
                </span>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  {currentAgenda.minutesSummary}
                </p>
              </div>
            )}

          </div>

          {/* Right Column: Chamber Logistics & Equipment Checklist (5 cols) */}
          <div className="lg:col-span-5 space-y-5">
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Package className="w-4 h-4 text-amber-400" />
                  <div>
                    <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                      Debate Logistics & Inventory
                    </h3>
                    <p className="text-[11px] text-slate-400">
                      Physical chamber & tournament gear
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowAddLogisticsModal(true)}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs border border-slate-700 transition-colors"
                >
                  <Plus className="w-3 h-3" />
                  <span>Add Gear</span>
                </button>
              </div>

              <div className="space-y-2">
                {currentAgenda.logisticsChecklist.map((log) => (
                  <div
                    key={log.id}
                    onClick={() =>
                      handleToggleLogisticsStatus(currentAgenda.id, log.id)
                    }
                    className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between gap-3 text-xs cursor-pointer hover:border-slate-700 transition-colors"
                  >
                    <div className="truncate pr-2">
                      <div className="font-medium text-slate-200 truncate">
                        {log.item}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                        Qty: {log.quantity} · Custodian: {log.assignedTo}
                      </div>
                    </div>

                    <button
                      className={`px-2.5 py-1 rounded text-[10px] font-semibold uppercase tracking-wider shrink-0 transition-colors ${
                        log.status === 'Ready'
                          ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                          : log.status === 'Pending'
                          ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                          : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                      }`}
                    >
                      {log.status}
                    </button>
                  </div>
                ))}
              </div>

              <p className="text-[11px] text-slate-500 italic text-center pt-2">
                Click any gear item to cycle status: Ready ➔ Pending ➔ Not Started
              </p>
            </div>

            {/* Executive Committee Roster */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Executive Portfolios
              </h4>
              <div className="space-y-1.5 text-xs">
                {members
                  .filter((m) => m.role === 'executive')
                  .map((exec) => (
                    <div
                      key={exec.id}
                      className="flex items-center justify-between p-2 rounded bg-slate-950/40 text-slate-300"
                    >
                      <span className="font-medium text-white">{exec.fullName}</span>
                      <span className="text-[10px] text-amber-400 font-mono">
                        {exec.executivePosition}
                      </span>
                    </div>
                  ))}
              </div>
            </div>

          </div>

        </div>
      )}

      {/* Add Action Item Modal */}
      {showAddActionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl bg-slate-900 border border-slate-800 p-6 shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Delegate Executive Action Item
            </h3>

            <form onSubmit={handleCreateActionItem} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">Task Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Confirm debate hall booking at Kibos Campus"
                  value={actionTitle}
                  onChange={(e) => setActionTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Assigned Executive</label>
                <select
                  value={actionAssignee}
                  onChange={(e) => setActionAssignee(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white"
                >
                  {members
                    .filter((m) => m.role === 'executive')
                    .map((m) => (
                      <option key={m.id} value={`${m.fullName} (${m.executivePosition})`}>
                        {m.fullName} — {m.executivePosition}
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Target Deadline</label>
                <input
                  type="date"
                  value={actionDeadline}
                  onChange={(e) => setActionDeadline(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Execution Notes (Optional)</label>
                <textarea
                  rows={2}
                  placeholder="Specific requirements, contact persons, or budget limits..."
                  value={actionNotes}
                  onChange={(e) => setActionNotes(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddActionModal(false)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold rounded"
                >
                  Assign Action
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Logistics Item Modal */}
      {showAddLogisticsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl bg-slate-900 border border-slate-800 p-6 shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Add Logistics Gear / Checklist Item
            </h3>

            <form onSubmit={handleCreateLogisticsItem} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">Item Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Wireless Microphones & PA System"
                  value={logisticsItem}
                  onChange={(e) => setLogisticsItem(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">Quantity</label>
                  <input
                    type="number"
                    min="1"
                    value={logisticsQty}
                    onChange={(e) => setLogisticsQty(parseInt(e.target.value) || 1)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Assigned Custodian</label>
                  <input
                    type="text"
                    value={logisticsAssignee}
                    onChange={(e) => setLogisticsAssignee(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddLogisticsModal(false)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold rounded"
                >
                  Add to Checklist
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};


