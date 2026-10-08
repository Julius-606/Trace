
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import {
  Member,
  DebateSession,
  FinancialTransaction,
  AgendaItem,
  Announcement,
  CalendarEvent,
  AlumniMentorshipNote,
  ClubNotification,
} from '../types/index.ts';
import {
  initialMembers,
  initialDebateSessions,
  initialTransactions,
  initialAgendas,
  initialAnnouncements,
  initialCalendarEvents,
  initialMentorshipNotes,
} from '../data/initialData.ts';

export interface UserAccount extends Member {
  passwordHash: string;
}

export interface DatabaseSchema {
  meta: {
    initializedAt: string;
    clubName: string;
    version: string;
    isFresh: boolean;
  };
  users: UserAccount[];
  sessions: { token: string; userId: string; createdAt: string }[];
  debates: DebateSession[];
  transactions: FinancialTransaction[];
  agendas: AgendaItem[];
  announcements: Announcement[];
  events: CalendarEvent[];
  notifications: ClubNotification[];
  mentorshipNotes: AlumniMentorshipNote[];
}

const DB_FILE_PATH = path.join(process.cwd(), 'database.json');

// SSE Client listeners for real-time live flow
type LiveListener = (event: { type: string; payload: any; timestamp: string }) => void;
const liveListeners: Set<LiveListener> = new Set();

export function subscribeLive(listener: LiveListener): () => void {
  liveListeners.add(listener);
  return () => {
    liveListeners.delete(listener);
  };
}

export function broadcastLive(type: string, payload: any) {
  const event = {
    type,
    payload,
    timestamp: new Date().toISOString(),
  };
  for (const listener of liveListeners) {
    try {
      listener(event);
    } catch (e) {
      // Ignore dead connection
    }
  }
}

// Password hashing helper using Node.js crypto
export function hashPassword(password: string): string {
  return crypto.createHash('sha256').update(password + '_GLUK_SALT_2026').digest('hex');
}

export function verifyPassword(password: string, hash: string): boolean {
  return hashPassword(password) === hash;
}

// Read database from root JSON file
export function readDatabase(): DatabaseSchema {
  try {
    if (!fs.existsSync(DB_FILE_PATH)) {
      return initializeFreshDatabase();
    }
    const raw = fs.readFileSync(DB_FILE_PATH, 'utf-8');
    if (!raw.trim()) {
      return initializeFreshDatabase();
    }
    const parsed = JSON.parse(raw);
    return parsed;
  } catch (err) {
    console.error('Error reading database.json, reinitializing fresh:', err);
    return initializeFreshDatabase();
  }
}

// Save database to root JSON file
export function saveDatabase(data: DatabaseSchema): void {
  try {
    fs.writeFileSync(DB_FILE_PATH, JSON.stringify(data, null, 2), 'utf-8');
  } catch (err) {
    console.error('Error writing database.json:', err);
  }
}

// Create a clean database structure at root
export function initializeFreshDatabase(withSeedData = false): DatabaseSchema {
  const freshDb: DatabaseSchema = {
    meta: {
      initializedAt: new Date().toISOString(),
      clubName: 'Great Lakes University of Kisumu Debate Club',
      version: '2.0.0',
      isFresh: !withSeedData,
    },
    users: withSeedData
      ? initialMembers.map((m) => ({
          ...m,
          passwordHash: hashPassword('gluk2026'), // Default password for pre-seeded profiles
        }))
      : [],
    sessions: [],
    debates: withSeedData ? initialDebateSessions : [],
    transactions: withSeedData ? initialTransactions : [],
    agendas: withSeedData ? initialAgendas : [],
    announcements: withSeedData ? initialAnnouncements : [],
    events: withSeedData ? initialCalendarEvents : [],
    notifications: [],
    mentorshipNotes: withSeedData ? initialMentorshipNotes : [],
  };

  saveDatabase(freshDb);
  return freshDb;
}

// Reset database
export function resetDatabase(withSeed = false): DatabaseSchema {
  return initializeFreshDatabase(withSeed);
}

// Helper to push a notification and broadcast it live to clients
export function pushNotification(
  targetUserId: string,
  title: string,
  message: string,
  type: 'duty_delegated' | 'announcement' | 'dues_verified' | 'debate_round' | 'general',
  linkTab?: string
): ClubNotification {
  const db = readDatabase();
  const notification: ClubNotification = {
    id: `notif-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
    targetUserId,
    title,
    message,
    type,
    linkTab,
    isRead: false,
    createdAt: new Date().toISOString(),
  };

  db.notifications.unshift(notification);
  saveDatabase(db);

  // Broadcast to all connected clients live!
  broadcastLive('NOTIFICATION_NEW', notification);

  return notification;
}


