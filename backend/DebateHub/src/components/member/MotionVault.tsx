
import React, { useState, useEffect } from 'react';
import { DebateSession } from '../../types';
import {
  BookOpen,
  Search,
  Filter,
  Trophy,
  Users,
  Clock,
  Sparkles,
  Play,
  Pause,
  RotateCcw,
  FileText,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

interface MotionVaultProps {
  debates: DebateSession[];
}

export const MotionVault: React.FC<MotionVaultProps> = ({ debates }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [selectedFormat, setSelectedFormat] = useState<string>('All');
  const [expandedDebateId, setExpandedDebateId] = useState<string | null>(
    debates[0]?.id || null
  );

  // 15-Minute Prep Timer state
  const [prepSeconds, setPrepSeconds] = useState(15 * 60);
  const [isPrepRunning, setIsPrepRunning] = useState(false);

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isPrepRunning && prepSeconds > 0) {
      interval = setInterval(() => {
        setPrepSeconds((sec) => sec - 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPrepRunning, prepSeconds]);

  const categories = [
    'All',
    'Economics & Development',
    'Technology & AI',
    'African Governance',
    'Geopolitics & IR',
    'Law & Human Rights',
  ];

  const filteredDebates = debates.filter((d) => {
    const matchesCategory =
      selectedCategory === 'All' || d.category === selectedCategory;
    const matchesFormat =
      selectedFormat === 'All' || d.format.includes(selectedFormat);
    const matchesSearch =
      d.motion.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (d.summaryClashes &&
        d.summaryClashes.some((c) =>
          c.toLowerCase().includes(searchQuery.toLowerCase())
        ));
    return matchesCategory && matchesFormat && matchesSearch;
  });

  const formatPrepTime = (totalSec: number) => {
    const m = Math.floor(totalSec / 60);
    const s = totalSec % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Historical Motion Vault & Debate Archives</span>
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
              {debates.length} Documented Rounds
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Permanent institutional knowledge base for current and incoming debaters, transcripts, and adjudicator clash analyses.
          </p>
        </div>

        {/* 15-Minute Prep Timer Box */}
        <div className="flex items-center gap-3 p-2 px-3 rounded-xl bg-slate-900 border border-slate-800 shrink-0">
          <div className="flex flex-col">
            <span className="text-[10px] uppercase font-bold text-amber-400 tracking-wider">
              15-Min Prep Clock
            </span>
            <span className="font-mono text-base font-extrabold text-white tabular-nums">
              {formatPrepTime(prepSeconds)}
            </span>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setIsPrepRunning(!isPrepRunning)}
              className="p-1.5 rounded-lg bg-amber-400 text-slate-950 hover:bg-amber-300 font-bold transition-colors"
              title={isPrepRunning ? 'Pause Prep' : 'Start 15m Prep'}
            >
              {isPrepRunning ? (
                <Pause className="w-3.5 h-3.5" />
              ) : (
                <Play className="w-3.5 h-3.5 fill-current" />
              )}
            </button>
            <button
              onClick={() => {
                setIsPrepRunning(false);
                setPrepSeconds(15 * 60);
              }}
              className="p-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors"
              title="Reset 15m Prep"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 no-scrollbar">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg whitespace-nowrap transition-colors ${
                selectedCategory === cat
                  ? 'bg-amber-400/20 text-amber-300 border border-amber-400/30 font-semibold'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search motions, clashes, or speakers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-amber-500/50 w-full md:w-64"
          />
        </div>
      </div>

      {/* Motion Archives Accordion / List */}
      <div className="space-y-4">
        {filteredDebates.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500 border border-slate-800 rounded-xl bg-slate-900/40">
            No motions found matching your search criteria.
          </div>
        ) : (
          filteredDebates.map((debate) => {
            const isExpanded = expandedDebateId === debate.id;

            return (
              <div
                key={debate.id}
                className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden transition-all"
              >
                {/* Accordion Trigger Header */}
                <div
                  onClick={() =>
                    setExpandedDebateId(isExpanded ? null : debate.id)
                  }
                  className="p-5 cursor-pointer hover:bg-slate-800/30 transition-colors flex items-start justify-between gap-4"
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      <span className="font-semibold text-amber-400">
                        {debate.format}
                      </span>
                      <span className="text-slate-600">·</span>
                      <span className="text-slate-400">{debate.category}</span>
                      <span className="text-slate-600">·</span>
                      <span className="font-mono text-slate-500">{debate.date}</span>
                      {debate.winningTeam && (
                        <>
                          <span className="text-slate-600">·</span>
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                            <Trophy className="w-3 h-3" />
                            Winner: {debate.winningTeam}
                          </span>
                        </>
                      )}
                    </div>

                    <h2 className="text-base font-bold text-white font-serif leading-snug">
                      "{debate.motion}"
                    </h2>

                    <p className="text-xs text-slate-400">
                      {debate.title}
                    </p>
                  </div>

                  <button className="p-1 text-slate-400 hover:text-white shrink-0 mt-1">
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </button>
                </div>

                {/* Expanded Details: Teams, Clashes, Transcripts */}
                {isExpanded && (
                  <div className="px-5 pb-5 pt-2 border-t border-slate-800/80 space-y-5 bg-slate-950/30">
                    
                    {/* Info Slide if present */}
                    {debate.motionInfoSlide && (
                      <div className="p-3.5 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-300">
                        <strong className="text-amber-300">Context & Info Slide: </strong>
                        {debate.motionInfoSlide}
                      </div>
                    )}

                    {/* Team Allocations & Ranks */}
                    <div>
                      <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2.5">
                        Team Allocations & Final Ranks
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                        {debate.teams.map((t, idx) => (
                          <div
                            key={idx}
                            className={`p-3 rounded-lg border ${
                              t.rank === 1
                                ? 'bg-amber-500/10 border-amber-500/30 text-amber-200'
                                : 'bg-slate-900/60 border-slate-800 text-slate-300'
                            }`}
                          >
                            <div className="flex items-center justify-between pb-1.5 border-b border-slate-800/80">
                              <span className="font-semibold">{t.positionName}</span>
                              {t.rank && (
                                <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-800">
                                  {t.rank === 1 ? '🥇 1st' : t.rank === 2 ? '🥈 2nd' : t.rank === 3 ? '🥉 3rd' : '4th'}
                                </span>
                              )}
                            </div>
                            <div className="mt-2 space-y-0.5 text-[11px] text-slate-400">
                              <div>{t.speaker1}</div>
                              {t.speaker2 && <div>{t.speaker2}</div>}
                            </div>
                            {t.teamScore && (
                              <div className="mt-2 pt-1 border-t border-slate-800/60 text-[10px] font-mono text-right text-slate-400">
                                Tab: {t.teamScore} pts
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Core Clashes Analysis */}
                    {debate.summaryClashes && debate.summaryClashes.length > 0 && (
                      <div>
                        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                          Key Clash Points Identified in Adjudication
                        </h4>
                        <div className="space-y-1.5 text-xs text-slate-300">
                          {debate.summaryClashes.map((clash, i) => (
                            <div
                              key={i}
                              className="p-2.5 rounded-lg bg-slate-900/40 border border-slate-800/60 flex items-start gap-2"
                            >
                              <span className="font-mono text-amber-400 font-bold shrink-0">
                                0{i + 1}.
                              </span>
                              <span>{clash}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Adjudicator Panel */}
                    <div className="text-xs text-slate-400 flex items-center gap-2">
                      <span className="font-semibold text-slate-300">Adjudication Panel:</span>
                      <span>{debate.adjudicators.join(' · ')}</span>
                    </div>

                    {/* Speech Transcript Preview if available */}
                    {debate.transcript && debate.transcript.length > 0 && (
                      <div className="space-y-2 pt-2 border-t border-slate-800">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                            <FileText className="w-3.5 h-3.5 text-amber-400" />
                            <span>Debate Floor Transcript Record</span>
                          </h4>
                          <span className="text-[10px] text-slate-500 font-mono">
                            {debate.transcript.length} turns recorded
                          </span>
                        </div>

                        <div className="max-h-60 overflow-y-auto space-y-2 pr-1">
                          {debate.transcript.map((line, lIdx) => (
                            <div
                              key={lIdx}
                              className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 text-xs space-y-1"
                            >
                              <div className="flex items-center justify-between text-[10px]">
                                <span className="font-semibold text-amber-400">
                                  {line.speaker}
                                </span>
                                <span className="font-mono text-slate-500">
                                  {line.timestamp}
                                </span>
                              </div>
                              <p className="text-slate-300 leading-relaxed">
                                {line.text}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

    </div>
  );
};


