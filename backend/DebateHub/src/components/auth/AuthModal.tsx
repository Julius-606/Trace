
import React, { useState } from 'react';
import { GlukDebateLogo } from '../common/GlukDebateLogo';
import { useAuth } from '../../contexts/AuthContext';
import {
  Lock,
  Mail,
  User,
  GraduationCap,
  Shield,
  Phone,
  ArrowRight,
  Sparkles,
  X,
  AlertCircle,
  Database,
  CheckCircle2,
} from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  isFreshDatabase?: boolean;
  onSeedTemplates?: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  isFreshDatabase = false,
  onSeedTemplates,
}) => {
  const { loginWithCredentials, registerAccount, loginWithGoogle } = useAuth();
  const [mode, setMode] = useState<'login' | 'signup'>(isFreshDatabase ? 'signup' : 'login');

  // Form states
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [studentId, setStudentId] = useState('');
  const [phone, setPhone] = useState('');
  const [faculty, setFaculty] = useState('Faculty of Arts and Social Sciences');
  const [yearOfStudy, setYearOfStudy] = useState<'Year 1' | 'Year 2' | 'Year 3' | 'Year 4' | 'Postgraduate' | 'Alumni'>('Year 1');
  const [role, setRole] = useState<'member' | 'executive' | 'alumni'>('member');
  const [executivePosition, setExecutivePosition] = useState<any>('President');

  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setLoading(true);

    try {
      await loginWithCredentials(email, password);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setLoading(true);

    try {
      await registerAccount({
        fullName,
        studentId,
        email,
        password,
        phone,
        faculty,
        yearOfStudy,
        role,
        executivePosition: role === 'executive' ? executivePosition : undefined,
      });
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md overflow-y-auto">
      <div className="w-full max-w-md my-8 rounded-2xl bg-slate-900 border border-slate-800 p-6 sm:p-7 shadow-2xl relative overflow-hidden">
        
        {/* Subtle accent glow */}
        <div className="absolute -top-12 left-1/2 -translate-x-1/2 w-48 h-48 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Close button */}
        {!isFreshDatabase && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}

        {/* Logo & Institution Header */}
        <div className="flex flex-col items-center text-center space-y-2 mb-6">
          <GlukDebateLogo size={52} />
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">
              Great Lakes University of Kisumu
            </h2>
            <p className="text-xs text-amber-400 font-semibold tracking-wider uppercase">
              Debate Club Operations Portal
            </p>
          </div>
        </div>

        {/* Fresh database notification banner */}
        {isFreshDatabase && (
          <div className="mb-5 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs space-y-2">
            <div className="flex items-center gap-2 text-amber-300 font-bold">
              <Database className="w-4 h-4 text-amber-400 shrink-0" />
              <span>Fresh Database Initialized</span>
            </div>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              No accounts exist yet in <code className="font-mono text-amber-300">database.json</code>. Register your account below to create the founding profile!
            </p>
            {onSeedTemplates && (
              <button
                type="button"
                onClick={onSeedTemplates}
                className="text-[11px] text-amber-400 hover:text-amber-300 font-semibold underline underline-offset-2 block"
              >
                Or click here to load GLUK starter motions & sample profiles
              </button>
            )}
          </div>
        )}

        {/* Segmented Mode Switcher */}
        <div className="grid grid-cols-2 p-1 bg-slate-950 rounded-xl border border-slate-800 mb-5">
          <button
            type="button"
            onClick={() => {
              setMode('login');
              setErrorMsg(null);
            }}
            className={`py-2 text-xs font-semibold rounded-lg transition-all ${
              mode === 'login'
                ? 'bg-amber-400 text-slate-950 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('signup');
              setErrorMsg(null);
            }}
            className={`py-2 text-xs font-semibold rounded-lg transition-all ${
              mode === 'signup'
                ? 'bg-amber-400 text-slate-950 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Error notice */}
        {errorMsg && (
          <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* 1. LOGIN FORM */}
        {mode === 'login' && (
          <form onSubmit={handleLoginSubmit} className="space-y-4 text-xs">
            <div>
              <label className="text-slate-300 block mb-1 font-medium">Email Address</label>
              <div className="relative">
                <Mail className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  placeholder="e.g. student@gluk.ac.ke or julius@..."
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500/50"
                />
              </div>
            </div>

            <div>
              <label className="text-slate-300 block mb-1 font-medium">Password</label>
              <div className="relative">
                <Lock className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500/50"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-amber-400 hover:bg-amber-300 disabled:opacity-50 text-slate-950 font-bold rounded-lg transition-colors shadow-md flex items-center justify-center gap-1.5"
            >
              <span>{loading ? 'Signing in...' : 'Sign In to Portal'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>

            <div className="relative py-2">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-800" />
              </div>
              <div className="relative flex justify-center text-[10px] uppercase">
                <span className="bg-slate-900 px-2 text-slate-500 font-semibold">Or continue with</span>
              </div>
            </div>

            <button
              type="button"
              onClick={loginWithGoogle}
              className="w-full py-2 bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-200 rounded-lg font-semibold flex items-center justify-center gap-2 transition-colors"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
              <span>Sign in with Google</span>
            </button>
          </form>
        )}

        {/* 2. SIGN UP FORM */}
        {mode === 'signup' && (
          <form onSubmit={handleSignupSubmit} className="space-y-3.5 text-xs max-h-[460px] overflow-y-auto pr-1">
            <div>
              <label className="text-slate-300 block mb-1 font-medium">Full Legal Name</label>
              <div className="relative">
                <User className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  placeholder="e.g. Julius Gachoki"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500/50"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div>
                <label className="text-slate-300 block mb-1 font-medium">Student ID / Reg No.</label>
                <input
                  type="text"
                  placeholder="GLUK/BC/2026/0142"
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder:text-slate-600 font-mono text-[11px]"
                />
              </div>

              <div>
                <label className="text-slate-300 block mb-1 font-medium">Phone (M-Pesa / WhatsApp)</label>
                <input
                  type="tel"
                  placeholder="+254 7..."
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder:text-slate-600 text-[11px]"
                />
              </div>
            </div>

            <div>
              <label className="text-slate-300 block mb-1 font-medium">Email Address</label>
              <div className="relative">
                <Mail className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  placeholder="e.g. j.gachoki@gluk.ac.ke"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500/50"
                />
              </div>
            </div>

            <div>
              <label className="text-slate-300 block mb-1 font-medium">Create Password</label>
              <div className="relative">
                <Lock className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  placeholder="At least 6 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500/50"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div>
                <label className="text-slate-300 block mb-1 font-medium">Faculty / School</label>
                <select
                  value={faculty}
                  onChange={(e) => setFaculty(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white text-[11px]"
                >
                  <option value="Health Sciences & Community Development">Health Sciences</option>
                  <option value="Faculty of Arts and Social Sciences">Arts & Social Sciences</option>
                  <option value="Computing & Informatics">Computing & Informatics</option>
                  <option value="Business Administration & Economics">Business & Economics</option>
                  <option value="Education & Community Studies">Education</option>
                  <option value="Agribusiness & Food Security">Agribusiness</option>
                </select>
              </div>

              <div>
                <label className="text-slate-300 block mb-1 font-medium">Year of Study</label>
                <select
                  value={yearOfStudy}
                  onChange={(e) => setYearOfStudy(e.target.value as any)}
                  className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white text-[11px]"
                >
                  <option value="Year 1">Year 1 (Novice)</option>
                  <option value="Year 2">Year 2 (Junior)</option>
                  <option value="Year 3">Year 3 (Senior)</option>
                  <option value="Year 4">Year 4 (Finalist)</option>
                  <option value="Postgraduate">Postgraduate</option>
                  <option value="Alumni">Alumni Practitioner</option>
                </select>
              </div>
            </div>

            {/* Role selection */}
            <div>
              <label className="text-slate-300 block mb-1 font-medium">Club Role</label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => setRole('member')}
                  className={`py-1.5 px-2 text-[11px] font-semibold rounded-lg border text-center transition-all ${
                    role === 'member'
                      ? 'bg-blue-500/20 text-blue-300 border-blue-500/40'
                      : 'bg-slate-950 text-slate-400 border-slate-800'
                  }`}
                >
                  Debate Member
                </button>
                <button
                  type="button"
                  onClick={() => setRole('executive')}
                  className={`py-1.5 px-2 text-[11px] font-semibold rounded-lg border text-center transition-all ${
                    role === 'executive'
                      ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                      : 'bg-slate-950 text-slate-400 border-slate-800'
                  }`}
                >
                  Executive Team
                </button>
                <button
                  type="button"
                  onClick={() => setRole('alumni')}
                  className={`py-1.5 px-2 text-[11px] font-semibold rounded-lg border text-center transition-all ${
                    role === 'alumni'
                      ? 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                      : 'bg-slate-950 text-slate-400 border-slate-800'
                  }`}
                >
                  Alumni Mentor
                </button>
              </div>
            </div>

            {/* Position if Executive */}
            {role === 'executive' && (
              <div>
                <label className="text-slate-300 block mb-1 font-medium">Executive Portfolio</label>
                <select
                  value={executivePosition}
                  onChange={(e) => setExecutivePosition(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-amber-300 font-semibold text-[11px]"
                >
                  <option value="President">President</option>
                  <option value="Vice President (Internal)">Vice President (Internal)</option>
                  <option value="Vice President (External)">Vice President (External)</option>
                  <option value="Chief Adjudicator & Training Director">Chief Adjudicator & Training Director</option>
                  <option value="Finance & Treasury Secretary">Finance & Treasury Secretary</option>
                  <option value="Organizing & Logistics Secretary">Organizing & Logistics Secretary</option>
                  <option value="Public Relations & Tech Lead">Public Relations & Tech Lead</option>
                </select>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-2.5 bg-amber-400 hover:bg-amber-300 disabled:opacity-50 text-slate-950 font-bold rounded-lg transition-colors shadow-md flex items-center justify-center gap-1.5"
            >
              <span>{loading ? 'Registering Account...' : 'Create Account & Access Portal'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>
        )}

      </div>
    </div>
  );
};


