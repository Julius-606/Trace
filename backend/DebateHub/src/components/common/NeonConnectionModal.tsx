
import React, { useState, useEffect } from 'react';
import { Database, CheckCircle, AlertCircle, Copy, Check, RefreshCw, X, Server } from 'lucide-react';

interface NeonConnectionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NeonConnectionModal: React.FC<NeonConnectionModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [status, setStatus] = useState<{
    isConnected: boolean;
    configured: boolean;
    dbName?: string;
    version?: string;
    message?: string;
    error?: string;
  }>({ isConnected: false, configured: false });

  const [loading, setLoading] = useState(false);
  const [copiedSql, setCopiedSql] = useState(false);
  const [initResult, setInitResult] = useState<string | null>(null);

  const checkStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/db/status');
      const data = await res.json();
      setStatus(data);
    } catch (err: any) {
      setStatus({
        isConnected: false,
        configured: false,
        message: 'Could not reach backend API endpoint /api/db/status',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      checkStatus();
    }
  }, [isOpen]);

  const handleInitializeTables = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/db/init', { method: 'POST' });
      const data = await res.json();
      setInitResult(data.message || (data.success ? 'Tables initialized!' : 'Initialization error'));
      await checkStatus();
    } catch (err: any) {
      setInitResult(`Failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const sqlSchemaScript = `-- GLUK Debate Club - Neon PostgreSQL Schema
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
);`;

  const copySql = () => {
    navigator.clipboard.writeText(sqlSchemaScript);
    setCopiedSql(true);
    setTimeout(() => setCopiedSql(false), 3000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="w-full max-w-2xl rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-2xl space-y-5">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <span>Neon PostgreSQL Database Integration</span>
              </h2>
              <p className="text-xs text-slate-400">
                Serverless PostgreSQL provided by neon.tech
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Live Status Card */}
        <div className={`p-4 rounded-xl border text-xs space-y-2 ${
          status.isConnected
            ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-200'
            : 'bg-slate-950/60 border-slate-800 text-slate-300'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 font-semibold">
              {status.isConnected ? (
                <>
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <span className="text-emerald-400">Connected to Neon Database: {status.dbName}</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-4 h-4 text-amber-400" />
                  <span className="text-amber-300">
                    {status.configured ? 'Configured but connection failed' : 'Awaiting DEBATEHUB_NEON_DATABASE_URL'}
                  </span>
                </>
              )}
            </div>

            <button
              onClick={checkStatus}
              disabled={loading}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]"
            >
              <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
              <span>Test Connection</span>
            </button>
          </div>

          <p className="text-slate-400 text-[11px] leading-relaxed">
            {status.message || 'Status unknown'}
          </p>

          {status.version && (
            <div className="font-mono text-[10px] text-slate-500">
              {status.version}
            </div>
          )}
        </div>

        {/* Action: Initialize tables or instructions */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">
              How to configure your Neon PostgreSQL Database
            </span>
            <button
              onClick={copySql}
              className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-400 hover:text-amber-300"
            >
              {copiedSql ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedSql ? 'SQL Copied!' : 'Copy Schema SQL'}</span>
            </button>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 text-xs space-y-2 text-slate-300">
            <ol className="list-decimal pl-4 space-y-1.5 leading-relaxed text-slate-300">
              <li>
                Create a database project on <a href="https://neon.tech" target="_blank" rel="noopener noreferrer" className="text-amber-400 underline">neon.tech</a>.
              </li>
              <li>
                Copy the connection string (e.g. <code className="text-amber-300 bg-slate-900 px-1 py-0.5 rounded font-mono text-[10px]">postgresql://user:pass@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require</code>).
              </li>
              <li>
                Set the environment variable <code className="text-amber-300 bg-slate-900 px-1 py-0.5 rounded font-mono text-[10px]">DEBATEHUB_NEON_DATABASE_URL</code> in the shared backend <code className="font-mono text-[10px]">.env</code> file or Secrets.
              </li>
              <li>
                Click <strong>"Initialize PostgreSQL Tables"</strong> below (or run the copied SQL in Neon's SQL Editor).
              </li>
            </ol>
          </div>

          {initResult && (
            <div className="p-2.5 rounded-lg bg-slate-950 text-xs text-amber-300 font-mono">
              {initResult}
            </div>
          )}

          <div className="flex items-center justify-between pt-2">
            <button
              onClick={handleInitializeTables}
              disabled={loading || !status.configured}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white font-bold rounded-lg text-xs transition-colors shadow-md"
            >
              Initialize PostgreSQL Tables in Neon
            </button>

            <button
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium rounded-lg text-xs transition-colors"
            >
              Close
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};

