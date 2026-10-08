
import React, { useState } from 'react';
import { CalendarEvent, Member } from '../../types';
import {
  Calendar as CalendarIcon,
  Clock,
  MapPin,
  ExternalLink,
  Plus,
  Download,
  Filter,
  CheckCircle,
} from 'lucide-react';

interface CalendarActivitiesProps {
  events: CalendarEvent[];
  currentUser: Member;
  onAddEvent: (event: CalendarEvent) => void;
}

export const CalendarActivities: React.FC<CalendarActivitiesProps> = ({
  events,
  currentUser,
  onAddEvent,
}) => {
  const [filterType, setFilterType] = useState<string>('All');
  const [showAddModal, setShowAddModal] = useState(false);

  // New event form state
  const [eventTitle, setEventTitle] = useState('');
  const [eventDate, setEventDate] = useState('');
  const [eventStart, setEventStart] = useState('17:00');
  const [eventEnd, setEventEnd] = useState('19:00');
  const [eventLocation, setEventLocation] = useState('GLUK Kibos Campus - Hall 4');
  const [eventMeetUrl, setEventMeetUrl] = useState('https://meet.google.com/gluk-deb-2026');
  const [eventType, setEventType] = useState<any>('Debate Session');
  const [eventDescription, setEventDescription] = useState('');

  const isExecutive = currentUser.role === 'executive';

  const filteredEvents = events.filter((ev) => {
    if (filterType === 'All') return true;
    return ev.eventType === filterType;
  });

  const handleCreateEvent = (e: React.FormEvent) => {
    e.preventDefault();
    if (!eventTitle || !eventDate) return;

    const newEv: CalendarEvent = {
      id: `cal-${Date.now()}`,
      title: eventTitle,
      date: eventDate,
      startTime: eventStart,
      endTime: eventEnd,
      location: eventLocation,
      googleMeetUrl: eventMeetUrl || undefined,
      eventType: eventType,
      description: eventDescription,
      leadCoordinator: currentUser.fullName,
    };

    onAddEvent(newEv);
    setShowAddModal(false);
    setEventTitle('');
    setEventDescription('');
  };

  const generateIcsFile = () => {
    let icsContent = `BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//GLUK Debate Club//Calendar//EN\nCALSCALE:GREGORIAN\nMETHOD:PUBLISH\n`;
    
    events.forEach((ev) => {
      const dtDate = ev.date.replace(/-/g, '');
      const dtStart = `${dtDate}T${ev.startTime.replace(':', '')}00`;
      const dtEnd = `${dtDate}T${ev.endTime.replace(':', '')}00`;

      icsContent += `BEGIN:VEVENT\nUID:${ev.id}@glukdebate.ke\nSUMMARY:${ev.title}\nDESCRIPTION:${ev.description}\nLOCATION:${ev.location}\nDTSTART:${dtStart}\nDTEND:${dtEnd}\nEND:VEVENT\n`;
    });

    icsContent += 'END:VCALENDAR';
    const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `GLUK_Debate_Calendar_${new Date().getFullYear()}.ics`;
    link.click();
  };

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Official Club Activity Calendar</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Weekly debate sessions, executive committee assemblies, national championship circuits, and workshops.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={generateIcsFile}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-900 border border-slate-800 hover:bg-slate-800 hover:text-white transition-colors"
            title="Download .ics file to import into Google Calendar or Apple Calendar"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Sync to Calendar (.ics)</span>
          </button>

          {isExecutive && (
            <button
              onClick={() => setShowAddModal(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-950 bg-amber-400 hover:bg-amber-300 transition-colors shadow-sm"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Schedule Event</span>
            </button>
          )}
        </div>
      </div>

      {/* Event Type Filter */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
        {['All', 'Debate Session', 'Training Workshop', 'Executive Meeting', 'Tournament', 'Alumni Mixer'].map((cat) => (
          <button
            key={cat}
            onClick={() => setFilterType(cat)}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg whitespace-nowrap transition-colors ${
              filterType === cat
                ? 'bg-amber-400/20 text-amber-300 border border-amber-400/30 font-semibold'
                : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Event Cards Timeline */}
      <div className="space-y-3.5">
        {filteredEvents.map((ev) => {
          const isDebate = ev.eventType === 'Debate Session';
          const isTournament = ev.eventType === 'Tournament';
          const isExec = ev.eventType === 'Executive Meeting';

          return (
            <div
              key={ev.id}
              className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1.5 flex-1">
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span
                    className={`font-semibold px-2 py-0.5 rounded text-[10px] uppercase tracking-wider ${
                      isTournament
                        ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                        : isDebate
                        ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                        : isExec
                        ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                        : 'bg-purple-500/15 text-purple-300 border border-purple-500/30'
                    }`}
                  >
                    {ev.eventType}
                  </span>
                  <span className="text-slate-600">·</span>
                  <span className="font-mono text-slate-300 font-semibold">
                    {ev.date}
                  </span>
                  <span className="text-slate-600">·</span>
                  <span className="font-mono text-slate-400">
                    {ev.startTime} - {ev.endTime} EAT
                  </span>
                </div>

                <h3 className="text-base font-bold text-white leading-snug">
                  {ev.title}
                </h3>

                <p className="text-xs text-slate-400 leading-relaxed">
                  {ev.description}
                </p>

                <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 pt-1">
                  <div className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    <span>{ev.location}</span>
                  </div>
                  <div>
                    Lead: <strong className="text-slate-300">{ev.leadCoordinator}</strong>
                  </div>
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex items-center gap-2 shrink-0">
                {ev.googleMeetUrl && (
                  <a
                    href={ev.googleMeetUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    <span>Open Meet Link</span>
                  </a>
                )}
                <a
                  href={`https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(
                    ev.title
                  )}&details=${encodeURIComponent(ev.description)}&location=${encodeURIComponent(
                    ev.location
                  )}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 transition-colors"
                >
                  + Google Cal
                </a>
              </div>
            </div>
          );
        })}
      </div>

      {/* Add Event Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl bg-slate-900 border border-slate-800 p-6 shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Schedule Official Club Activity
            </h3>

            <form onSubmit={handleCreateEvent} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">Event Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Round 15: Public Speaking & Karl Popper Drills"
                  value={eventTitle}
                  onChange={(e) => setEventTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">Event Type</label>
                  <select
                    value={eventType}
                    onChange={(e) => setEventType(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white"
                  >
                    <option value="Debate Session">Debate Session</option>
                    <option value="Training Workshop">Training Workshop</option>
                    <option value="Executive Meeting">Executive Meeting</option>
                    <option value="Tournament">Tournament</option>
                    <option value="Alumni Mixer">Alumni Mixer</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Date</label>
                  <input
                    type="date"
                    required
                    value={eventDate}
                    onChange={(e) => setEventDate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">Start Time (EAT)</label>
                  <input
                    type="time"
                    value={eventStart}
                    onChange={(e) => setEventStart(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">End Time (EAT)</label>
                  <input
                    type="time"
                    value={eventEnd}
                    onChange={(e) => setEventEnd(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                  />
                </div>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Physical Location / Campus</label>
                <input
                  type="text"
                  placeholder="e.g. GLUK Kibos Main Campus - Hall 4"
                  value={eventLocation}
                  onChange={(e) => setEventLocation(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Google Meet URL</label>
                <input
                  type="url"
                  placeholder="https://meet.google.com/..."
                  value={eventMeetUrl}
                  onChange={(e) => setEventMeetUrl(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Description / Notes</label>
                <textarea
                  rows={2}
                  placeholder="Format guidelines, reading materials, or speaker prep expectations..."
                  value={eventDescription}
                  onChange={(e) => setEventDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                />
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
                  Publish to Calendar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};


