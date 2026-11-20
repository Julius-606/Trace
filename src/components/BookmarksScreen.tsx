import React, { useState } from 'react';
import {
  Bookmark as BookmarkIcon,
  Trash2,
  ExternalLink,
  BookOpen,
  MessageSquare,
  HelpCircle,
  Clock,
  Sparkles,
  ArrowRight,
  Search
} from 'lucide-react';
import { Bookmark } from '../types';
import { TraceStore } from '../lib/store';

interface BookmarksScreenProps {
  onNavigateToLearn: (subtopicId: number) => void;
  onOpenBrowser: (url: string) => void;
  onSelectTab: (tab: string) => void;
}

export const BookmarksScreen: React.FC<BookmarksScreenProps> = ({
  onNavigateToLearn,
  onOpenBrowser,
  onSelectTab
}) => {
  const [bookmarks, setBookmarks] = useState<any[]>(() => TraceStore.getBookmarks(TraceStore.getUser().id));
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<'all' | 'learn' | 'browser' | 'chat'>('all');

  const handleDelete = (id: string) => {
    const updated = TraceStore.deleteBookmark(id);
    setBookmarks(updated.filter((b) => b.userId === TraceStore.getUser().id));
  };

  const filteredBookmarks = bookmarks.filter((bm) => {
    // Search matching
    const matchesSearch =
      (bm.subtopicName || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (bm.objectiveDescription || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (bm.notes || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (bm.title || '').toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    // Filter type
    if (activeFilter === 'all') return true;
    if (activeFilter === 'learn') {
      return !bm.type || bm.type === 'learn' || bm.subtopicId;
    }
    if (activeFilter === 'browser') return bm.type === 'browser';
    if (activeFilter === 'chat') return bm.type === 'chat';
    return true;
  });

  return (
    <div className="space-y-6 pb-12 animate-in fade-in duration-200">
      {/* Title & Stats */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 backdrop-blur-md flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <BookmarkIcon className="w-4 h-4 fill-current" />
            </div>
            <h1 className="text-xl font-bold text-white">Saved Bookmarks & Clips</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Access and review your saved syllabus points, consultation transcripts, and browser references.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-slate-950 px-4 py-2 rounded-2xl border border-slate-800 text-center">
            <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Total Saved</p>
            <p className="text-lg font-black text-amber-400 mt-0.5">{bookmarks.length}</p>
          </div>
        </div>
      </div>

      {/* Filters and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-slate-900/40 p-3 rounded-2xl border border-slate-800/60">
        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          {(['all', 'learn', 'browser', 'chat'] as const).map((filter) => (
            <button
              key={filter}
              onClick={() => setActiveFilter(filter)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold capitalize transition-all whitespace-nowrap ${
                activeFilter === filter
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {filter === 'all'
                ? 'All Clips'
                : filter === 'learn'
                ? 'Syllabus Points'
                : filter === 'browser'
                ? 'Browser Links'
                : 'Consultation Excerpts'}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search bookmarks..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-3.5 py-1.5 text-xs text-slate-200 placeholder-slate-500 outline-none focus:border-amber-500/50 transition-colors"
          />
        </div>
      </div>

      {/* Bookmarks Grid / List */}
      {filteredBookmarks.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredBookmarks.map((bm) => {
            const isBrowser = bm.type === 'browser';
            const isChat = bm.type === 'chat';
            const isLearn = !bm.type || bm.type === 'learn' || bm.subtopicId;

            return (
              <div
                key={bm.id}
                className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-5 flex flex-col justify-between hover:border-amber-500/30 transition-all duration-200 group"
              >
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1.5 ${
                      isBrowser
                        ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                        : isChat
                        ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                        : 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                    }`}>
                      {isBrowser ? (
                        <>
                          <ExternalLink className="w-3 h-3" />
                          <span>Browser Reference</span>
                        </>
                      ) : isChat ? (
                        <>
                          <MessageSquare className="w-3 h-3" />
                          <span>Tutor Consultation</span>
                        </>
                      ) : (
                        <>
                          <BookOpen className="w-3 h-3" />
                          <span>Syllabus Target</span>
                        </>
                      )}
                    </span>

                    <button
                      onClick={() => handleDelete(bm.id)}
                      className="p-1.5 text-slate-500 hover:text-red-400 rounded-lg hover:bg-red-950/20 opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Delete bookmark"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <h3 className="text-sm font-bold text-slate-100 mt-3.5 leading-tight">
                    {bm.title || bm.subtopicName || 'Saved Learning Clip'}
                  </h3>

                  {bm.objectiveDescription && (
                    <p className="text-[11px] text-amber-400 mt-1 font-semibold">
                      {bm.objectiveDescription}
                    </p>
                  )}

                  {bm.excerpt && (
                    <p className="text-xs text-slate-400 mt-2.5 line-clamp-3 bg-slate-950/40 p-2.5 rounded-xl border border-slate-800/60 leading-relaxed italic">
                      "{bm.excerpt}"
                    </p>
                  )}

                  {bm.notes && (
                    <div className="mt-3 p-2 rounded-xl bg-amber-500/5 border border-amber-500/10 text-[11px] text-slate-300">
                      <span className="font-bold text-amber-300">My Notes:</span> {bm.notes}
                    </div>
                  )}
                </div>

                <div className="mt-5 pt-3.5 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(bm.timestamp).toLocaleDateString()}
                  </span>

                  {isLearn && bm.subtopicId && (
                    <button
                      onClick={() => onNavigateToLearn(bm.subtopicId)}
                      className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-bold transition-colors"
                    >
                      <span>Study Now</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}

                  {isBrowser && bm.target && (
                    <button
                      onClick={() => onOpenBrowser(bm.target)}
                      className="flex items-center gap-1 text-blue-400 hover:text-blue-300 font-bold transition-colors"
                    >
                      <span>Open Link</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}

                  {isChat && (
                    <button
                      onClick={() => onSelectTab('consultations')}
                      className="flex items-center gap-1 text-purple-400 hover:text-purple-300 font-bold transition-colors"
                    >
                      <span>Resume Chat</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-16 bg-slate-900/20 border border-dashed border-slate-800 rounded-3xl">
          <BookmarkIcon className="w-10 h-10 text-slate-600 mx-auto stroke-[1.5]" />
          <h3 className="text-sm font-bold text-slate-300 mt-4">No Bookmarks Found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
            Try choosing a unit, opening reference links or chat, and bookmarking key clinical insights.
          </p>
        </div>
      )}
    </div>
  );
};
