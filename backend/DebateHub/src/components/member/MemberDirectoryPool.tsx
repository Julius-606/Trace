
import React, { useState } from 'react';
import { Member, AlumniMentorshipNote } from '../../types';
import { GlukDebateLogo } from '../common/GlukDebateLogo';
import {
  Users,
  Search,
  Filter,
  GraduationCap,
  Briefcase,
  Award,
  CheckCircle,
  Clock,
  Mail,
  Phone,
  QrCode,
  Sparkles,
  MessageSquare,
  BookOpen,
} from 'lucide-react';

interface MemberDirectoryPoolProps {
  members: Member[];
  currentUser: Member;
  mentorshipNotes: AlumniMentorshipNote[];
  onAddMentorshipNote: (note: AlumniMentorshipNote) => void;
}

export const MemberDirectoryPool: React.FC<MemberDirectoryPoolProps> = ({
  members,
  currentUser,
  mentorshipNotes,
  onAddMentorshipNote,
}) => {
  const [filterRole, setFilterRole] = useState<'all' | 'student' | 'executive' | 'alumni'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMember, setSelectedMember] = useState<Member | null>(null);

  // Mentorship request modal
  const [showMentorModal, setShowMentorModal] = useState(false);
  const [targetAlumni, setTargetAlumni] = useState<Member | null>(null);
  const [mentorTopic, setMentorTopic] = useState('');
  const [mentorAdviceNote, setMentorAdviceNote] = useState('');

  const filteredMembers = members.filter((m) => {
    const matchesRole =
      filterRole === 'all'
        ? true
        : filterRole === 'alumni'
        ? m.role === 'alumni'
        : filterRole === 'executive'
        ? m.role === 'executive'
        : m.role === 'member';

    const matchesSearch =
      m.fullName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.faculty.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.studentId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (m.alumniOccupation && m.alumniOccupation.toLowerCase().includes(searchQuery.toLowerCase()));

    return matchesRole && matchesSearch;
  });

  const handleRequestMentorship = (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetAlumni || !mentorTopic) return;

    const newNote: AlumniMentorshipNote = {
      id: `mn-${Date.now()}`,
      alumniId: targetAlumni.id,
      alumniName: targetAlumni.fullName,
      menteeName: currentUser.fullName,
      menteeId: currentUser.id,
      topic: mentorTopic,
      date: new Date().toISOString().split('T')[0],
      adviceSummary: mentorAdviceNote || 'Mentorship session scheduled on Google Meet. Awaiting initial briefing.',
      status: 'Active',
    };

    onAddMentorshipNote(newNote);
    setShowMentorModal(false);
    setMentorTopic('');
    setMentorAdviceNote('');
  };

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Member Pool & Alumni Mentorship Hub</span>
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20">
              {members.length} Debaters & Alumni
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Community pool of active university debaters, executive officers, and distinguished alumni mentors.
          </p>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by name, faculty, or career..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-amber-500/50 w-64 sm:w-72"
          />
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5 p-1 bg-slate-900 rounded-lg border border-slate-800 w-fit">
        <button
          onClick={() => setFilterRole('all')}
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
            filterRole === 'all'
              ? 'bg-amber-400/20 text-amber-300 font-semibold shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          All Members ({members.length})
        </button>
        <button
          onClick={() => setFilterRole('executive')}
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
            filterRole === 'executive'
              ? 'bg-amber-400/20 text-amber-300 font-semibold shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Executive Committee ({members.filter((m) => m.role === 'executive').length})
        </button>
        <button
          onClick={() => setFilterRole('student')}
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
            filterRole === 'student'
              ? 'bg-amber-400/20 text-amber-300 font-semibold shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Active Debaters ({members.filter((m) => m.role === 'member').length})
        </button>
        <button
          onClick={() => setFilterRole('alumni')}
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
            filterRole === 'alumni'
              ? 'bg-amber-400/20 text-amber-300 font-semibold shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Alumni Mentors ({members.filter((m) => m.role === 'alumni').length})
        </button>
      </div>

      {/* Member Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredMembers.map((member) => {
          const isAlumni = member.role === 'alumni';
          const isExec = member.role === 'executive';

          return (
            <div
              key={member.id}
              className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4 hover:border-slate-700 transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/20 to-blue-600/20 border border-slate-700 flex items-center justify-center text-amber-300 font-bold text-sm shrink-0">
                      {member.fullName.charAt(0)}
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white leading-tight">
                        {member.fullName}
                      </h3>
                      <span className="text-[11px] font-mono text-slate-400">
                        {member.studentId}
                      </span>
                    </div>
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${
                      isExec
                        ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                        : isAlumni
                        ? 'bg-purple-500/15 text-purple-300 border border-purple-500/30'
                        : 'bg-blue-500/15 text-blue-300 border border-blue-500/30'
                    }`}
                  >
                    {isExec ? member.executivePosition : member.role}
                  </span>
                </div>

                {isAlumni ? (
                  <div className="space-y-1.5 p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 text-xs">
                    <div className="flex items-center gap-1.5 text-purple-300 font-medium">
                      <Briefcase className="w-3.5 h-3.5" />
                      <span className="truncate">{member.alumniOccupation}</span>
                    </div>
                    <div className="text-[11px] text-slate-400 truncate pl-5">
                      {member.alumniOrganization}
                    </div>
                  </div>
                ) : (
                  <div className="text-xs text-slate-300">
                    <span className="font-medium text-slate-400">{member.yearOfStudy}</span>
                    <span className="text-slate-600 mx-1.5">·</span>
                    <span className="truncate">{member.faculty}</span>
                  </div>
                )}

                {member.bio && (
                  <p className="text-[11px] text-slate-400 line-clamp-2 italic">
                    "{member.bio}"
                  </p>
                )}

                {/* Quantitative debate track record */}
                <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800/80 text-center text-xs">
                  <div>
                    <span className="text-[10px] text-slate-500 block uppercase">
                      Attendance
                    </span>
                    <span className="font-mono font-bold text-white tabular-nums">
                      {member.attendanceRate}%
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block uppercase">
                      Debates
                    </span>
                    <span className="font-mono font-bold text-slate-200 tabular-nums">
                      {member.debatesAttendedCount}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block uppercase">
                      Avg Speaker
                    </span>
                    <span className="font-mono font-bold text-amber-400 tabular-nums">
                      {member.speakerPointsAvg}
                    </span>
                  </div>
                </div>
              </div>

              {/* Action buttons */}
              <div className="pt-3 border-t border-slate-800 flex items-center justify-between gap-2">
                <button
                  onClick={() => setSelectedMember(member)}
                  className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-white"
                >
                  <QrCode className="w-3.5 h-3.5 text-amber-400" />
                  <span>View Member Pass</span>
                </button>

                {isAlumni ? (
                  <button
                    onClick={() => {
                      setTargetAlumni(member);
                      setShowMentorModal(true);
                    }}
                    className="px-2.5 py-1 bg-purple-500/20 hover:bg-purple-500/30 text-purple-200 border border-purple-500/30 rounded text-xs font-semibold transition-colors"
                  >
                    Request Mentorship
                  </button>
                ) : (
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded font-medium ${
                      member.membershipStatus === 'Paid'
                        ? 'text-emerald-400 bg-emerald-500/10'
                        : 'text-amber-400 bg-amber-500/10'
                    }`}
                  >
                    Dues: {member.membershipStatus}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Alumni Mentorship Notes Log */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-purple-400" />
              <span>Alumni Mentorship Notes & Masterclasses</span>
            </h3>
            <p className="text-xs text-slate-400">
              Direct guidance shared between GLUK alumni practitioners and active student debaters.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {mentorshipNotes.map((note) => (
            <div
              key={note.id}
              className="p-4 rounded-lg bg-slate-950/70 border border-slate-800 text-xs space-y-2"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="font-semibold text-amber-300">
                  {note.topic}
                </span>
                <span className="text-[10px] font-mono text-slate-500 whitespace-nowrap">
                  {note.date}
                </span>
              </div>
              <p className="text-slate-300 leading-relaxed italic">
                "{note.adviceSummary}"
              </p>
              <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-[10px] text-slate-400">
                <span>Mentor: <strong className="text-slate-200">{note.alumniName}</strong></span>
                <span>Mentee: <strong className="text-slate-200">{note.menteeName}</strong></span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Member Pass / ID Card Modal */}
      {selectedMember && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-amber-500/30 p-6 shadow-2xl space-y-5 text-center relative overflow-hidden">
            {/* Top gold badge glow */}
            <div className="absolute -top-12 left-1/2 -translate-x-1/2 w-40 h-40 bg-amber-500/10 rounded-full blur-2xl pointer-events-none" />

            <div className="flex justify-center">
              <GlukDebateLogo size={64} />
            </div>

            <div>
              <span className="text-[10px] uppercase font-bold tracking-widest text-amber-400 block">
                Great Lakes University of Kisumu
              </span>
              <h3 className="text-lg font-bold text-white mt-0.5">
                {selectedMember.fullName}
              </h3>
              <p className="text-xs font-mono text-slate-400">
                {selectedMember.studentId}
              </p>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-left space-y-1.5">
              <div className="flex justify-between">
                <span className="text-slate-400">Portfolio:</span>
                <span className="font-semibold text-slate-200 capitalize">
                  {selectedMember.executivePosition || selectedMember.role}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Faculty:</span>
                <span className="font-semibold text-slate-200 truncate max-w-[170px]">
                  {selectedMember.faculty}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Dues Status:</span>
                <span
                  className={`font-bold ${
                    selectedMember.membershipStatus === 'Paid'
                      ? 'text-emerald-400'
                      : 'text-amber-400'
                  }`}
                >
                  {selectedMember.membershipStatus} (AY 2026/2027)
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Attendance:</span>
                <span className="font-mono text-slate-200">
                  {selectedMember.attendanceRate}% ({selectedMember.debatesAttendedCount} Rounds)
                </span>
              </div>
            </div>

            {/* QR Code Simulation */}
            <div className="flex flex-col items-center justify-center p-3 rounded-xl bg-white text-slate-950 space-y-1">
              <div className="w-24 h-24 border-2 border-slate-950 p-1 flex items-center justify-center bg-slate-100">
                <QrCode className="w-20 h-20 text-slate-950" />
              </div>
              <span className="text-[9px] font-mono tracking-widest uppercase font-bold text-slate-700">
                GLUK-DC-VERIFIED-PASS
              </span>
            </div>

            <button
              onClick={() => setSelectedMember(null)}
              className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold transition-colors"
            >
              Close Pass
            </button>
          </div>
        </div>
      )}

      {/* Mentorship Request Modal */}
      {showMentorModal && targetAlumni && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl bg-slate-900 border border-slate-800 p-6 shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Request 1-on-1 Mentorship with {targetAlumni.fullName}
            </h3>
            <p className="text-xs text-slate-400">
              {targetAlumni.alumniOccupation} at {targetAlumni.alumniOrganization}.
            </p>

            <form onSubmit={handleRequestMentorship} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">Debate or Career Focus Area</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Masterclass on Closing Half Extensions or Law School Prep"
                  value={mentorTopic}
                  onChange={(e) => setMentorTopic(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Specific Questions or Background</label>
                <textarea
                  rows={3}
                  placeholder="Share the debate clash points or career trajectory you'd like advice on..."
                  value={mentorAdviceNote}
                  onChange={(e) => setMentorAdviceNote(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowMentorModal(false)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-purple-500 hover:bg-purple-400 text-white font-bold rounded"
                >
                  Send Mentorship Request
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};


