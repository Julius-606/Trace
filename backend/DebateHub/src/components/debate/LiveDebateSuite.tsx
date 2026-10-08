
import React, { useState, useEffect, useRef } from 'react';
import {
  DebateSession,
  Member,
  SpeakerScore,
} from '../../types';
import { debateBell } from '../../services/audioBell';
import {
  Mic,
  MicOff,
  Play,
  Pause,
  RotateCcw,
  Bell,
  Radio,
  ExternalLink,
  Users,
  CheckCircle2,
  Clock,
  Sparkles,
  Download,
  AlertCircle,
  Award,
} from 'lucide-react';
import confetti from 'canvas-confetti';

interface LiveDebateSuiteProps {
  session: DebateSession;
  allMembers: Member[];
  onUpdateSession: (updatedSession: DebateSession) => void;
  onSaveSessionToArchive: (session: DebateSession) => void;
}

const BP_ROLES = [
  { id: 'OG-1', team: 'Opening Government (OG)', role: 'Prime Minister (PM)' },
  { id: 'OO-1', team: 'Opening Opposition (OO)', role: 'Leader of Opposition (LO)' },
  { id: 'OG-2', team: 'Opening Government (OG)', role: 'Deputy Prime Minister (DPM)' },
  { id: 'OO-2', team: 'Opening Opposition (OO)', role: 'Deputy Leader of Opposition (DLO)' },
  { id: 'CG-1', team: 'Closing Government (CG)', role: 'Member of Government (MG)' },
  { id: 'CO-1', team: 'Closing Opposition (CO)', role: 'Member of Opposition (MO)' },
  { id: 'CG-2', team: 'Closing Government (CG)', role: 'Government Whip (GW)' },
  { id: 'CO-2', team: 'Closing Opposition (CO)', role: 'Opposition Whip (OW)' },
];

export const LiveDebateSuite: React.FC<LiveDebateSuiteProps> = ({
  session,
  allMembers,
  onUpdateSession,
  onSaveSessionToArchive,
}) => {
  // Active speaker state
  const [selectedRoleIdx, setSelectedRoleIdx] = useState(0);
  const activeRole = BP_ROLES[selectedRoleIdx];

  // Timer state (seconds)
  const [seconds, setSeconds] = useState(0);
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // POI state
  const [poiCountOffered, setPoiCountOffered] = useState(0);
  const [poiCountAccepted, setPoiCountAccepted] = useState(0);
  const [poiTimerSeconds, setPoiTimerSeconds] = useState(0);
  const [isPoiTimerRunning, setIsPoiTimerRunning] = useState(false);

  // Speech Recognition state
  const [isListening, setIsListening] = useState(false);
  const [transcriptLines, setTranscriptLines] = useState<
    { speaker: string; timestamp: string; text: string }[]
  >(session.transcript || []);
  const [currentSpeechDraft, setCurrentSpeechDraft] = useState('');
  const recognitionRef = useRef<any>(null);

  // Adjudication ballots state
  const [scores, setScores] = useState<Record<string, { matter: number; manner: number; method: number; feedback: string }>>({
    'OG-1': { matter: 31, manner: 31, method: 15, feedback: 'Strong economic models on currency devaluation.' },
    'OO-1': { matter: 30, manner: 32, method: 15, feedback: 'Pivotal rebuttal on state sovereignty.' },
    'OG-2': { matter: 29, manner: 30, method: 14, feedback: 'Good defense on liquidity reserves.' },
    'OO-2': { matter: 30, manner: 29, method: 14, feedback: 'Rebuilt case against inflation contagion.' },
    'CG-1': { matter: 32, manner: 30, method: 15, feedback: 'Great extension on cross-border informal traders.' },
    'CO-1': { matter: 31, manner: 31, method: 15, feedback: 'Sharp analysis of fiscal disparity.' },
    'CG-2': { matter: 30, manner: 30, method: 14, feedback: 'Solid whip crystallization.' },
    'CO-2': { matter: 31, manner: 30, method: 14, feedback: 'Effective comparative weighing.' },
  });

  // Track bell triggers so they don't fire repeatedly
  const bellsTriggeredRef = useRef<{ m1: boolean; m6: boolean; m7: boolean; m715: boolean }>({
    m1: false,
    m6: false,
    m7: false,
    m715: false,
  });

  // Setup Web Speech API if supported
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-KE'; // English (Kenya)

        recognition.onresult = (event: any) => {
          let interim = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              const finalText = event.results[i][0].transcript.trim();
              if (finalText) {
                const nowTimestamp = `${Math.floor(seconds / 60)}:${(seconds % 60).toString().padStart(2, '0')}`;
                setTranscriptLines((prev) => [
                  ...prev,
                  {
                    speaker: `${activeRole.team} - ${activeRole.role}`,
                    timestamp: nowTimestamp,
                    text: finalText,
                  },
                ]);
              }
            } else {
              interim += event.results[i][0].transcript;
            }
          }
          setCurrentSpeechDraft(interim);
        };

        recognition.onerror = (err: any) => {
          console.warn('Speech recognition status:', err.error);
          if (err.error === 'not-allowed') {
            setIsListening(false);
          }
        };

        recognition.onend = () => {
          if (isListening) {
            try {
              recognition.start();
            } catch (e) {
              setIsListening(false);
            }
          }
        };

        recognitionRef.current = recognition;
      } catch (e) {
        console.warn('Speech recognition not available', e);
      }
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [seconds, activeRole, isListening]);

  // Main Speech Timer
  useEffect(() => {
    if (isTimerRunning) {
      timerRef.current = setInterval(() => {
        setSeconds((s) => {
          const nextSec = s + 1;

          // Check bell rules:
          // 1:00 min -> 60s
          if (nextSec === 60 && !bellsTriggeredRef.current.m1) {
            debateBell.playSingleBell();
            bellsTriggeredRef.current.m1 = true;
          }
          // 6:00 min -> 360s
          if (nextSec === 360 && !bellsTriggeredRef.current.m6) {
            debateBell.playSingleBell();
            bellsTriggeredRef.current.m6 = true;
          }
          // 7:00 min -> 420s
          if (nextSec === 420 && !bellsTriggeredRef.current.m7) {
            debateBell.playDoubleBell();
            bellsTriggeredRef.current.m7 = true;
          }
          // 7:15 min -> 435s overtime
          if (nextSec === 435 && !bellsTriggeredRef.current.m715) {
            debateBell.playOvertimeBells();
            bellsTriggeredRef.current.m715 = true;
          }

          return nextSec;
        });
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isTimerRunning]);

  // POI stopwatch
  useEffect(() => {
    let pInterval: NodeJS.Timeout | null = null;
    if (isPoiTimerRunning) {
      pInterval = setInterval(() => {
        setPoiTimerSeconds((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (pInterval) clearInterval(pInterval);
    };
  }, [isPoiTimerRunning]);

  const toggleMicListening = () => {
    if (!recognitionRef.current) {
      // Simulate live input if browser doesn't have recognition
      simulateLiveGoogleMeetSpeech();
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (err) {
        simulateLiveGoogleMeetSpeech();
      }
    }
  };

  // Simulate audio capture directly from Google Meet session stream
  const simulateLiveGoogleMeetSpeech = () => {
    const simulationSnippets = [
      "Let us examine the counterfactual presented by the Deputy Leader of Opposition. If we don't centralize currency volatility reserves under the EAC treaty, small border markets in Busia and Namanga bear 100% of foreign exchange shocks.",
      "Point of Clarification: The opposition claims sovereign autonomy is compromised. But real sovereignty is the ability of your citizens to purchase essential medicine without 30% inflation penalties.",
      "Furthermore, when you analyze intra-regional trade metrics, non-tariff currency friction currently suppresses East African trade to under 15% of regional GDP. This motion fixes the fundamental mechanism.",
      "We in Closing Government extend this case by demonstrating how automated smart contracts on an EAC digital ledger eliminate customs clearance bribery entirely at port corridors.",
    ];

    const randomSnippet = simulationSnippets[Math.floor(Math.random() * simulationSnippets.length)];
    const timeFormatted = `${Math.floor(seconds / 60)}:${(seconds % 60).toString().padStart(2, '0')}`;

    setTranscriptLines((prev) => [
      ...prev,
      {
        speaker: `${activeRole.team} - ${activeRole.role}`,
        timestamp: timeFormatted,
        text: randomSnippet,
      },
    ]);
  };

  const handleResetTimer = () => {
    setIsTimerRunning(false);
    setSeconds(0);
    bellsTriggeredRef.current = { m1: false, m6: false, m7: false, m715: false };
  };

  // Determine speech status phase
  let phaseText = 'Protected Time (0:00 - 1:00) · No POIs';
  let phaseColor = 'text-slate-400';
  let isPoiAllowed = false;

  if (seconds >= 60 && seconds < 360) {
    phaseText = 'Open Debate (1:00 - 6:00) · POIs Allowed';
    phaseColor = 'text-emerald-400';
    isPoiAllowed = true;
  } else if (seconds >= 360 && seconds < 420) {
    phaseText = 'Protected Wrap-up (6:00 - 7:00) · 1 Min Warning';
    phaseColor = 'text-amber-400';
  } else if (seconds >= 420 && seconds < 435) {
    phaseText = 'Time Expired (7:00) · 15s Grace Period';
    phaseColor = 'text-rose-400 font-semibold';
  } else if (seconds >= 435) {
    phaseText = 'Overtime (7:15+) · Cease Speaking!';
    phaseColor = 'text-red-500 font-bold animate-pulse';
  }

  const formatTime = (totalSec: number) => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleFinalizeAndArchive = () => {
    confetti({
      particleCount: 100,
      spread: 80,
      origin: { y: 0.6 },
    });

    const ogScore = (scores['OG-1']?.matter || 31) + (scores['OG-1']?.manner || 31) + (scores['OG-1']?.method || 15)
                  + (scores['OG-2']?.matter || 29) + (scores['OG-2']?.manner || 30) + (scores['OG-2']?.method || 14);
    const ooScore = (scores['OO-1']?.matter || 30) + (scores['OO-1']?.manner || 32) + (scores['OO-1']?.method || 15)
                  + (scores['OO-2']?.matter || 30) + (scores['OO-2']?.manner || 29) + (scores['OO-2']?.method || 14);
    const cgScore = (scores['CG-1']?.matter || 32) + (scores['CG-1']?.manner || 30) + (scores['CG-1']?.method || 15)
                  + (scores['CG-2']?.matter || 30) + (scores['CG-2']?.manner || 30) + (scores['CG-2']?.method || 14);
    const coScore = (scores['CO-1']?.matter || 31) + (scores['CO-1']?.manner || 31) + (scores['CO-1']?.method || 15)
                  + (scores['CO-2']?.matter || 31) + (scores['CO-2']?.manner || 30) + (scores['CO-2']?.method || 14);

    const rankedTeams = [
      { positionName: 'Opening Government (OG)', teamScore: ogScore },
      { positionName: 'Opening Opposition (OO)', teamScore: ooScore },
      { positionName: 'Closing Government (CG)', teamScore: cgScore },
      { positionName: 'Closing Opposition (CO)', teamScore: coScore },
    ]
      .sort((a, b) => b.teamScore - a.teamScore)
      .map((t, idx) => ({ ...t, rank: idx + 1, speaker1: 'Debater 1', speaker2: 'Debater 2' }));

    const updated: DebateSession = {
      ...session,
      status: 'Archived',
      transcript: transcriptLines,
      winningTeam: `${rankedTeams[0].positionName} (${rankedTeams[0].teamScore} pts)`,
      teams: rankedTeams,
    };

    onSaveSessionToArchive(updated);
  };

  const activeSpeakerScore = scores[activeRole.id] || { matter: 30, manner: 30, method: 15, feedback: '' };

  const handleUpdateScore = (field: 'matter' | 'manner' | 'method' | 'feedback', val: any) => {
    setScores((prev) => ({
      ...prev,
      [activeRole.id]: {
        ...prev[activeRole.id],
        [field]: val,
      },
    }));
  };

  const currentSpeakerTotal = activeSpeakerScore.matter + activeSpeakerScore.manner + activeSpeakerScore.method;

  return (
    <div className="space-y-6">
      
      {/* Top Banner: Google Meet Active Connection */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 backdrop-blur-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="flex h-2.5 w-2.5 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              </span>
              <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
                Google Meet Active Sync
              </span>
              <span className="text-slate-600">·</span>
              <span className="text-xs text-slate-400">ID: GLUK-DEB-2026</span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              {session.title}
            </h2>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="text-amber-400 font-medium">{session.format}</span>
              <span>·</span>
              <span>{session.category}</span>
              <span>·</span>
              <span>{session.time}</span>
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <a
              href={session.googleMeetLink}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-lg shadow-emerald-950 transition-all whitespace-nowrap"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Launch Google Meet Room</span>
            </a>
            <button
              onClick={handleFinalizeAndArchive}
              className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500/15 text-amber-300 hover:bg-amber-500/25 border border-amber-500/30 rounded-lg text-xs font-semibold transition-all whitespace-nowrap"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-amber-400" />
              <span>Complete & Archive Round</span>
            </button>
          </div>
        </div>

        {/* Motion Card with Info Slide */}
        <div className="mt-4 pt-4 border-t border-slate-800/80">
          <div className="text-xs text-amber-400/90 font-semibold uppercase tracking-wider">
            Motion on Floor:
          </div>
          <p className="mt-1 text-base font-semibold text-slate-100 font-serif leading-relaxed">
            "{session.motion}"
          </p>
          {session.motionInfoSlide && (
            <div className="mt-2.5 p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs text-slate-300 leading-normal">
              <span className="font-semibold text-amber-300">Info Slide: </span>
              {session.motionInfoSlide}
            </div>
          )}
        </div>
      </div>

      {/* Main 3-Column Debate Cockpit */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Column 1: Speaker Order & BP Roster (3 cols) */}
        <div className="lg:col-span-3 space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Speaker Order
              </h3>
              <span className="text-[11px] font-mono text-amber-400">
                {selectedRoleIdx + 1} of {BP_ROLES.length}
              </span>
            </div>

            <div className="mt-3 space-y-2">
              {BP_ROLES.map((role, idx) => {
                const isSelected = selectedRoleIdx === idx;
                const isGov = role.team.includes('Government');

                return (
                  <button
                    key={role.id}
                    onClick={() => {
                      setSelectedRoleIdx(idx);
                      handleResetTimer();
                    }}
                    className={`w-full flex items-center justify-between p-2.5 rounded-lg text-left transition-all text-xs border ${
                      isSelected
                        ? 'bg-amber-500/15 border-amber-500/40 text-amber-200 font-semibold shadow-sm'
                        : 'bg-slate-950/40 border-slate-800/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <span
                        className={`w-1.5 h-6 rounded-full shrink-0 ${
                          isGov ? 'bg-blue-400' : 'bg-rose-400'
                        }`}
                      />
                      <div className="flex flex-col truncate">
                        <span className="truncate">{role.role}</span>
                        <span className="text-[10px] text-slate-500 truncate">
                          {role.team}
                        </span>
                      </div>
                    </div>
                    {isSelected && (
                      <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse shrink-0" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Quick Audio Bell Controls */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Bell className="w-3.5 h-3.5 text-amber-400" />
                <span>Parliamentary Bells</span>
              </h4>
              <span className="text-[10px] text-slate-500 font-mono">Web Audio</span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => debateBell.playSingleBell()}
                className="px-2.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md text-xs font-medium border border-slate-700 transition-colors"
              >
                1 Bell (1m / 6m)
              </button>
              <button
                onClick={() => debateBell.playDoubleBell()}
                className="px-2.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md text-xs font-medium border border-slate-700 transition-colors"
              >
                2 Bells (7:00)
              </button>
            </div>
            <button
              onClick={() => debateBell.playOvertimeBells()}
              className="w-full py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 rounded-md text-xs font-medium border border-rose-500/30 transition-colors"
            >
              Rapid Overtime Gavel (7:15)
            </button>
          </div>
        </div>

        {/* Column 2: Center Live Timer & POI Console (5 cols) */}
        <div className="lg:col-span-5 space-y-5">
          
          {/* Main Timekeeper Display */}
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-6 flex flex-col items-center justify-center text-center relative overflow-hidden">
            {/* Subtle glow backdrop */}
            <div className="absolute -top-16 left-1/2 -translate-x-1/2 w-48 h-48 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
              Active Speaker: {activeRole.role}
            </div>
            <div className="text-xs font-semibold text-amber-400 mb-4">
              {activeRole.team}
            </div>

            {/* Giant Monospace Timer */}
            <div className="font-mono text-6xl sm:text-7xl font-extrabold tracking-tight text-white tabular-nums drop-shadow-lg">
              {formatTime(seconds)}
            </div>

            {/* Phase indicator text */}
            <div className={`mt-3 text-xs tracking-wide transition-colors ${phaseColor}`}>
              {phaseText}
            </div>

            {/* Progress Bar (0 to 420s standard, with overtime indicator) */}
            <div className="w-full bg-slate-800 h-2 rounded-full mt-4 overflow-hidden relative">
              {/* 1m marker */}
              <div className="absolute left-[14.2%] top-0 bottom-0 w-0.5 bg-slate-500 z-10" title="1 min" />
              {/* 6m marker */}
              <div className="absolute left-[85.7%] top-0 bottom-0 w-0.5 bg-slate-500 z-10" title="6 min" />
              
              <div
                className={`h-full transition-all duration-300 ${
                  seconds < 60
                    ? 'bg-slate-400'
                    : seconds < 360
                    ? 'bg-emerald-500'
                    : seconds < 420
                    ? 'bg-amber-400'
                    : 'bg-red-500'
                }`}
                style={{ width: `${Math.min(100, (seconds / 420) * 100)}%` }}
              />
            </div>

            {/* Timer Actions */}
            <div className="flex items-center gap-3 mt-6">
              <button
                onClick={() => setIsTimerRunning(!isTimerRunning)}
                className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-bold transition-all shadow-md ${
                  isTimerRunning
                    ? 'bg-amber-500 text-slate-950 hover:bg-amber-400 shadow-amber-500/20'
                    : 'bg-white text-slate-900 hover:bg-slate-100'
                }`}
              >
                {isTimerRunning ? (
                  <>
                    <Pause className="w-4 h-4" />
                    <span>Pause Speech</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    <span>Start Speech Timer</span>
                  </>
                )}
              </button>

              <button
                onClick={handleResetTimer}
                className="p-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
                title="Reset Timer"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Point of Information (POI) Manager */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                POI (Point of Information) Tracker
              </h4>
              <span
                className={`text-[11px] font-medium px-2 py-0.5 rounded ${
                  isPoiAllowed
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                    : 'bg-slate-800 text-slate-500'
                }`}
              >
                {isPoiAllowed ? 'POIs Legal' : 'Protected Time'}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 mt-3">
              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-center">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                  Offered from Floor
                </span>
                <span className="font-mono text-2xl font-bold text-white tabular-nums">
                  {poiCountOffered}
                </span>
                <button
                  onClick={() => setPoiCountOffered((p) => p + 1)}
                  disabled={!isPoiAllowed}
                  className="mt-2 w-full py-1 text-[11px] bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 rounded border border-slate-700 transition-colors"
                >
                  + Offer POI
                </button>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-center">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                  Accepted by Speaker
                </span>
                <span className="font-mono text-2xl font-bold text-emerald-400 tabular-nums">
                  {poiCountAccepted}
                </span>
                <button
                  onClick={() => {
                    setPoiCountAccepted((p) => p + 1);
                    setPoiTimerSeconds(0);
                    setIsPoiTimerRunning(true);
                  }}
                  disabled={!isPoiAllowed}
                  className="mt-2 w-full py-1 text-[11px] bg-emerald-600/20 hover:bg-emerald-600/30 disabled:opacity-40 text-emerald-300 rounded border border-emerald-500/40 transition-colors font-medium"
                >
                  Accept (15s Cap)
                </button>
              </div>
            </div>

            {isPoiTimerRunning && (
              <div className="mt-3 p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-500/30 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="w-3.5 h-3.5 text-emerald-400 animate-spin" />
                  <span className="text-xs text-emerald-300 font-medium">
                    Active POI Clock: <span className="font-mono font-bold">{poiTimerSeconds}s</span> (Standard: ≤15s)
                  </span>
                </div>
                <button
                  onClick={() => setIsPoiTimerRunning(false)}
                  className="px-2 py-0.5 text-[11px] bg-emerald-700 text-white rounded font-medium hover:bg-emerald-600"
                >
                  Stop POI
                </button>
              </div>
            )}
          </div>

          {/* Adjudication Scorecard for active speaker */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5 text-amber-400" />
                <span>Adjudicator Ballot Rubric</span>
              </h4>
              <span className="font-mono text-xs font-bold text-amber-400">
                Total: {currentSpeakerTotal} / 100
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-xs">
              <div>
                <label className="text-[10px] text-slate-400 block mb-1">
                  Matter (Max 40)
                </label>
                <input
                  type="number"
                  min="20"
                  max="40"
                  value={activeSpeakerScore.matter}
                  onChange={(e) => handleUpdateScore('matter', parseInt(e.target.value) || 0)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-center font-mono font-semibold text-white"
                />
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1">
                  Manner (Max 40)
                </label>
                <input
                  type="number"
                  min="20"
                  max="40"
                  value={activeSpeakerScore.manner}
                  onChange={(e) => handleUpdateScore('manner', parseInt(e.target.value) || 0)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-center font-mono font-semibold text-white"
                />
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1">
                  Method (Max 20)
                </label>
                <input
                  type="number"
                  min="10"
                  max="20"
                  value={activeSpeakerScore.method}
                  onChange={(e) => handleUpdateScore('method', parseInt(e.target.value) || 0)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-center font-mono font-semibold text-white"
                />
              </div>
            </div>

            <div>
              <label className="text-[10px] text-slate-400 block mb-1">
                Adjudicator Notes / Rebuttal Critique
              </label>
              <input
                type="text"
                placeholder="Key argument clarity, weighing, engagement with opening half..."
                value={activeSpeakerScore.feedback}
                onChange={(e) => handleUpdateScore('feedback', e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-amber-500/50"
              />
            </div>
          </div>
        </div>

        {/* Column 3: Live Transcription & Audio Stream (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 flex flex-col h-[580px]">
            
            {/* Header */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Radio className={`w-3.5 h-3.5 ${isListening ? 'text-rose-400 animate-pulse' : 'text-slate-500'}`} />
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Live Meet Transcription
                </h3>
              </div>
              <button
                onClick={toggleMicListening}
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold transition-all ${
                  isListening
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse'
                    : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
                }`}
              >
                {isListening ? (
                  <>
                    <MicOff className="w-3.5 h-3.5" />
                    <span>Stop Mic</span>
                  </>
                ) : (
                  <>
                    <Mic className="w-3.5 h-3.5 text-amber-400" />
                    <span>Capture Audio</span>
                  </>
                )}
              </button>
            </div>

            {/* Quick Simulate Live Stream Audio button */}
            <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-400">
              <span>Simulated or Real mic:</span>
              <button
                onClick={simulateLiveGoogleMeetSpeech}
                className="text-amber-400 hover:text-amber-300 font-medium underline underline-offset-2"
              >
                + Inject Live Stream Snippet
              </button>
            </div>

            {/* Transcript log scroll area */}
            <div className="flex-1 overflow-y-auto mt-3 pr-1 space-y-3">
              {transcriptLines.length === 0 && !currentSpeechDraft && (
                <div className="h-full flex flex-col items-center justify-center text-center p-4 text-slate-500">
                  <Mic className="w-8 h-8 stroke-[1.5] text-slate-600 mb-2" />
                  <p className="text-xs font-medium text-slate-400">No speech recorded yet</p>
                  <p className="text-[11px] text-slate-600 mt-1 max-w-[200px]">
                    Click "Capture Audio" or speak into Google Meet to stream real-time debate remarks.
                  </p>
                </div>
              )}

              {transcriptLines.map((entry, i) => (
                <div key={i} className="p-3 rounded-lg bg-slate-950/70 border border-slate-800/80 text-xs space-y-1">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="font-semibold text-amber-400/90">{entry.speaker}</span>
                    <span className="font-mono text-slate-500 tabular-nums">{entry.timestamp}</span>
                  </div>
                  <p className="text-slate-200 leading-relaxed font-sans">{entry.text}</p>
                </div>
              ))}

              {currentSpeechDraft && (
                <div className="p-3 rounded-lg bg-slate-950/40 border border-amber-500/20 text-xs italic text-amber-200/80">
                  <span className="text-[10px] uppercase font-mono text-amber-400/70 block mb-0.5">
                    Recognizing voice...
                  </span>
                  {currentSpeechDraft}
                </div>
              )}
            </div>

            {/* Post-Debate Auto-Export Bar */}
            <div className="pt-3 border-t border-slate-800 mt-2 flex items-center justify-between">
              <span className="text-[11px] text-slate-500 font-mono">
                {transcriptLines.length} debate turns logged
              </span>
              <button
                onClick={() => {
                  const textBlob = transcriptLines
                    .map((t) => `[${t.timestamp}] ${t.speaker}:\n${t.text}\n`)
                    .join('\n');
                  const blob = new Blob([textBlob], { type: 'text/plain' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `GLUK_Debate_Transcript_${session.id}.txt`;
                  a.click();
                }}
                className="text-[11px] inline-flex items-center gap-1 text-slate-400 hover:text-white"
              >
                <Download className="w-3 h-3" />
                <span>Export TXT</span>
              </button>
            </div>

          </div>
        </div>

      </div>

    </div>
  );
};


