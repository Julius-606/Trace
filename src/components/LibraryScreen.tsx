import React, { useState } from 'react';
import {
  BookOpen,
  Search,
  Check,
  Plus,
  ArrowRight,
  Sparkles,
  Layers,
  ArrowLeft
} from 'lucide-react';
import { Unit } from '../types';

interface LibraryScreenProps {
  units: Unit[];
  onToggleEnroll: (unitId: number, isActive: boolean) => void;
  onSelectUnit: (unitId: number) => void;
  onBack: () => void;
}

export const LibraryScreen: React.FC<LibraryScreenProps> = ({
  units,
  onToggleEnroll,
  onSelectUnit,
  onBack
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');

  const derivedCategories = Array.from(new Set(units.map((u) => u.category).filter(Boolean)));
  const categories = ['All', ...(derivedCategories.length > 0 ? derivedCategories : ['Foundations & Sciences', 'Engineering & Technology', 'Business & Law', 'Health Sciences', 'Humanities'])];

  const filtered = units.filter((u) => {
    const matchSearch =
      u.unitName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchCat = selectedCategory === 'All' || u.category === selectedCategory;
    return matchSearch && matchCat;
  });

  return (
    <div className="space-y-6 pb-16 animate-in fade-in duration-200">
      {/* Top Header */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 backdrop-blur-md flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Back to Dashboard"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">
              Curriculum Catalog
            </span>
            <h1 className="text-2xl font-black text-white mt-0.5">Discipline & Unit Library</h1>
            <p className="text-xs text-slate-400">Explore and enroll in medical syllabus programs</p>
          </div>
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search disciplines or units..."
            className="w-full bg-slate-950 border border-slate-800 rounded-2xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-indigo-500 transition-colors"
          />
        </div>
      </div>

      {/* Category Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        {categories.map((c) => (
          <button
            key={c}
            onClick={() => setSelectedCategory(c)}
            className={`px-4 py-2 rounded-xl font-semibold whitespace-nowrap transition-colors ${
              selectedCategory === c
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            {c}
          </button>
        ))}
      </div>

      {/* Units Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map((unit) => {
          const totalSubtopics = unit.modules.flatMap((m) => m.topics.flatMap((t) => t.subtopics)).length;
          const completedSubtopics = unit.modules
            .flatMap((m) => m.topics.flatMap((t) => t.subtopics))
            .filter((s) => s.isCompleted).length;
          const progress = totalSubtopics > 0 ? Math.round((completedSubtopics / totalSubtopics) * 100) : 0;

          return (
            <div
              key={unit.id}
              className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 flex flex-col justify-between hover:border-slate-700 transition-all shadow-lg group"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                    {unit.category}
                  </span>
                  {unit.isActive ? (
                    <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-400">
                      <Check className="w-3.5 h-3.5" />
                      <span>Enrolled</span>
                    </span>
                  ) : (
                    <span className="text-[11px] text-slate-500 font-medium">Available</span>
                  )}
                </div>

                <h3 className="text-lg font-bold text-white group-hover:text-indigo-300 transition-colors">
                  {unit.unitName}
                </h3>
                <p className="text-xs text-slate-400 mt-1.5 leading-relaxed line-clamp-3">
                  {unit.description}
                </p>

                <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span>{unit.modules.length} Modules</span>
                  <span>{totalSubtopics} Subtopics</span>
                  {unit.isActive && <span className="font-bold text-indigo-400">{progress}% Done</span>}
                </div>
              </div>

              {/* Card Actions */}
              <div className="mt-5 pt-4 border-t border-slate-800/80 flex items-center justify-between gap-2">
                <button
                  onClick={() => onSelectUnit(unit.id)}
                  className="flex items-center gap-1 text-xs font-semibold text-indigo-400 hover:text-indigo-300"
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span>Outline</span>
                </button>

                <button
                  onClick={() => onToggleEnroll(unit.id, !unit.isActive)}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                    unit.isActive
                      ? 'bg-slate-800 text-slate-300 hover:bg-red-950/40 hover:text-red-300'
                      : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20'
                  }`}
                >
                  {unit.isActive ? 'Deactivate' : 'Enroll Now'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
