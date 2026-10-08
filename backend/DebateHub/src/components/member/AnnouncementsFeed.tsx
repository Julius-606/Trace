
import React, { useState } from 'react';
import { Announcement, Member } from '../../types';
import {
  Bell,
  Pin,
  Calendar,
  User,
  Plus,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  CreditCard,
  QrCode,
  Send,
} from 'lucide-react';

interface AnnouncementsFeedProps {
  announcements: Announcement[];
  currentUser: Member;
  onAddAnnouncement: (announcement: Announcement) => void;
  onSubmitDuesMpesa: (mpesaCode: string) => void;
  onOpenPassModal: () => void;
}

export const AnnouncementsFeed: React.FC<AnnouncementsFeedProps> = ({
  announcements,
  currentUser,
  onAddAnnouncement,
  onSubmitDuesMpesa,
  onOpenPassModal,
}) => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [newCategory, setNewCategory] = useState<any>('Tournament');
  const [newPriority, setNewPriority] = useState<any>('High');
  const [isPinned, setIsPinned] = useState(false);

  // Mpesa submit state
  const [memberMpesaInput, setMemberMpesaInput] = useState('');
  const [submittedMpesaSuccess, setSubmittedMpesaSuccess] = useState(false);

  const isExecutive = currentUser.role === 'executive';

  const handleCreateAnnouncement = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle || !newContent) return;

    const ann: Announcement = {
      id: `ann-${Date.now()}`,
      title: newTitle,
      content: newContent,
      author: currentUser.fullName,
      authorRole: currentUser.executivePosition || 'Executive Officer',
      publishDate: new Date().toISOString().split('T')[0],
      priority: newPriority,
      category: newCategory,
      pinned: isPinned,
    };

    onAddAnnouncement(ann);
    setShowAddModal(false);
    setNewTitle('');
    setNewContent('');
    setIsPinned(false);
  };

  const handleMpesaSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!memberMpesaInput) return;
    onSubmitDuesMpesa(memberMpesaInput.toUpperCase().trim());
    setSubmittedMpesaSuccess(true);
    setMemberMpesaInput('');
    setTimeout(() => setSubmittedMpesaSuccess(false), 4000);
  };

  // Sort: pinned first, then by date
  const sortedAnnouncements = [...announcements].sort((a, b) => {
    if (a.pinned && !b.pinned) return -1;
    if (!a.pinned && b.pinned) return 1;
    return new Date(b.publishDate).getTime() - new Date(a.publishDate).getTime();
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

      {/* Main Feed: 8 cols */}
      <div className="lg:col-span-8 space-y-4">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Bell className="w-4 h-4 text-amber-400" />
              <span>Official Executive Announcements</span>
            </h2>
            <p className="text-xs text-slate-400">
              Notices from the President, Chief Adjudicator, and Treasury.
            </p>
          </div>

          {isExecutive && (
            <button
              onClick={() => setShowAddModal(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-950 bg-amber-400 hover:bg-amber-300 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Post Notice</span>
            </button>
          )}
        </div>

        {/* List of Notices */}
        <div className="space-y-3.5">
          {sortedAnnouncements.map((ann) => {
            const isUrgent = ann.priority === 'Urgent';
            const isHigh = ann.priority === 'High';

            return (
              <div
                key={ann.id}
                className={`p-5 rounded-xl border transition-all ${
                  ann.pinned
                    ? 'bg-slate-900/90 border-amber-500/40 shadow-sm shadow-amber-500/5'
                    : 'bg-slate-900/60 border-slate-800'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1 flex-1">
                    <div className="flex flex-wrap items-center gap-2 text-[11px]">
                      {ann.pinned && (
                        <span className="inline-flex items-center gap-1 text-amber-400 font-semibold">
                          <Pin className="w-3 h-3 fill-current" />
                          Pinned Notice
                        </span>
                      )}
                      <span className="text-slate-600">·</span>
                      <span className="text-slate-400 font-medium">{ann.category}</span>
                      <span className="text-slate-600">·</span>
                      <span className="font-mono text-slate-500">{ann.publishDate}</span>
                    </div>

                    <h3 className="text-sm sm:text-base font-bold text-white pt-1">
                      {ann.title}
                    </h3>
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider shrink-0 ${
                      isUrgent
                        ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                        : isHigh
                        ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {ann.priority}
                  </span>
                </div>

                <p className="mt-2.5 text-xs text-slate-300 leading-relaxed font-sans">
                  {ann.content}
                </p>

                <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                  <span>
                    Posted by: <strong className="text-slate-200">{ann.author}</strong> ({ann.authorRole})
                  </span>
                  <span className="text-slate-500 font-mono text-[10px]">
                    Great Lakes University of Kisumu
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Sidebar: Member Personal Standing & Dues Tracker (4 cols) */}
      <div className="lg:col-span-4 space-y-4">
        
        {/* Member Profile Standing Card */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              My Member Standing
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 capitalize">
              {currentUser.role}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500/20 to-blue-600/20 border border-slate-700 flex items-center justify-center text-amber-300 font-bold text-lg shrink-0">
              {currentUser.fullName.charAt(0)}
            </div>
            <div>
              <h4 className="text-sm font-bold text-white">{currentUser.fullName}</h4>
              <p className="text-xs font-mono text-slate-400">{currentUser.studentId}</p>
              <p className="text-[11px] text-slate-500 truncate max-w-[170px]">
                {currentUser.faculty}
              </p>
            </div>
          </div>

          {/* Attendance progress bar */}
          <div className="space-y-1.5 pt-2 border-t border-slate-800">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">Semester Session Attendance</span>
              <span className="font-mono text-white font-bold">
                {currentUser.attendanceRate}%
              </span>
            </div>
            <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
              <div
                className="bg-emerald-400 h-full rounded-full"
                style={{ width: `${currentUser.attendanceRate}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>{currentUser.debatesAttendedCount} Attended</span>
              <span>{currentUser.totalDebatesCount} Rounds Held</span>
            </div>
          </div>

          {/* Dues Status & Payment verification */}
          <div className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Semester 1 Dues:</span>
              <span
                className={`font-semibold ${
                  currentUser.membershipStatus === 'Paid'
                    ? 'text-emerald-400'
                    : 'text-amber-400'
                }`}
              >
                {currentUser.membershipStatus} (KES 500)
              </span>
            </div>

            {currentUser.membershipStatus === 'Paid' ? (
              <div className="flex items-center gap-1.5 text-[11px] text-emerald-400">
                <CheckCircle className="w-3.5 h-3.5 shrink-0" />
                <span>Cleared via M-Pesa: {currentUser.mpesaRef}</span>
              </div>
            ) : (
              <form onSubmit={handleMpesaSubmit} className="space-y-2 pt-1">
                <p className="text-[11px] text-slate-400">
                  Pay KES 500 via M-Pesa Buy Goods / Till, then submit your transaction code below:
                </p>
                <div className="flex gap-1.5">
                  <input
                    type="text"
                    placeholder="e.g. QRA891MP11"
                    value={memberMpesaInput}
                    onChange={(e) => setMemberMpesaInput(e.target.value)}
                    className="flex-1 bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-xs text-amber-300 font-mono uppercase"
                  />
                  <button
                    type="submit"
                    className="px-3 py-1 bg-amber-400 text-slate-950 rounded text-xs font-bold hover:bg-amber-300"
                  >
                    Submit
                  </button>
                </div>
                {submittedMpesaSuccess && (
                  <p className="text-[11px] text-emerald-400">
                    ✓ Code submitted to Treasury Secretary for verification!
                  </p>
                )}
              </form>
            )}
          </div>

          {/* Pass button */}
          <button
            onClick={onOpenPassModal}
            className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
          >
            <QrCode className="w-3.5 h-3.5 text-amber-400" />
            <span>Digital Club Member Card</span>
          </button>
        </div>

        {/* Club Quick Tips */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2 text-xs">
          <span className="font-bold text-slate-300 uppercase tracking-wider text-[10px]">
            Debater Guidelines
          </span>
          <p className="text-slate-400 leading-normal">
            To qualify for the KUDC 2026 travel delegation and ballot voting, debaters must maintain ≥75% attendance and active dues clearance.
          </p>
        </div>

      </div>

      {/* Post Notice Modal (Executive) */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl bg-slate-900 border border-slate-800 p-6 shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Publish Executive Club Notice
            </h3>

            <form onSubmit={handleCreateAnnouncement} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">Notice Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Western Circuit Open - Bus Departure Times"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">Category</label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white"
                  >
                    <option value="Tournament">Tournament</option>
                    <option value="Weekly Training">Weekly Training</option>
                    <option value="Executive Notice">Executive Notice</option>
                    <option value="Social & Mentorship">Social & Mentorship</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Priority Level</label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white"
                  >
                    <option value="Normal">Normal</option>
                    <option value="High">High</option>
                    <option value="Urgent">Urgent</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Notice Content</label>
                <textarea
                  rows={4}
                  required
                  placeholder="Write full details, instructions, or deadlines for members..."
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="pinNotice"
                  checked={isPinned}
                  onChange={(e) => setIsPinned(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-950 text-amber-400"
                />
                <label htmlFor="pinNotice" className="text-slate-300">
                  Pin this notice to top of member feed
                </label>
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold rounded"
                >
                  Publish Notice
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};


