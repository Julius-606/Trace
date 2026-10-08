
import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.resolve(process.cwd(), '.env') });
dotenv.config({ path: path.resolve(process.cwd(), '..', '.env') });

const databaseUrl =
  process.env.DEBATEHUB_NEON_DATABASE_URL ||
  process.env.DEBATEHUB_DATABASE_URL;

export const isNeonConfigured = Boolean(databaseUrl && databaseUrl.startsWith('postgres'));

// Export Neon SQL client if configured
export const sql = isNeonConfigured && databaseUrl ? neon(databaseUrl) : null;

/**
 * Initializes the required PostgreSQL schema in Neon.
 */
export async function initializeNeonTables(): Promise<{ success: boolean; message: string }> {
  if (!sql) {
    return {
      success: false,
      message: 'DEBATEHUB_NEON_DATABASE_URL environment variable is not set. Add it in Hugging Face Space Secrets or .env file.',
    };
  }

  try {
    // 1. Members table
    await sql`
      CREATE TABLE IF NOT EXISTS members (
        id VARCHAR(64) PRIMARY KEY,
        full_name VARCHAR(255) NOT NULL,
        student_id VARCHAR(64) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        phone VARCHAR(64),
        role VARCHAR(32) NOT NULL DEFAULT 'member',
        executive_position VARCHAR(128),
        year_of_study VARCHAR(32) NOT NULL DEFAULT 'Year 1',
        faculty VARCHAR(255) NOT NULL,
        membership_status VARCHAR(32) NOT NULL DEFAULT 'Pending',
        dues_amount_kes NUMERIC NOT NULL DEFAULT 500,
        mpesa_ref VARCHAR(64),
        joined_date VARCHAR(32) NOT NULL,
        attendance_rate NUMERIC NOT NULL DEFAULT 0,
        debates_attended_count INTEGER NOT NULL DEFAULT 0,
        total_debates_count INTEGER NOT NULL DEFAULT 0,
        speaker_points_avg NUMERIC NOT NULL DEFAULT 70,
        bio TEXT,
        alumni_occupation VARCHAR(255),
        alumni_organization VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      );
    `;

    // 2. Financial Transactions table
    await sql`
      CREATE TABLE IF NOT EXISTS financial_transactions (
        id VARCHAR(64) PRIMARY KEY,
        date VARCHAR(32) NOT NULL,
        type VARCHAR(16) NOT NULL,
        category VARCHAR(64) NOT NULL,
        amount_kes NUMERIC NOT NULL,
        description TEXT NOT NULL,
        reference_code VARCHAR(64) NOT NULL,
        recorded_by VARCHAR(255) NOT NULL,
        status VARCHAR(32) NOT NULL DEFAULT 'Verified',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      );
    `;

    // 3. Debate Sessions table
    await sql`
      CREATE TABLE IF NOT EXISTS debate_sessions (
        id VARCHAR(64) PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        motion TEXT NOT NULL,
        motion_info_slide TEXT,
        category VARCHAR(64) NOT NULL,
        format VARCHAR(64) NOT NULL,
        date VARCHAR(32) NOT NULL,
        time VARCHAR(64) NOT NULL,
        status VARCHAR(32) NOT NULL DEFAULT 'Scheduled',
        google_meet_link TEXT,
        winning_team VARCHAR(128),
        adjudicators JSONB DEFAULT '[]'::jsonb,
        teams JSONB DEFAULT '[]'::jsonb,
        summary_clashes JSONB DEFAULT '[]'::jsonb,
        attendee_ids JSONB DEFAULT '[]'::jsonb,
        transcript JSONB DEFAULT '[]'::jsonb,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      );
    `;

    // 4. Executive Agendas table
    await sql`
      CREATE TABLE IF NOT EXISTS executive_agendas (
        id VARCHAR(64) PRIMARY KEY,
        meeting_title VARCHAR(255) NOT NULL,
        date VARCHAR(32) NOT NULL,
        time VARCHAR(64) NOT NULL,
        location VARCHAR(255) NOT NULL,
        status VARCHAR(32) NOT NULL DEFAULT 'Upcoming',
        chairperson VARCHAR(255) NOT NULL,
        agenda_items JSONB DEFAULT '[]'::jsonb,
        logistics_checklist JSONB DEFAULT '[]'::jsonb,
        minutes_summary TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      );
    `;

    // 5. Announcements table
    await sql`
      CREATE TABLE IF NOT EXISTS announcements (
        id VARCHAR(64) PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        content TEXT NOT NULL,
        author VARCHAR(255) NOT NULL,
        author_role VARCHAR(128) NOT NULL,
        publish_date VARCHAR(32) NOT NULL,
        priority VARCHAR(32) NOT NULL DEFAULT 'Normal',
        category VARCHAR(64) NOT NULL,
        pinned BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      );
    `;

    // 6. Calendar Events table
    await sql`
      CREATE TABLE IF NOT EXISTS calendar_events (
        id VARCHAR(64) PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        date VARCHAR(32) NOT NULL,
        start_time VARCHAR(32) NOT NULL,
        end_time VARCHAR(32) NOT NULL,
        location VARCHAR(255) NOT NULL,
        google_meet_url TEXT,
        event_type VARCHAR(64) NOT NULL,
        description TEXT NOT NULL,
        lead_coordinator VARCHAR(255) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      );
    `;

    // 7. Mentorship Notes table
    await sql`
      CREATE TABLE IF NOT EXISTS mentorship_notes (
        id VARCHAR(64) PRIMARY KEY,
        alumni_id VARCHAR(64) NOT NULL,
        alumni_name VARCHAR(255) NOT NULL,
        mentee_id VARCHAR(64) NOT NULL,
        mentee_name VARCHAR(255) NOT NULL,
        topic VARCHAR(255) NOT NULL,
        date VARCHAR(32) NOT NULL,
        advice_summary TEXT NOT NULL,
        status VARCHAR(32) NOT NULL DEFAULT 'Active',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      );
    `;

    return {
      success: true,
      message: 'Neon PostgreSQL tables initialized successfully (members, transactions, debates, agendas, announcements, events, mentorship_notes).',
    };
  } catch (error: any) {
    console.error('Error initializing Neon tables:', error);
    return {
      success: false,
      message: `Failed to initialize Neon schema: ${error.message}`,
    };
  }
}
