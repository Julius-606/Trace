
import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Play,
  Pause,
  RotateCcw,
  Zap,
  Target,
  Brain,
  HelpCircle,
  Award,
} from 'lucide-react';
import { debateBell } from '../../services/audioBell';

const SAMPLE_DRILLS = [
  {
    topic: 'Informal Cross-Border Trade & Mobile Money',
    scenario: 'The opposition argues: "Small-scale traders in Busia will bypass the digital EAC currency and continue transacting in physical cash notes because digital networks have unpredictable outages."',
    challenge: 'Deliver a 60-second Point of Information (POI) refuting their premise using network redundancy and merchant tax incentives.',
  },
  {
    topic: 'Healthcare AI Autonomy vs Human Clinicians',
    scenario: 'The opposition argues: "Rural patients in Lake Basin hospitals will refuse AI-derived clinical prescriptions because they value culturally informed bedside empathy above diagnostic algorithms."',
    challenge: 'Deliver a 60-second Point of Information demonstrating that maternal mortality reduction overrides initial cultural hesitancy.',
  },
  {
    topic: 'African Union Sovereign Debt Default',
    scenario: 'The opposition argues: "If African nations collectively default against Paris Club lenders, global credit rating agencies will permanently downgrade our economies, halting all infrastructure loans."',
    challenge: 'Deliver a 60-second POI explaining the collective bargaining power of a united African bloc versus isolated debtor states.',
  },
  {
    topic: 'Environmental Reparations for Lake Victoria Pollution',
    scenario: 'The opposition argues: "Holding upstream industrial firms strictly liable without proving specific point-source effluent discharge violates fundamental corporate due process."',
    challenge: 'Deliver a 60-second POI establishing the precautionary principle in international environmental jurisprudence.',
  },
];

export const DrillsPractice: React.FC = () => {
  const [currentDrillIdx, setCurrentDrillIdx] = useState(0);
  const [drillSeconds, setDrillSeconds] = useState(60);
  const [isDrillRunning, setIsDrillRunning] = useState(false);

  const activeDrill = SAMPLE_DRILLS[currentDrillIdx];

  useEffect(() => {
    let int: NodeJS.Timeout | null = null;
    if (isDrillRunning && drillSeconds > 0) {
      int = setInterval(() => {
        setDrillSeconds((s) => {
          if (s - 1 === 0) {
            debateBell.playDoubleBell();
          }
          return s - 1;
        });
      }, 1000);
    }
    return () => {
      if (int) clearInterval(int);
    };
  }, [isDrillRunning, drillSeconds]);

  const handleNextDrill = () => {
    setCurrentDrillIdx((prev) => (prev + 1) % SAMPLE_DRILLS.length);
    setIsDrillRunning(false);
    setDrillSeconds(60);
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="pb-4 border-b border-slate-800">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-400" />
          <span>60-Second POI & Rapid Rebuttal Arena</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Sharpen speaker reflexes between official rounds. Formulate tight, high-impact responses under strict time pressure.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Drill Console: 7 cols */}
        <div className="lg:col-span-7 rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <span className="text-[11px] font-bold uppercase tracking-wider text-amber-400">
              Drill #{currentDrillIdx + 1}: {activeDrill.topic}
            </span>
            <button
              onClick={handleNextDrill}
              className="text-xs text-amber-400 hover:text-amber-300 font-medium"
            >
              Next Scenario →
            </button>
          </div>

          <div className="space-y-3">
            <div className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800 space-y-1 text-xs">
              <span className="font-semibold text-rose-300 uppercase text-[10px] tracking-wider block">
                Opposition Assertion:
              </span>
              <p className="text-slate-200 italic leading-relaxed">
                "{activeDrill.scenario}"
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/30 space-y-1 text-xs">
              <span className="font-semibold text-amber-300 uppercase text-[10px] tracking-wider block flex items-center gap-1">
                <Target className="w-3.5 h-3.5" />
                <span>Your Objective:</span>
              </span>
              <p className="text-slate-100 font-medium leading-relaxed">
                {activeDrill.challenge}
              </p>
            </div>
          </div>

          {/* Drill Timer */}
          <div className="pt-2 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="font-mono text-3xl font-extrabold text-white tabular-nums">
                00:{drillSeconds.toString().padStart(2, '0')}
              </span>
              <span className="text-[11px] text-slate-400">
                {drillSeconds === 0 ? 'Time Up! Double bell sounded.' : 'Speech limit: 60s'}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsDrillRunning(!isDrillRunning)}
                className="px-4 py-2 bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold rounded-lg text-xs flex items-center gap-1.5 transition-colors"
              >
                {isDrillRunning ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 fill-current" />}
                <span>{isDrillRunning ? 'Pause' : 'Start POI Drill'}</span>
              </button>
              <button
                onClick={() => {
                  setIsDrillRunning(false);
                  setDrillSeconds(60);
                }}
                className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs transition-colors"
                title="Reset drill"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* WUDC Rubric Guide: 5 cols */}
        <div className="lg:col-span-5 rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3 text-xs">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
            <Award className="w-3.5 h-3.5 text-amber-400" />
            <span>PAUDC / WUDC Scoring Breakdown</span>
          </h3>

          <div className="space-y-2">
            <div className="p-2.5 rounded bg-slate-950/60 border border-slate-800">
              <span className="font-bold text-amber-400 block mb-0.5">Matter (Max 40 Pts)</span>
              <p className="text-slate-400 text-[11px] leading-normal">
                Substance, logic, evidence, and analytical depth. Is the argument grounded in real-world mechanisms?
              </p>
            </div>

            <div className="p-2.5 rounded bg-slate-950/60 border border-slate-800">
              <span className="font-bold text-blue-400 block mb-0.5">Manner (Max 40 Pts)</span>
              <p className="text-slate-400 text-[11px] leading-normal">
                Persuasiveness, rhetoric, vocal cadence, eye contact, and passion. Did the speaker command the chamber?
              </p>
            </div>

            <div className="p-2.5 rounded bg-slate-950/60 border border-slate-800">
              <span className="font-bold text-purple-400 block mb-0.5">Method (Max 20 Pts)</span>
              <p className="text-slate-400 text-[11px] leading-normal">
                Internal structure, POI management, time pacing, and direct engagement with opposing team arguments.
              </p>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
};


