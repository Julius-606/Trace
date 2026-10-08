
import {
  Member,
  AgendaItem,
  FinancialTransaction,
  DebateSession,
  Announcement,
  CalendarEvent,
  AlumniMentorshipNote,
} from '../types';
import {
  initialMembers,
  initialAgendas,
  initialTransactions,
  initialDebateSessions,
  initialAnnouncements,
  initialCalendarEvents,
  initialMentorshipNotes,
} from '../data/initialData';

const STORAGE_KEYS = {
  MEMBERS: 'gluk_dc_members_v1',
  AGENDAS: 'gluk_dc_agendas_v1',
  TRANSACTIONS: 'gluk_dc_transactions_v1',
  DEBATES: 'gluk_dc_debates_v1',
  ANNOUNCEMENTS: 'gluk_dc_announcements_v1',
  EVENTS: 'gluk_dc_events_v1',
  MENTORSHIP: 'gluk_dc_mentorship_v1',
  CURRENT_USER_ID: 'gluk_dc_current_user_id_v1',
  CURRENT_ROLE: 'gluk_dc_current_role_v1',
};

function loadItem<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw);
  } catch (err) {
    console.warn(`Failed to parse localStorage key ${key}:`, err);
    return fallback;
  }
}

function saveItem<T>(key: string, data: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (err) {
    console.error(`Failed to save localStorage key ${key}:`, err);
  }
}

export const storage = {
  getMembers(): Member[] {
    return loadItem(STORAGE_KEYS.MEMBERS, initialMembers);
  },
  saveMembers(members: Member[]): void {
    saveItem(STORAGE_KEYS.MEMBERS, members);
  },

  getAgendas(): AgendaItem[] {
    return loadItem(STORAGE_KEYS.AGENDAS, initialAgendas);
  },
  saveAgendas(agendas: AgendaItem[]): void {
    saveItem(STORAGE_KEYS.AGENDAS, agendas);
  },

  getTransactions(): FinancialTransaction[] {
    return loadItem(STORAGE_KEYS.TRANSACTIONS, initialTransactions);
  },
  saveTransactions(txns: FinancialTransaction[]): void {
    saveItem(STORAGE_KEYS.TRANSACTIONS, txns);
  },

  getDebates(): DebateSession[] {
    return loadItem(STORAGE_KEYS.DEBATES, initialDebateSessions);
  },
  saveDebates(debates: DebateSession[]): void {
    saveItem(STORAGE_KEYS.DEBATES, debates);
  },

  getAnnouncements(): Announcement[] {
    return loadItem(STORAGE_KEYS.ANNOUNCEMENTS, initialAnnouncements);
  },
  saveAnnouncements(ann: Announcement[]): void {
    saveItem(STORAGE_KEYS.ANNOUNCEMENTS, ann);
  },

  getEvents(): CalendarEvent[] {
    return loadItem(STORAGE_KEYS.EVENTS, initialCalendarEvents);
  },
  saveEvents(events: CalendarEvent[]): void {
    saveItem(STORAGE_KEYS.EVENTS, events);
  },

  getMentorshipNotes(): AlumniMentorshipNote[] {
    return loadItem(STORAGE_KEYS.MENTORSHIP, initialMentorshipNotes);
  },
  saveMentorshipNotes(notes: AlumniMentorshipNote[]): void {
    saveItem(STORAGE_KEYS.MENTORSHIP, notes);
  },

  getCurrentUserId(): string {
    return loadItem(STORAGE_KEYS.CURRENT_USER_ID, 'mem-exec-1'); // Default Julius Gachoki (President)
  },
  saveCurrentUserId(id: string): void {
    saveItem(STORAGE_KEYS.CURRENT_USER_ID, id);
  },

  getCurrentRole(): 'executive' | 'member' | 'alumni' {
    return loadItem(STORAGE_KEYS.CURRENT_ROLE, 'executive');
  },
  saveCurrentRole(role: 'executive' | 'member' | 'alumni'): void {
    saveItem(STORAGE_KEYS.CURRENT_ROLE, role);
  },

  resetAll(): void {
    localStorage.removeItem(STORAGE_KEYS.MEMBERS);
    localStorage.removeItem(STORAGE_KEYS.AGENDAS);
    localStorage.removeItem(STORAGE_KEYS.TRANSACTIONS);
    localStorage.removeItem(STORAGE_KEYS.DEBATES);
    localStorage.removeItem(STORAGE_KEYS.ANNOUNCEMENTS);
    localStorage.removeItem(STORAGE_KEYS.EVENTS);
    localStorage.removeItem(STORAGE_KEYS.MENTORSHIP);
    localStorage.removeItem(STORAGE_KEYS.CURRENT_USER_ID);
    localStorage.removeItem(STORAGE_KEYS.CURRENT_ROLE);
  },

  exportDatabaseJson(): string {
    const fullDb = {
      members: this.getMembers(),
      agendas: this.getAgendas(),
      transactions: this.getTransactions(),
      debates: this.getDebates(),
      announcements: this.getAnnouncements(),
      events: this.getEvents(),
      mentorshipNotes: this.getMentorshipNotes(),
      exportedAt: new Date().toISOString(),
      institution: 'Great Lakes University of Kisumu Debate Club',
    };
    return JSON.stringify(fullDb, null, 2);
  },
};


