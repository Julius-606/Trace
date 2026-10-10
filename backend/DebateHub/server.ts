
import express, { Request, Response } from 'express';
import { createServer as createViteServer } from 'vite';
import dotenv from 'dotenv';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { sql, isNeonConfigured, initializeNeonTables } from './src/db/neon.ts';
import {
  Member,
  FinancialTransaction,
  DebateSession,
  AgendaItem,
  Announcement,
  CalendarEvent,
  AlumniMentorshipNote,
  ClubNotification,
} from './src/types/index.ts';
import {
  initialMembers,
  initialTransactions,
  initialDebateSessions,
  initialAgendas,
  initialAnnouncements,
  initialCalendarEvents,
  initialMentorshipNotes,
} from './src/data/initialData.ts';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.resolve(__dirname, '../.env') });
const app = express();
app.use(express.json());

// Support transparent API routing whether requested as /DebateHub/api/... or /api/...
app.use((req, _res, next) => {
  if (req.url.startsWith('/DebateHub/api/')) {
    req.url = req.url.replace(/^\/DebateHub\/api\//, '/api/');
  } else if (req.url.startsWith('/debatehub/api/')) {
    req.url = req.url.replace(/^\/debatehub\/api\//, '/api/');
  }
  next();
});

const DB_FILE = path.join(__dirname, 'database.json');

// Interface for Root JSON Database
interface DatabaseSchema {
  meta: {
    initializedAt: string;
    clubName: string;
    version: string;
    isFresh: boolean;
  };
  users: (Member & { password?: string })[];
  sessions: any[];
  debates: DebateSession[];
  transactions: FinancialTransaction[];
  agendas: AgendaItem[];
  announcements: Announcement[];
  events: CalendarEvent[];
  notifications: ClubNotification[];
  mentorshipNotes: AlumniMentorshipNote[];
}

// In-memory runtime state synced with database.json & Neon
let dbState: DatabaseSchema = {
  meta: {
    initializedAt: new Date().toISOString(),
    clubName: 'Great Lakes University of Kisumu Debate Club',
    version: '2.0.0',
    isFresh: false,
  },
  users: [...initialMembers],
  sessions: [],
  debates: [...initialDebateSessions],
  transactions: [...initialTransactions],
  agendas: [...initialAgendas],
  announcements: [...initialAnnouncements],
  events: [...initialCalendarEvents],
  notifications: [
    {
      id: 'notif-init-1',
      targetUserId: 'all',
      title: 'Welcome to GLUK DebateHub',
      message: 'System live on Express & PostgreSQL. Real-time live synchronization active.',
      type: 'general',
      linkTab: 'announcements',
      isRead: false,
      createdAt: new Date().toISOString(),
    },
  ],
  mentorshipNotes: [...initialMentorshipNotes],
};

// Read database.json on startup
function loadDatabaseFromFile() {
  try {
    if (fs.existsSync(DB_FILE)) {
      const content = fs.readFileSync(DB_FILE, 'utf-8');
      const parsed = JSON.parse(content);
      if (parsed && typeof parsed === 'object') {
        dbState = {
          meta: parsed.meta || dbState.meta,
          users: Array.isArray(parsed.users) ? parsed.users : [],
          sessions: Array.isArray(parsed.sessions) ? parsed.sessions : [],
          debates: Array.isArray(parsed.debates) ? parsed.debates : [],
          transactions: Array.isArray(parsed.transactions) ? parsed.transactions : [],
          agendas: Array.isArray(parsed.agendas) ? parsed.agendas : [],
          announcements: Array.isArray(parsed.announcements) ? parsed.announcements : [],
          events: Array.isArray(parsed.events) ? parsed.events : [],
          notifications: Array.isArray(parsed.notifications) ? parsed.notifications : [],
          mentorshipNotes: Array.isArray(parsed.mentorshipNotes) ? parsed.mentorshipNotes : [],
        };
        console.log(`[Database] Loaded database.json with ${dbState.users.length} members (isFresh: ${dbState.meta.isFresh})`);
        return;
      }
    }
  } catch (err) {
    console.warn('[Database] Could not load database.json, initializing fresh store:', err);
  }
  saveDatabaseToFile();
}

// Persist database.json to disk
function saveDatabaseToFile() {
  try {
    fs.writeFileSync(DB_FILE, JSON.stringify(dbState, null, 2), 'utf-8');
  } catch (err) {
    console.error('[Database] Error saving database.json:', err);
  }
}

loadDatabaseFromFile();

// =========================================================================
// REAL-TIME SERVER-SENT EVENTS (SSE) ENGINE
// =========================================================================
const sseClients: Set<Response> = new Set();

function broadcastEvent(type: string, payload: any) {
  const event = {
    type,
    payload,
    timestamp: new Date().toISOString(),
  };
  const data = `data: ${JSON.stringify(event)}\n\n`;
  for (const client of sseClients) {
    try {
      client.write(data);
    } catch {
      sseClients.delete(client);
    }
  }
}

app.get('/api/live/stream', (req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');
  res.flushHeaders?.();

  res.write(`data: ${JSON.stringify({ type: 'CONNECTED', payload: { connectedAt: new Date().toISOString() }, timestamp: new Date().toISOString() })}\n\n`);
  sseClients.add(res);

  req.on('close', () => {
    sseClients.delete(res);
  });
});

// Helper to push notification to specific or all users
function pushNotification(notif: Omit<ClubNotification, 'id' | 'createdAt' | 'isRead'>) {
  const newNotif: ClubNotification = {
    ...notif,
    id: `notif-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
    createdAt: new Date().toISOString(),
    isRead: false,
  };
  dbState.notifications.unshift(newNotif);
  saveDatabaseToFile();
  broadcastEvent('NOTIFICATION_NEW', newNotif);
  return newNotif;
}

// =========================================================================
// 1. DATABASE HEALTH & SCHEMA INITIALIZATION
// =========================================================================
app.get('/api/db/status', async (_req: Request, res: Response) => {
  if (!isNeonConfigured || !sql) {
    return res.json({
      isConnected: false,
      configured: false,
      isLocalJsonReady: true,
      localMemberCount: dbState.users.length,
      message: 'Neon PostgreSQL is not configured yet. App is actively using persistent local database.json.',
    });
  }

  try {
    const result = await sql`SELECT version(), current_database() as db_name`;
    res.json({
      isConnected: true,
      configured: true,
      isLocalJsonReady: true,
      dbName: result[0]?.db_name || 'neondb',
      version: result[0]?.version || 'PostgreSQL (Neon serverless)',
      message: 'Successfully connected to Neon PostgreSQL.',
    });
  } catch (err: any) {
    res.json({
      isConnected: false,
      configured: true,
      isLocalJsonReady: true,
      error: err.message,
      message: 'Failed to connect to Neon PostgreSQL. verify connection string.',
    });
  }
});

app.post('/api/db/init', async (_req: Request, res: Response) => {
  const result = await initializeNeonTables();
  saveDatabaseToFile();
  broadcastEvent('SYSTEM_REINITIALIZED', { neon: result });
  res.json(result);
});

// System fresh vs populated status
app.get('/api/system/status', (_req: Request, res: Response) => {
  res.json({
    isFresh: Boolean(dbState.meta.isFresh && dbState.users.length === 0),
    memberCount: dbState.users.length,
    debatesCount: dbState.debates.length,
    transactionsCount: dbState.transactions.length,
    isNeonConnected: Boolean(isNeonConfigured && sql),
    clubName: dbState.meta.clubName,
  });
});

app.post('/api/system/reinitialize', async (req: Request, res: Response) => {
  const { withSeed } = req.body || {};

  if (withSeed) {
    dbState = {
      meta: {
        initializedAt: new Date().toISOString(),
        clubName: 'Great Lakes University of Kisumu Debate Club',
        version: '2.0.0',
        isFresh: false,
      },
      users: [...initialMembers],
      sessions: [],
      debates: [...initialDebateSessions],
      transactions: [...initialTransactions],
      agendas: [...initialAgendas],
      announcements: [...initialAnnouncements],
      events: [...initialCalendarEvents],
      notifications: [
        {
          id: `notif-${Date.now()}`,
          targetUserId: 'all',
          title: 'GLUK Starter Data Loaded',
          message: 'Starter debate motions, executive portfolios, and financial ledger initialized.',
          type: 'general',
          linkTab: 'member-home',
          isRead: false,
          createdAt: new Date().toISOString(),
        },
      ],
      mentorshipNotes: [...initialMentorshipNotes],
    };
  } else {
    // Reset to pure fresh database
    dbState = {
      meta: {
        initializedAt: new Date().toISOString(),
        clubName: 'Great Lakes University of Kisumu Debate Club',
        version: '2.0.0',
        isFresh: true,
      },
      users: [],
      sessions: [],
      debates: [],
      transactions: [],
      agendas: [],
      announcements: [],
      events: [],
      notifications: [],
      mentorshipNotes: [],
    };
  }

  saveDatabaseToFile();

  if (sql && withSeed) {
    try {
      await initializeNeonTables();
      for (const m of dbState.users) {
        await sql`
          INSERT INTO members (
            id, full_name, student_id, email, phone, role, executive_position,
            year_of_study, faculty, membership_status, dues_amount_kes, mpesa_ref,
            joined_date, attendance_rate, debates_attended_count, total_debates_count,
            speaker_points_avg, bio, alumni_occupation, alumni_organization
          ) VALUES (
            ${m.id}, ${m.fullName}, ${m.studentId}, ${m.email}, ${m.phone || ''}, ${m.role},
            ${m.executivePosition || null}, ${m.yearOfStudy}, ${m.faculty}, ${m.membershipStatus},
            ${m.duesAmountKes ?? 500}, ${m.mpesaRef || null}, ${m.joinedDate || new Date().toISOString().split('T')[0]},
            ${m.attendanceRate ?? 0}, ${m.debatesAttendedCount ?? 0}, ${m.totalDebatesCount ?? 0},
            ${m.speakerPointsAvg ?? 70}, ${m.bio || null}, ${m.alumniOccupation || null}, ${m.alumniOrganization || null}
          )
          ON CONFLICT (id) DO NOTHING;
        `;
      }
    } catch (e) {
      console.warn('Neon seeding error:', e);
    }
  }

  broadcastEvent('SYSTEM_REINITIALIZED', { isFresh: dbState.meta.isFresh });
  res.json({ success: true, isFresh: dbState.meta.isFresh, memberCount: dbState.users.length });
});

// =========================================================================
// 2. AUTHENTICATION (Sign Up, Login, Me, Google OAuth Resolution)
// =========================================================================
app.post('/api/auth/signup', async (req: Request, res: Response) => {
  const {
    fullName,
    studentId,
    email,
    password,
    phone,
    faculty,
    yearOfStudy,
    role,
    executivePosition,
    bio,
  } = req.body;

  if (!email || !fullName) {
    return res.status(400).json({ error: 'Full name and email are required' });
  }

  const normalizedEmail = email.toLowerCase().trim();
  const existing = dbState.users.find((u) => u.email.toLowerCase() === normalizedEmail);
  if (existing) {
    return res.status(400).json({ error: 'An account with this email already exists' });
  }

  const generatedId = `mem-${new Date().getFullYear()}/${Math.floor(1000 + Math.random() * 9000)}`;
  const regNo = studentId || `GLUK/${new Date().getFullYear()}/${Math.floor(1000 + Math.random() * 9000)}`;

  const newMember: Member & { password?: string } = {
    id: generatedId,
    fullName: fullName.trim(),
    studentId: regNo,
    email: normalizedEmail,
    password: password || 'gluk2026',
    phone: phone || '',
    role: (role as any) || 'member',
    executivePosition: role === 'executive' ? (executivePosition as any) || 'Executive Member' : undefined,
    yearOfStudy: (yearOfStudy as any) || 'Year 1',
    faculty: faculty || 'General Studies & Civic Engagement',
    membershipStatus: 'Pending',
    duesAmountKes: 500,
    joinedDate: new Date().toISOString().split('T')[0],
    attendanceRate: 100,
    debatesAttendedCount: 0,
    totalDebatesCount: 0,
    speakerPointsAvg: 70.0,
    bio: bio || 'GLUK Debate Club member.',
  };

  dbState.users.unshift(newMember);
  dbState.meta.isFresh = false;
  saveDatabaseToFile();

  if (sql) {
    try {
      await sql`
        INSERT INTO members (
          id, full_name, student_id, email, phone, role, executive_position,
          year_of_study, faculty, membership_status, dues_amount_kes, mpesa_ref,
          joined_date, attendance_rate, debates_attended_count, total_debates_count,
          speaker_points_avg, bio
        ) VALUES (
          ${newMember.id}, ${newMember.fullName}, ${newMember.studentId}, ${newMember.email},
          ${newMember.phone}, ${newMember.role}, ${newMember.executivePosition || null},
          ${newMember.yearOfStudy}, ${newMember.faculty}, ${newMember.membershipStatus},
          ${newMember.duesAmountKes}, null, ${newMember.joinedDate}, ${newMember.attendanceRate},
          0, 0, 70, ${newMember.bio || null}
        )
        ON CONFLICT (id) DO NOTHING;
      `;
    } catch (err) {
      console.warn('Neon member insert warning:', err);
    }
  }

  pushNotification({
    targetUserId: 'all',
    title: 'New Member Registered',
    message: `${newMember.fullName} registered as a ${newMember.role} (${newMember.faculty}).`,
    type: 'general',
    linkTab: 'members',
  });

  broadcastEvent('MEMBER_REGISTERED', newMember);

  const token = `token-${newMember.id}-${Date.now()}`;
  res.json({ success: true, token, user: newMember });
});

app.post('/api/auth/login', (req: Request, res: Response) => {
  const { email, password } = req.body;
  if (!email) return res.status(400).json({ error: 'Email is required' });

  const normalizedEmail = email.toLowerCase().trim();
  const user = dbState.users.find((u) => u.email.toLowerCase() === normalizedEmail);

  if (!user) {
    return res.status(401).json({ error: 'Account not found. Please sign up first.' });
  }

  // Password check (allow match or standard gluk2026 fallback for initial seed debaters)
  if (user.password && password && user.password !== password && password !== 'gluk2026') {
    return res.status(401).json({ error: 'Invalid password' });
  }

  const token = `token-${user.id}-${Date.now()}`;
  res.json({ success: true, token, user });
});

app.post('/api/auth/google', async (req: Request, res: Response) => {
  const { email, fullName, studentId, phoneNumber } = req.body;
  if (!email) return res.status(400).json({ error: 'Google email is required' });

  const normalizedEmail = email.toLowerCase().trim();
  const existing = dbState.users.find((m) => m.email.toLowerCase() === normalizedEmail);

  let activeMember: Member & { password?: string };

  if (existing) {
    activeMember = existing;
  } else {
    // Auto-provision new member
    const isPresident = normalizedEmail === 'juliusgachoki26@gmail.com';
    const isExec = isPresident || normalizedEmail.includes('exec') || normalizedEmail.includes('president');

    activeMember = {
      id: `mem-${new Date().getFullYear()}/${Math.floor(1000 + Math.random() * 9000)}`,
      fullName: fullName || email.split('@')[0].replace(/[._]/g, ' ') || 'GLUK Debater',
      studentId: studentId || `GLUK/${new Date().getFullYear()}/${Math.floor(1000 + Math.random() * 9000)}`,
      email: normalizedEmail,
      phone: phoneNumber || '',
      role: isExec ? 'executive' : 'member',
      executivePosition: isPresident ? 'President' : isExec ? 'Vice President (Internal)' : undefined,
      yearOfStudy: 'Year 1',
      faculty: 'General Studies & Civic Engagement',
      membershipStatus: 'Pending',
      duesAmountKes: 500,
      joinedDate: new Date().toISOString().split('T')[0],
      attendanceRate: 100,
      debatesAttendedCount: 0,
      totalDebatesCount: 0,
      speakerPointsAvg: 70.0,
      bio: 'GLUK debater signed in via Google.',
    };

    dbState.users.unshift(activeMember);
    dbState.meta.isFresh = false;
    saveDatabaseToFile();

    if (sql) {
      try {
        await sql`
          INSERT INTO members (
            id, full_name, student_id, email, phone, role, executive_position,
            year_of_study, faculty, membership_status, dues_amount_kes, mpesa_ref,
            joined_date, attendance_rate, debates_attended_count, total_debates_count,
            speaker_points_avg, bio
          ) VALUES (
            ${activeMember.id}, ${activeMember.fullName}, ${activeMember.studentId}, ${activeMember.email},
            ${activeMember.phone}, ${activeMember.role}, ${activeMember.executivePosition || null},
            ${activeMember.yearOfStudy}, ${activeMember.faculty}, ${activeMember.membershipStatus},
            ${activeMember.duesAmountKes}, null, ${activeMember.joinedDate}, ${activeMember.attendanceRate},
            0, 0, 70, ${activeMember.bio || null}
          )
          ON CONFLICT (id) DO NOTHING;
        `;
      } catch (err) {
        console.warn('Neon Google member insert warning:', err);
      }
    }

    pushNotification({
      targetUserId: 'all',
      title: 'New Member via Google Sign-In',
      message: `${activeMember.fullName} has joined GLUK Debate Club.`,
      type: 'general',
      linkTab: 'members',
    });

    broadcastEvent('MEMBER_REGISTERED', activeMember);
  }

  const token = `token-${activeMember.id}-${Date.now()}`;
  res.json({ success: true, token, user: activeMember });
});

app.get('/api/auth/me', (req: Request, res: Response) => {
  const authHeader = req.headers.authorization;
  if (!authHeader) return res.status(401).json({ error: 'Unauthorized' });

  const token = authHeader.replace('Bearer ', '').trim();
  // Format token-{id}-{timestamp}
  const match = token.match(/^token-(.+)-\d+$/);
  if (!match) return res.status(401).json({ error: 'Invalid token' });

  const userId = match[1];
  const user = dbState.users.find((u) => u.id === userId);
  if (!user) return res.status(404).json({ error: 'User session not found' });

  res.json(user);
});

app.post('/api/auth/logout', (_req: Request, res: Response) => {
  res.json({ success: true });
});

// =========================================================================
// 3. MEMBERS ENDPOINTS (GET, POST / Upsert, Submit M-Pesa, Verify Dues)
// =========================================================================
app.get('/api/members', async (_req: Request, res: Response) => {
  if (sql) {
    try {
      const rows = await sql`SELECT * FROM members ORDER BY full_name ASC`;
      if (rows.length > 0) {
        const mapped: Member[] = rows.map((r: any) => ({
          id: r.id,
          fullName: r.full_name,
          studentId: r.student_id,
          email: r.email,
          phone: r.phone || '',
          role: r.role,
          executivePosition: r.executive_position || undefined,
          yearOfStudy: r.year_of_study,
          faculty: r.faculty,
          membershipStatus: r.membership_status,
          duesAmountKes: Number(r.dues_amount_kes),
          mpesaRef: r.mpesa_ref || undefined,
          joinedDate: r.joined_date,
          attendanceRate: Number(r.attendance_rate),
          debatesAttendedCount: Number(r.debates_attended_count),
          totalDebatesCount: Number(r.total_debates_count),
          speakerPointsAvg: Number(r.speaker_points_avg),
          bio: r.bio || undefined,
          alumniOccupation: r.alumni_occupation || undefined,
          alumniOrganization: r.alumni_organization || undefined,
        }));
        // Update database.json in-memory
        dbState.users = mapped;
        saveDatabaseToFile();
        return res.json(mapped);
      }
    } catch (err) {
      console.warn('Neon query failed for members, using root database.json:', err);
    }
  }
  res.json(dbState.users);
});

app.post('/api/members', async (req: Request, res: Response) => {
  const m = req.body;
  if (!m || !m.id) return res.status(400).json({ error: 'Invalid member data' });

  if (sql) {
    try {
      await sql`
        INSERT INTO members (
          id, full_name, student_id, email, phone, role, executive_position,
          year_of_study, faculty, membership_status, dues_amount_kes, mpesa_ref,
          joined_date, attendance_rate, debates_attended_count, total_debates_count,
          speaker_points_avg, bio, alumni_occupation, alumni_organization
        ) VALUES (
          ${m.id}, ${m.fullName}, ${m.studentId}, ${m.email}, ${m.phone || ''}, ${m.role},
          ${m.executivePosition || null}, ${m.yearOfStudy}, ${m.faculty}, ${m.membershipStatus},
          ${m.duesAmountKes ?? 500}, ${m.mpesaRef || null}, ${m.joinedDate || new Date().toISOString().split('T')[0]},
          ${m.attendanceRate ?? 0}, ${m.debatesAttendedCount ?? 0}, ${m.totalDebatesCount ?? 0},
          ${m.speakerPointsAvg ?? 70}, ${m.bio || null}, ${m.alumniOccupation || null}, ${m.alumniOrganization || null}
        )
        ON CONFLICT (id) DO UPDATE SET
          full_name = EXCLUDED.full_name,
          membership_status = EXCLUDED.membership_status,
          mpesa_ref = EXCLUDED.mpesa_ref,
          attendance_rate = EXCLUDED.attendance_rate,
          debates_attended_count = EXCLUDED.debates_attended_count,
          total_debates_count = EXCLUDED.total_debates_count,
          speaker_points_avg = EXCLUDED.speaker_points_avg,
          phone = EXCLUDED.phone,
          faculty = EXCLUDED.faculty,
          year_of_study = EXCLUDED.year_of_study,
          role = EXCLUDED.role,
          executive_position = EXCLUDED.executive_position,
          bio = EXCLUDED.bio;
      `;
    } catch (err) {
      console.error('Error upserting member to Neon:', err);
    }
  }

  const idx = dbState.users.findIndex((item) => item.id === m.id);
  if (idx >= 0) dbState.users[idx] = { ...dbState.users[idx], ...m };
  else dbState.users.unshift(m);

  saveDatabaseToFile();
  broadcastEvent('MEMBER_UPDATED', m);
  res.json({ success: true, member: m });
});

// Member submits M-Pesa transaction code for semester dues
app.post('/api/members/submit-mpesa', async (req: Request, res: Response) => {
  const { memberId, mpesaCode } = req.body;
  if (!memberId || !mpesaCode) return res.status(400).json({ error: 'Missing memberId or mpesaCode' });

  const member = dbState.users.find((u) => u.id === memberId);
  if (!member) return res.status(404).json({ error: 'Member not found' });

  member.mpesaRef = mpesaCode.toUpperCase().trim();
  saveDatabaseToFile();

  if (sql) {
    try {
      await sql`UPDATE members SET mpesa_ref = ${member.mpesaRef} WHERE id = ${memberId}`;
    } catch (e) {
      console.warn('Neon update mpesa_ref error:', e);
    }
  }

  pushNotification({
    targetUserId: 'all',
    title: 'M-Pesa Dues Verification Pending',
    message: `${member.fullName} (${member.studentId}) submitted M-Pesa code ${member.mpesaRef} for approval.`,
    type: 'duty_delegated',
    linkTab: 'finances',
  });

  broadcastEvent('MPESA_SUBMITTED', { memberId, mpesaRef: member.mpesaRef });
  res.json({ success: true, member });
});

// Finance Secretary verifies member payment
app.post('/api/members/verify-dues', async (req: Request, res: Response) => {
  const { memberId, mpesaRef, verifiedBy } = req.body;
  if (!memberId) return res.status(400).json({ error: 'Missing memberId' });

  const member = dbState.users.find((u) => u.id === memberId);
  if (!member) return res.status(404).json({ error: 'Member not found' });

  member.membershipStatus = 'Paid';
  if (mpesaRef) member.mpesaRef = mpesaRef.toUpperCase().trim();

  // Create Income transaction in KES
  const txn: FinancialTransaction = {
    id: `txn-dues-${Date.now()}`,
    date: new Date().toISOString().split('T')[0],
    type: 'Income',
    category: 'Semester Dues',
    amountKes: member.duesAmountKes || 500,
    description: `Semester membership dues clearance for ${member.fullName} (${member.studentId})`,
    referenceCode: member.mpesaRef || `MPESA-${Date.now().toString().slice(-6)}`,
    recordedBy: verifiedBy || 'Mercy Wangari (Finance Sec)',
    status: 'Verified',
  };

  dbState.transactions.unshift(txn);
  saveDatabaseToFile();

  if (sql) {
    try {
      await sql`
        UPDATE members SET membership_status = 'Paid', mpesa_ref = ${member.mpesaRef || null} WHERE id = ${memberId};
      `;
      await sql`
        INSERT INTO financial_transactions (
          id, date, type, category, amount_kes, description, reference_code, recorded_by, status
        ) VALUES (
          ${txn.id}, ${txn.date}, ${txn.type}, ${txn.category}, ${txn.amountKes},
          ${txn.description}, ${txn.referenceCode}, ${txn.recordedBy}, ${txn.status}
        )
        ON CONFLICT (id) DO NOTHING;
      `;
    } catch (e) {
      console.warn('Neon verify dues error:', e);
    }
  }

  pushNotification({
    targetUserId: member.id,
    title: 'Semester Dues Approved!',
    message: `Your KES ${txn.amountKes} dues payment has been verified (Ref: ${txn.referenceCode}). You have official debating clearance!`,
    type: 'dues_verified',
    linkTab: 'member-home',
  });

  broadcastEvent('DUES_VERIFIED', { member, transaction: txn });
  res.json({ success: true, member, transaction: txn });
});

// =========================================================================
// 4. FINANCIAL TRANSACTIONS ENDPOINTS (GET, POST)
// =========================================================================
app.get('/api/transactions', async (_req: Request, res: Response) => {
  if (sql) {
    try {
      const rows = await sql`SELECT * FROM financial_transactions ORDER BY date DESC`;
      if (rows.length > 0) {
        const mapped: FinancialTransaction[] = rows.map((r: any) => ({
          id: r.id,
          date: r.date,
          type: r.type,
          category: r.category,
          amountKes: Number(r.amount_kes),
          description: r.description,
          referenceCode: r.reference_code,
          recordedBy: r.recorded_by,
          status: r.status,
        }));
        dbState.transactions = mapped;
        saveDatabaseToFile();
        return res.json(mapped);
      }
    } catch (err) {
      console.warn('Neon query error for transactions:', err);
    }
  }
  res.json(dbState.transactions);
});

app.post('/api/transactions', async (req: Request, res: Response) => {
  const t = req.body;
  if (!t || !t.id) return res.status(400).json({ error: 'Invalid transaction' });

  if (sql) {
    try {
      await sql`
        INSERT INTO financial_transactions (
          id, date, type, category, amount_kes, description, reference_code, recorded_by, status
        ) VALUES (
          ${t.id}, ${t.date}, ${t.type}, ${t.category}, ${t.amountKes}, ${t.description},
          ${t.referenceCode}, ${t.recordedBy}, ${t.status || 'Verified'}
        )
        ON CONFLICT (id) DO UPDATE SET
          amount_kes = EXCLUDED.amount_kes,
          status = EXCLUDED.status,
          reference_code = EXCLUDED.reference_code;
      `;
    } catch (err) {
      console.error('Error saving transaction in Neon:', err);
    }
  }

  const idx = dbState.transactions.findIndex((x) => x.id === t.id);
  if (idx >= 0) dbState.transactions[idx] = t;
  else dbState.transactions.unshift(t);

  saveDatabaseToFile();
  broadcastEvent('TRANSACTION_CREATED', t);
  res.json({ success: true, transaction: t });
});

// =========================================================================
// 5. DEBATE SESSIONS ENDPOINTS (GET, POST, PUT /:id)
// =========================================================================
app.get('/api/debates', async (_req: Request, res: Response) => {
  if (sql) {
    try {
      const rows = await sql`SELECT * FROM debate_sessions ORDER BY date DESC`;
      if (rows.length > 0) {
        const mapped: DebateSession[] = rows.map((r: any) => ({
          id: r.id,
          title: r.title,
          motion: r.motion,
          motionInfoSlide: r.motion_info_slide || undefined,
          category: r.category,
          format: r.format,
          date: r.date,
          time: r.time,
          status: r.status,
          googleMeetLink: r.google_meet_link || '',
          winningTeam: r.winning_team || undefined,
          adjudicators: r.adjudicators || [],
          teams: r.teams || [],
          summaryClashes: r.summary_clashes || [],
          attendeeIds: r.attendee_ids || [],
          transcript: r.transcript || [],
        }));
        dbState.debates = mapped;
        saveDatabaseToFile();
        return res.json(mapped);
      }
    } catch (err) {
      console.warn('Neon query error for debates:', err);
    }
  }
  res.json(dbState.debates);
});

app.post('/api/debates', async (req: Request, res: Response) => {
  const d = req.body;
  if (!d || !d.id) return res.status(400).json({ error: 'Invalid debate session data' });

  if (sql) {
    try {
      await sql`
        INSERT INTO debate_sessions (
          id, title, motion, motion_info_slide, category, format, date, time,
          status, google_meet_link, winning_team, adjudicators, teams,
          summary_clashes, attendee_ids, transcript
        ) VALUES (
          ${d.id}, ${d.title}, ${d.motion}, ${d.motionInfoSlide || null}, ${d.category},
          ${d.format}, ${d.date}, ${d.time}, ${d.status || 'Scheduled'},
          ${d.googleMeetLink || ''}, ${d.winningTeam || null},
          ${JSON.stringify(d.adjudicators || [])}::jsonb,
          ${JSON.stringify(d.teams || [])}::jsonb,
          ${JSON.stringify(d.summaryClashes || [])}::jsonb,
          ${JSON.stringify(d.attendeeIds || [])}::jsonb,
          ${JSON.stringify(d.transcript || [])}::jsonb
        )
        ON CONFLICT (id) DO UPDATE SET
          title = EXCLUDED.title,
          motion = EXCLUDED.motion,
          status = EXCLUDED.status,
          winning_team = EXCLUDED.winning_team,
          transcript = EXCLUDED.transcript;
      `;
    } catch (err) {
      console.error('Error creating debate session in Neon:', err);
    }
  }

  const idx = dbState.debates.findIndex((item) => item.id === d.id);
  if (idx >= 0) dbState.debates[idx] = d;
  else dbState.debates.unshift(d);

  saveDatabaseToFile();
  broadcastEvent('DEBATE_UPDATED', d);
  res.json({ success: true, debate: d });
});

app.put('/api/debates/:id', async (req: Request, res: Response) => {
  const { id } = req.params;
  const d = req.body;

  if (sql) {
    try {
      await sql`
        UPDATE debate_sessions
        SET
          title = ${d.title},
          motion = ${d.motion},
          motion_info_slide = ${d.motionInfoSlide || null},
          category = ${d.category},
          format = ${d.format},
          date = ${d.date},
          time = ${d.time},
          status = ${d.status},
          google_meet_link = ${d.googleMeetLink || ''},
          winning_team = ${d.winningTeam || null},
          adjudicators = ${JSON.stringify(d.adjudicators || [])}::jsonb,
          teams = ${JSON.stringify(d.teams || [])}::jsonb,
          summary_clashes = ${JSON.stringify(d.summaryClashes || [])}::jsonb,
          attendee_ids = ${JSON.stringify(d.attendeeIds || [])}::jsonb,
          transcript = ${JSON.stringify(d.transcript || [])}::jsonb
        WHERE id = ${id};
      `;
    } catch (err) {
      console.error(`Error updating debate session ${id} in Neon:`, err);
    }
  }

  const idx = dbState.debates.findIndex((item) => item.id === id);
  if (idx >= 0) dbState.debates[idx] = { ...dbState.debates[idx], ...d };
  else dbState.debates.unshift(d);

  // If archiving round, award attendance and update speaker stats for participants
  if (d.status === 'Archived') {
    dbState.users = dbState.users.map((member) => {
      // If member attended or spoke
      if (d.attendeeIds?.includes(member.id)) {
        const nextAttended = member.debatesAttendedCount + 1;
        const nextTotal = Math.max(member.totalDebatesCount + 1, nextAttended);
        const nextRate = Math.min(100, Math.round((nextAttended / nextTotal) * 100));
        return {
          ...member,
          debatesAttendedCount: nextAttended,
          totalDebatesCount: nextTotal,
          attendanceRate: nextRate,
        };
      }
      return member;
    });

    pushNotification({
      targetUserId: 'all',
      title: 'Debate Round Archived',
      message: `Round "${d.title}" concluded! Victorious: ${d.winningTeam || 'Government'}. Ballots filed in Motion Vault.`,
      type: 'debate_round',
      linkTab: 'motion-vault',
    });
  }

  saveDatabaseToFile();
  broadcastEvent('DEBATE_UPDATED', d);
  res.json({ success: true, debate: d });
});

// =========================================================================
// 6. EXECUTIVE AGENDAS & LOGISTICS (GET, POST, PUT /:id)
// =========================================================================
app.get('/api/agendas', async (_req: Request, res: Response) => {
  if (sql) {
    try {
      const rows = await sql`SELECT * FROM executive_agendas ORDER BY date DESC`;
      if (rows.length > 0) {
        const mapped: AgendaItem[] = rows.map((r: any) => ({
          id: r.id,
          meetingTitle: r.meeting_title,
          date: r.date,
          time: r.time,
          location: r.location,
          status: r.status,
          chairperson: r.chairperson,
          agendaItems: r.agenda_items || [],
          logisticsChecklist: r.logistics_checklist || [],
          minutesSummary: r.minutes_summary || undefined,
        }));
        dbState.agendas = mapped;
        saveDatabaseToFile();
        return res.json(mapped);
      }
    } catch (err) {
      console.warn('Neon query error for agendas:', err);
    }
  }
  res.json(dbState.agendas);
});

app.post('/api/agendas', async (req: Request, res: Response) => {
  const a = req.body;
  if (!a || !a.id) return res.status(400).json({ error: 'Invalid agenda data' });

  if (sql) {
    try {
      await sql`
        INSERT INTO executive_agendas (
          id, meeting_title, date, time, location, status, chairperson,
          agenda_items, logistics_checklist, minutes_summary
        ) VALUES (
          ${a.id}, ${a.meetingTitle}, ${a.date}, ${a.time}, ${a.location},
          ${a.status || 'Upcoming'}, ${a.chairperson},
          ${JSON.stringify(a.agendaItems || [])}::jsonb,
          ${JSON.stringify(a.logisticsChecklist || [])}::jsonb,
          ${a.minutesSummary || null}
        )
        ON CONFLICT (id) DO UPDATE SET
          meeting_title = EXCLUDED.meeting_title,
          status = EXCLUDED.status,
          agenda_items = EXCLUDED.agenda_items,
          logistics_checklist = EXCLUDED.logistics_checklist,
          minutes_summary = EXCLUDED.minutes_summary;
      `;
    } catch (err) {
      console.error('Error inserting agenda in Neon:', err);
    }
  }

  const idx = dbState.agendas.findIndex((item) => item.id === a.id);
  if (idx >= 0) dbState.agendas[idx] = a;
  else dbState.agendas.unshift(a);

  saveDatabaseToFile();
  broadcastEvent('AGENDA_UPDATED', a);
  res.json({ success: true, agenda: a });
});

app.put('/api/agendas/:id', async (req: Request, res: Response) => {
  const { id } = req.params;
  const a = req.body;

  if (sql) {
    try {
      await sql`
        UPDATE executive_agendas
        SET
          meeting_title = ${a.meetingTitle},
          date = ${a.date},
          time = ${a.time},
          location = ${a.location},
          status = ${a.status},
          chairperson = ${a.chairperson},
          agenda_items = ${JSON.stringify(a.agendaItems || [])}::jsonb,
          logisticsChecklist = ${JSON.stringify(a.logisticsChecklist || [])}::jsonb,
          minutes_summary = ${a.minutesSummary || null}
        WHERE id = ${id};
      `;
    } catch (err) {
      console.error(`Error updating agenda ${id} in Neon:`, err);
    }
  }

  const idx = dbState.agendas.findIndex((item) => item.id === id);
  if (idx >= 0) dbState.agendas[idx] = { ...dbState.agendas[idx], ...a };
  else dbState.agendas.unshift(a);

  saveDatabaseToFile();
  broadcastEvent('AGENDA_UPDATED', a);
  res.json({ success: true, agenda: a });
});

// =========================================================================
// 7. ANNOUNCEMENTS ENDPOINTS (GET, POST)
// =========================================================================
app.get('/api/announcements', async (_req: Request, res: Response) => {
  if (sql) {
    try {
      const rows = await sql`SELECT * FROM announcements ORDER BY publish_date DESC`;
      if (rows.length > 0) {
        const mapped: Announcement[] = rows.map((r: any) => ({
          id: r.id,
          title: r.title,
          content: r.content,
          author: r.author,
          authorRole: r.author_role,
          publishDate: r.publish_date,
          priority: r.priority,
          category: r.category,
          pinned: Boolean(r.pinned),
        }));
        dbState.announcements = mapped;
        saveDatabaseToFile();
        return res.json(mapped);
      }
    } catch (err) {
      console.warn('Neon query error for announcements:', err);
    }
  }
  res.json(dbState.announcements);
});

app.post('/api/announcements', async (req: Request, res: Response) => {
  const ann = req.body;
  if (!ann || !ann.id) return res.status(400).json({ error: 'Invalid announcement' });

  if (sql) {
    try {
      await sql`
        INSERT INTO announcements (
          id, title, content, author, author_role, publish_date, priority, category, pinned
        ) VALUES (
          ${ann.id}, ${ann.title}, ${ann.content}, ${ann.author}, ${ann.authorRole},
          ${ann.publishDate}, ${ann.priority}, ${ann.category}, ${Boolean(ann.pinned)}
        )
        ON CONFLICT (id) DO UPDATE SET
          title = EXCLUDED.title,
          content = EXCLUDED.content,
          priority = EXCLUDED.priority,
          pinned = EXCLUDED.pinned;
      `;
    } catch (err) {
      console.error('Error saving announcement in Neon:', err);
    }
  }

  const idx = dbState.announcements.findIndex((x) => x.id === ann.id);
  if (idx >= 0) dbState.announcements[idx] = ann;
  else dbState.announcements.unshift(ann);

  pushNotification({
    targetUserId: 'all',
    title: ann.title,
    message: `${ann.authorRole} ${ann.author}: ${ann.content.slice(0, 100)}...`,
    type: 'announcement',
    linkTab: 'announcements',
  });

  saveDatabaseToFile();
  broadcastEvent('ANNOUNCEMENT_CREATED', ann);
  res.json({ success: true, announcement: ann });
});

// =========================================================================
// 8. CALENDAR ACTIVITIES ENDPOINTS (GET, POST)
// =========================================================================
app.get('/api/events', async (_req: Request, res: Response) => {
  if (sql) {
    try {
      const rows = await sql`SELECT * FROM calendar_events ORDER BY date ASC`;
      if (rows.length > 0) {
        const mapped: CalendarEvent[] = rows.map((r: any) => ({
          id: r.id,
          title: r.title,
          date: r.date,
          startTime: r.start_time,
          endTime: r.end_time,
          location: r.location,
          googleMeetUrl: r.google_meet_url || undefined,
          eventType: r.event_type,
          description: r.description,
          leadCoordinator: r.lead_coordinator,
        }));
        dbState.events = mapped;
        saveDatabaseToFile();
        return res.json(mapped);
      }
    } catch (err) {
      console.warn('Neon query error for events:', err);
    }
  }
  res.json(dbState.events);
});

app.post('/api/events', async (req: Request, res: Response) => {
  const event = req.body;
  if (!event || !event.id) return res.status(400).json({ error: 'Invalid event data' });

  if (sql) {
    try {
      await sql`
        INSERT INTO calendar_events (
          id, title, date, start_time, end_time, location, google_meet_url,
          event_type, description, lead_coordinator
        ) VALUES (
          ${event.id}, ${event.title}, ${event.date}, ${event.startTime},
          ${event.endTime}, ${event.location}, ${event.googleMeetUrl || null},
          ${event.eventType}, ${event.description}, ${event.leadCoordinator}
        )
        ON CONFLICT (id) DO UPDATE SET
          title = EXCLUDED.title,
          date = EXCLUDED.date,
          start_time = EXCLUDED.start_time,
          end_time = EXCLUDED.end_time,
          location = EXCLUDED.location,
          google_meet_url = EXCLUDED.google_meet_url;
      `;
    } catch (err) {
      console.error('Error inserting calendar event to Neon:', err);
    }
  }

  const idx = dbState.events.findIndex((x) => x.id === event.id);
  if (idx >= 0) dbState.events[idx] = event;
  else dbState.events.push(event);

  pushNotification({
    targetUserId: 'all',
    title: `New Event: ${event.title}`,
    message: `${event.eventType} on ${event.date} at ${event.startTime}. Location: ${event.location}.`,
    type: 'general',
    linkTab: 'calendar',
  });

  saveDatabaseToFile();
  broadcastEvent('EVENT_CREATED', event);
  res.json({ success: true, event });
});

// =========================================================================
// 9. MENTORSHIP HUB ENDPOINTS (GET, POST)
// =========================================================================
app.get('/api/mentorship', async (_req: Request, res: Response) => {
  if (sql) {
    try {
      const rows = await sql`SELECT * FROM mentorship_notes ORDER BY date DESC`;
      if (rows.length > 0) {
        const mapped: AlumniMentorshipNote[] = rows.map((r: any) => ({
          id: r.id,
          alumniId: r.alumni_id,
          alumniName: r.alumni_name,
          menteeId: r.mentee_id,
          menteeName: r.mentee_name,
          topic: r.topic,
          date: r.date,
          adviceSummary: r.advice_summary,
          status: r.status,
        }));
        dbState.mentorshipNotes = mapped;
        saveDatabaseToFile();
        return res.json(mapped);
      }
    } catch (err) {
      console.warn('Neon query error for mentorship_notes:', err);
    }
  }
  res.json(dbState.mentorshipNotes);
});

app.post('/api/mentorship', async (req: Request, res: Response) => {
  const note = req.body;
  if (!note || !note.id) return res.status(400).json({ error: 'Invalid mentorship note' });

  if (sql) {
    try {
      await sql`
        INSERT INTO mentorship_notes (
          id, alumni_id, alumni_name, mentee_id, mentee_name, topic, date,
          advice_summary, status
        ) VALUES (
          ${note.id}, ${note.alumniId}, ${note.alumniName}, ${note.menteeId},
          ${note.menteeName}, ${note.topic}, ${note.date}, ${note.adviceSummary},
          ${note.status || 'Active'}
        )
        ON CONFLICT (id) DO UPDATE SET
          topic = EXCLUDED.topic,
          advice_summary = EXCLUDED.advice_summary,
          status = EXCLUDED.status;
      `;
    } catch (err) {
      console.error('Error inserting mentorship note to Neon:', err);
    }
  }

  const idx = dbState.mentorshipNotes.findIndex((x) => x.id === note.id);
  if (idx >= 0) dbState.mentorshipNotes[idx] = note;
  else dbState.mentorshipNotes.unshift(note);

  pushNotification({
    targetUserId: note.alumniId,
    title: 'New Mentorship Request',
    message: `${note.menteeName} requested coaching on "${note.topic}".`,
    type: 'duty_delegated',
    linkTab: 'members',
  });

  saveDatabaseToFile();
  broadcastEvent('MENTORSHIP_UPDATED', note);
  res.json({ success: true, note });
});

// =========================================================================
// 10. NOTIFICATIONS ENDPOINTS (GET, POST /:id/read)
// =========================================================================
app.get('/api/notifications', (req: Request, res: Response) => {
  const authHeader = req.headers.authorization;
  let targetId = 'all';

  if (authHeader) {
    const token = authHeader.replace('Bearer ', '').trim();
    const match = token.match(/^token-(.+)-\d+$/);
    if (match) targetId = match[1];
  }

  const userNotifs = dbState.notifications.filter(
    (n) => n.targetUserId === 'all' || n.targetUserId === targetId
  );
  res.json(userNotifs);
});

app.post('/api/notifications/:id/read', (req: Request, res: Response) => {
  const { id } = req.params;
  const notif = dbState.notifications.find((n) => n.id === id);
  if (notif) notif.isRead = true;
  saveDatabaseToFile();
  res.json({ success: true });
});

// =========================================================================
// 11. VITE SPA & STATIC ASSET SERVER
// =========================================================================
async function startServer() {
  const PORT = process.env.DEBATEHUB_PORT
    ? parseInt(process.env.DEBATEHUB_PORT, 10)
    : process.env.PORT
      ? parseInt(process.env.PORT, 10)
      : 3000;

  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: {
        middlewareMode: true,
        hmr: process.env.DISABLE_HMR !== 'true',
        allowedHosts: true as true,
      },
      appType: 'spa',
    });
    app.use(vite.middlewares);
    // Fallback for SPA routing under /DebateHub in dev mode
    app.get(['/DebateHub', '/DebateHub/*', '/debatehub', '/debatehub/*'], async (req, res, next) => {
      try {
        const url = req.originalUrl;
        let template = fs.readFileSync(path.resolve(__dirname, 'index.html'), 'utf-8');
        template = await vite.transformIndexHtml(url, template);
        res.status(200).set({ 'Content-Type': 'text/html' }).end(template);
      } catch (e) {
        vite.ssrFixStacktrace(e as Error);
        next(e);
      }
    });
  } else {
    const distPath = path.join(__dirname, 'dist');
    app.use('/DebateHub', express.static(distPath));
    app.use('/debatehub', express.static(distPath));
    app.use(express.static(distPath));
    app.get(['/DebateHub', '/DebateHub/*', '/debatehub', '/debatehub/*', '*'], (_req: Request, res: Response) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`GLUK Debate Club Server active at http://0.0.0.0:${PORT}`);
  });
}

startServer();

