
import React, { useState } from 'react';
import { FinancialTransaction, Member } from '../../types';
import {
  Wallet,
  ArrowDownLeft,
  ArrowUpRight,
  Filter,
  Plus,
  Download,
  CheckCircle,
  Clock,
  Search,
  Receipt,
  FileSpreadsheet,
} from 'lucide-react';

interface FinancialLedgerProps {
  transactions: FinancialTransaction[];
  members: Member[];
  onAddTransaction: (txn: FinancialTransaction) => void;
  onVerifyMemberPayment: (memberId: string, mpesaRef: string) => void;
}

export const FinancialLedger: React.FC<FinancialLedgerProps> = ({
  transactions,
  members,
  onAddTransaction,
  onVerifyMemberPayment,
}) => {
  const [filterType, setFilterType] = useState<'All' | 'Income' | 'Expense'>('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'ledger' | 'dues'>('ledger');
  const [showAddModal, setShowAddModal] = useState(false);

  // New transaction form state
  const [formType, setFormType] = useState<'Income' | 'Expense'>('Income');
  const [formCategory, setFormCategory] = useState<any>('Semester Dues');
  const [formAmount, setFormAmount] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [formRefCode, setFormRefCode] = useState('');
  const [formRecordedBy, setFormRecordedBy] = useState('Mercy Wangari (Finance Sec)');

  // Dues verification modal state
  const [verifyTargetMember, setVerifyTargetMember] = useState<Member | null>(null);
  const [inputMpesaCode, setInputMpesaCode] = useState('');

  // Calculations
  const verifiedTxns = transactions.filter((t) => t.status === 'Verified');
  const totalIncome = verifiedTxns
    .filter((t) => t.type === 'Income')
    .reduce((sum, t) => sum + t.amountKes, 0);

  const totalExpense = verifiedTxns
    .filter((t) => t.type === 'Expense')
    .reduce((sum, t) => sum + t.amountKes, 0);

  const netBalance = totalIncome - totalExpense;

  const filteredTransactions = transactions.filter((t) => {
    const matchesType = filterType === 'All' || t.type === filterType;
    const matchesSearch =
      t.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.referenceCode.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.category.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  const handleCreateTransaction = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formAmount || !formDescription || !formRefCode) return;

    const newTxn: FinancialTransaction = {
      id: `txn-${Date.now()}`,
      date: new Date().toISOString().split('T')[0],
      type: formType,
      category: formCategory,
      amountKes: parseFloat(formAmount),
      description: formDescription,
      referenceCode: formRefCode.toUpperCase().trim(),
      recordedBy: formRecordedBy,
      status: 'Verified',
    };

    onAddTransaction(newTxn);
    setShowAddModal(false);
    setFormAmount('');
    setFormDescription('');
    setFormRefCode('');
  };

  const handleConfirmVerification = () => {
    if (!verifyTargetMember || !inputMpesaCode) return;
    onVerifyMemberPayment(verifyTargetMember.id, inputMpesaCode.toUpperCase().trim());
    setVerifyTargetMember(null);
    setInputMpesaCode('');
  };

  const exportFinancialsCsv = () => {
    const headers = 'ID,Date,Type,Category,Amount (KES),Description,Reference Code,Recorded By,Status\n';
    const rows = transactions
      .map(
        (t) =>
          `"${t.id}","${t.date}","${t.type}","${t.category}","${t.amountKes}","${t.description.replace(/"/g, '""')}","${t.referenceCode}","${t.recordedBy}","${t.status}"`
      )
      .join('\n');
    const blob = new Blob([headers + rows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `GLUK_Debate_Financial_Ledger_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  return (
    <div className="space-y-6">

      {/* Top Ledger Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Treasury & Financial Ledger</span>
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
              KES (Kenyan Shillings)
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Official cash flow, semester membership dues, tournament funding, and M-Pesa reconciliation.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={exportFinancialsCsv}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-900 border border-slate-800 hover:bg-slate-800 hover:text-white transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>

          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-950 bg-amber-400 hover:bg-amber-300 transition-colors shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Record Transaction</span>
          </button>
        </div>
      </div>

      {/* Balance Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        
        {/* Net Treasury */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Net Treasury Reserve</span>
            <Wallet className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-1">
            <span className="font-mono text-xs font-bold text-amber-400">KES</span>
            <span className="font-mono text-2xl font-bold text-white tabular-nums">
              {netBalance.toLocaleString()}
            </span>
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">
            Audited & verified by Finance Secretary
          </span>
        </div>

        {/* Total Inflow */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Income / Inflow</span>
            <ArrowDownLeft className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-1">
            <span className="font-mono text-xs font-bold text-emerald-400">KES</span>
            <span className="font-mono text-2xl font-bold text-emerald-400 tabular-nums">
              {totalIncome.toLocaleString()}
            </span>
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">
            Semester dues + Alumni patron grants
          </span>
        </div>

        {/* Total Outflow */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Expenses / Outflow</span>
            <ArrowUpRight className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-1">
            <span className="font-mono text-xs font-bold text-rose-400">KES</span>
            <span className="font-mono text-2xl font-bold text-rose-400 tabular-nums">
              {totalExpense.toLocaleString()}
            </span>
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">
            Tournaments, bells, stopwatches & transport
          </span>
        </div>

      </div>

      {/* Segmented View Switcher: Ledger vs Member Dues Compliance */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2 p-1 bg-slate-900 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab('ledger')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              activeTab === 'ledger'
                ? 'bg-amber-400/20 text-amber-300 font-semibold shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Transaction Ledger ({transactions.length})
          </button>
          <button
            onClick={() => setActiveTab('dues')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              activeTab === 'dues'
                ? 'bg-amber-400/20 text-amber-300 font-semibold shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Semester Dues Clearance ({members.length} Members)
          </button>
        </div>

        {activeTab === 'ledger' && (
          <div className="flex items-center gap-2">
            {/* Filter buttons */}
            <div className="hidden sm:flex items-center gap-1 text-xs">
              {(['All', 'Income', 'Expense'] as const).map((type) => (
                <button
                  key={type}
                  onClick={() => setFilterType(type)}
                  className={`px-2.5 py-1 rounded text-xs transition-colors ${
                    filterType === type
                      ? 'bg-slate-800 text-white font-semibold'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search reference or desc..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-amber-500/50 w-44 sm:w-56"
              />
            </div>
          </div>
        )}
      </div>

      {/* Tab 1: Transaction Ledger Table */}
      {activeTab === 'ledger' && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-mono uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Type & Category</th>
                  <th className="py-3 px-4">Description</th>
                  <th className="py-3 px-4">M-Pesa / Bank Ref</th>
                  <th className="py-3 px-4 text-right">Amount (KES)</th>
                  <th className="py-3 px-4">Recorded By</th>
                  <th className="py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredTransactions.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-500">
                      No transactions found matching your criteria.
                    </td>
                  </tr>
                ) : (
                  filteredTransactions.map((txn) => (
                    <tr key={txn.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4 font-mono text-slate-400 whitespace-nowrap">
                        {txn.date}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span
                          className={`font-semibold ${
                            txn.type === 'Income' ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {txn.type}
                        </span>
                        <span className="text-slate-500 mx-1">·</span>
                        <span className="text-slate-300">{txn.category}</span>
                      </td>
                      <td className="py-3 px-4 text-slate-200 max-w-xs truncate">
                        {txn.description}
                      </td>
                      <td className="py-3 px-4 font-mono text-amber-300/90 whitespace-nowrap">
                        {txn.referenceCode}
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-bold whitespace-nowrap tabular-nums">
                        <span
                          className={
                            txn.type === 'Income' ? 'text-emerald-400' : 'text-rose-400'
                          }
                        >
                          {txn.type === 'Income' ? '+' : '-'} {txn.amountKes.toLocaleString()}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                        {txn.recordedBy}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400">
                          <CheckCircle className="w-3 h-3" />
                          <span>{txn.status}</span>
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Member Semester Dues Clearance Tracker */}
      {activeTab === 'dues' && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between text-xs">
            <div>
              <h3 className="font-semibold text-white">Semester 1 Fee: KES 500 per debater</h3>
              <p className="text-slate-400 mt-0.5">
                Funds cover debate bells, printed WUDC adjudication sheets, and subsidized tournament travel.
              </p>
            </div>
            <div className="text-right">
              <span className="font-mono text-emerald-400 font-bold text-sm">
                {members.filter((m) => m.membershipStatus === 'Paid').length} / {members.length}
              </span>
              <span className="text-slate-500 block text-[10px]">Paid Debaters</span>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-mono uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Member Name</th>
                    <th className="py-3 px-4">Student ID</th>
                    <th className="py-3 px-4">Faculty</th>
                    <th className="py-3 px-4">Dues Status</th>
                    <th className="py-3 px-4">M-Pesa Reference</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {members.map((member) => (
                    <tr key={member.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4 font-medium text-slate-200 whitespace-nowrap">
                        {member.fullName}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-400 whitespace-nowrap">
                        {member.studentId}
                      </td>
                      <td className="py-3 px-4 text-slate-300 truncate max-w-xs">
                        {member.faculty}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            member.membershipStatus === 'Paid'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                              : member.membershipStatus === 'Waived'
                              ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
                              : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                          }`}
                        >
                          {member.membershipStatus}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-400 whitespace-nowrap">
                        {member.mpesaRef || '—'}
                      </td>
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        {member.membershipStatus === 'Pending' ? (
                          <button
                            onClick={() => {
                              setVerifyTargetMember(member);
                              setInputMpesaCode('');
                            }}
                            className="px-2.5 py-1 bg-amber-400/20 hover:bg-amber-400/30 text-amber-300 font-semibold rounded text-[11px] border border-amber-400/40 transition-colors"
                          >
                            Verify M-Pesa Code
                          </button>
                        ) : (
                          <span className="text-slate-500 text-[11px]">Cleared</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Record Transaction Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl bg-slate-900 border border-slate-800 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Record Treasury Transaction
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white text-xs"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateTransaction} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">Transaction Type</label>
                  <select
                    value={formType}
                    onChange={(e) => setFormType(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white font-medium"
                  >
                    <option value="Income">Income (+)</option>
                    <option value="Expense">Expense (-)</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Category</label>
                  <select
                    value={formCategory}
                    onChange={(e) => setFormCategory(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white font-medium"
                  >
                    <option value="Semester Dues">Semester Dues</option>
                    <option value="Tournament Registration">Tournament Registration</option>
                    <option value="Logistics & Transport">Logistics & Transport</option>
                    <option value="Equipment & Audio">Equipment & Audio</option>
                    <option value="Merchandise">Merchandise</option>
                    <option value="Sponsorship & Donation">Sponsorship & Donation</option>
                    <option value="Refreshments">Refreshments</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Amount (KES)</label>
                <input
                  type="number"
                  placeholder="e.g. 5000"
                  required
                  value={formAmount}
                  onChange={(e) => setFormAmount(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white font-mono"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Description</label>
                <input
                  type="text"
                  placeholder="e.g. KUDC tournament delegation bus fuel"
                  required
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-white"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">M-Pesa / Bank Reference Code</label>
                <input
                  type="text"
                  placeholder="e.g. QKR992AA31"
                  required
                  value={formRefCode}
                  onChange={(e) => setFormRefCode(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-amber-300 font-mono uppercase"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold rounded"
                >
                  Save to Ledger
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Verify Member Payment Modal */}
      {verifyTargetMember && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl bg-slate-900 border border-slate-800 p-6 shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Verify Dues Payment for {verifyTargetMember.fullName}
            </h3>
            <p className="text-xs text-slate-400">
              Enter the M-Pesa transaction reference received from the member. Once verified, their membership status will update to "Paid" and a KES 500 income transaction will be recorded automatically.
            </p>

            <div>
              <label className="text-[11px] text-slate-400 block mb-1">
                M-Pesa Confirmation Code (10 alphanumeric chars)
              </label>
              <input
                type="text"
                placeholder="e.g. QRT892ZZ19"
                value={inputMpesaCode}
                onChange={(e) => setInputMpesaCode(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-amber-300 font-mono text-sm uppercase"
              />
            </div>

            <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-2 text-xs">
              <button
                onClick={() => setVerifyTargetMember(null)}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmVerification}
                disabled={!inputMpesaCode}
                className="px-4 py-1.5 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 text-white font-bold rounded"
              >
                Confirm & Mark Paid
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};


