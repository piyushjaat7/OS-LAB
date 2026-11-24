import React, { useState, useMemo } from 'react';
import {
  Layers,
  Search,
  ArrowUpDown,
  Filter,
  ChevronLeft,
  ChevronRight,
  Info,
  X,
  Play,
  Pause,
} from 'lucide-react';
import { useMetrics } from '../context/MetricsContext';
import { api } from '../services/api';
import { ProcessMetrics } from '../types/metrics';
import { formatBytes } from '../utils/formatters';

type SortField = 'cpu_percent' | 'memory_rss' | 'pid' | 'name';
type SortOrder = 'asc' | 'desc';

export const ProcessPage: React.FC = () => {
  const { metrics } = useMetrics();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortField, setSortField] = useState<SortField>('cpu_percent');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);
  const [selectedPid, setSelectedPid] = useState<number | null>(null);
  const [selectedProcess, setSelectedProcess] = useState<ProcessMetrics | null>(null);
  const [loadingModal, setLoadingModal] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);
  const [isPaused, setIsPaused] = useState(false);

  const allProcesses = metrics?.processes?.processes ?? [];

  // Filter and sort
  const filteredProcesses = useMemo(() => {
    return allProcesses
      .filter((proc) => {
        const matchesSearch =
          proc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          String(proc.pid).includes(searchTerm) ||
          (proc.username && proc.username.toLowerCase().includes(searchTerm.toLowerCase()));

        const matchesStatus = statusFilter === 'all' || proc.status.toLowerCase() === statusFilter.toLowerCase();

        return matchesSearch && matchesStatus;
      })
      .sort((a, b) => {
        let aVal = a[sortField];
        let bVal = b[sortField];

        if (aVal === null || aVal === undefined) aVal = 0;
        if (bVal === null || bVal === undefined) bVal = 0;

        if (typeof aVal === 'string') {
          return sortOrder === 'asc'
            ? (aVal as string).localeCompare(bVal as string)
            : (bVal as string).localeCompare(aVal as string);
        }

        return sortOrder === 'asc' ? (aVal as number) - (bVal as number) : (bVal as number) - (aVal as number);
      });
  }, [allProcesses, searchTerm, statusFilter, sortField, sortOrder]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filteredProcesses.length / pageSize));
  const paginatedProcesses = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredProcesses.slice(start, start + pageSize);
  }, [filteredProcesses, currentPage, pageSize]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
    setCurrentPage(1);
  };

  const openProcessDetail = async (pid: number) => {
    setSelectedPid(pid);
    setLoadingModal(true);
    setModalError(null);
    try {
      const data = await api.getProcessByPid(pid);
      setSelectedProcess(data);
    } catch (err: any) {
      setModalError(err.message || 'Process terminated or inaccessible.');
      setSelectedProcess(null);
    } finally {
      setLoadingModal(false);
    }
  };

  const closeProcessDetail = () => {
    setSelectedPid(null);
    setSelectedProcess(null);
    setModalError(null);
  };

  const statuses = Array.from(new Set(allProcesses.map((p) => p.status.toLowerCase())));

  return (
    <div className="space-y-6">
      {/* Action Header & Filtering Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 rounded-xl border border-gray-800 bg-gray-900/60 p-4 backdrop-blur-md">
        {/* Search Input */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search processes by name, PID, or user..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full pl-10 pr-4 py-2 bg-gray-800/60 border border-gray-700/60 rounded-xl text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-cyan-500/60 transition-colors"
          />
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-400 shrink-0" />
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="bg-gray-800/60 border border-gray-700/60 rounded-xl px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-cyan-500/60"
            >
              <option value="all">All Statuses ({allProcesses.length})</option>
              {statuses.map((s) => (
                <option key={s} value={s}>
                  {s.toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold border transition-all ${
              isPaused
                ? 'bg-amber-950/40 border-amber-800/60 text-amber-300'
                : 'bg-gray-800/60 border-gray-700/60 text-gray-300 hover:text-white'
            }`}
          >
            {isPaused ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
            <span>{isPaused ? 'Resume' : 'Pause'}</span>
          </button>
        </div>
      </div>

      {/* Process Table */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/60 backdrop-blur-md overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-gray-800 bg-gray-900/80 text-gray-400 font-semibold uppercase text-[10px] tracking-wider select-none">
              <tr>
                <th
                  onClick={() => handleSort('pid')}
                  className="py-3 px-4 cursor-pointer hover:text-white transition-colors"
                >
                  <div className="flex items-center gap-1.5">
                    <span>PID</span>
                    <ArrowUpDown className="h-3 w-3" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('name')}
                  className="py-3 px-4 cursor-pointer hover:text-white transition-colors"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Process Name</span>
                    <ArrowUpDown className="h-3 w-3" />
                  </div>
                </th>
                <th className="py-3 px-4">Status</th>
                <th
                  onClick={() => handleSort('cpu_percent')}
                  className="py-3 px-4 text-right cursor-pointer hover:text-white transition-colors"
                >
                  <div className="flex items-center justify-end gap-1.5">
                    <span>CPU %</span>
                    <ArrowUpDown className="h-3 w-3" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('memory_rss')}
                  className="py-3 px-4 text-right cursor-pointer hover:text-white transition-colors"
                >
                  <div className="flex items-center justify-end gap-1.5">
                    <span>Memory (RSS)</span>
                    <ArrowUpDown className="h-3 w-3" />
                  </div>
                </th>
                <th className="py-3 px-4 text-right">RAM %</th>
                <th className="py-3 px-4 text-right">Threads</th>
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60 font-mono text-gray-300">
              {paginatedProcesses.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-gray-500 font-sans text-xs">
                    No matching processes found.
                  </td>
                </tr>
              ) : (
                paginatedProcesses.map((proc) => (
                  <tr
                    key={proc.pid}
                    className="hover:bg-gray-800/40 transition-colors cursor-pointer group"
                    onClick={() => openProcessDetail(proc.pid)}
                  >
                    <td className="py-3 px-4 font-semibold text-gray-400 group-hover:text-cyan-400">
                      {proc.pid}
                    </td>
                    <td className="py-3 px-4 font-sans font-medium text-white max-w-[200px] truncate">
                      {proc.name}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center rounded-md bg-gray-800 px-2 py-0.5 text-[10px] text-gray-300 capitalize font-sans">
                        {proc.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right text-cyan-400 font-semibold">
                      {proc.cpu_percent !== null && proc.cpu_percent !== undefined
                        ? `${proc.cpu_percent.toFixed(1)}%`
                        : '0.0%'}
                    </td>
                    <td className="py-3 px-4 text-right font-medium">
                      {formatBytes(proc.memory_rss)}
                    </td>
                    <td className="py-3 px-4 text-right text-purple-400 font-medium">
                      {proc.memory_percent.toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-right text-gray-400">{proc.num_threads}</td>
                    <td className="py-3 px-4 text-gray-400 font-sans text-[11px] truncate max-w-[120px]">
                      {proc.username ?? '-'}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          openProcessDetail(proc.pid);
                        }}
                        className="p-1 rounded hover:bg-gray-700 text-gray-400 hover:text-cyan-400 transition-colors"
                        title="View Process Details"
                      >
                        <Info className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border-t border-gray-800 bg-gray-900/40 text-xs text-gray-400">
          <div className="flex items-center gap-2">
            <span>Showing</span>
            <span className="font-semibold text-white">
              {filteredProcesses.length > 0 ? (currentPage - 1) * pageSize + 1 : 0}
            </span>
            <span>to</span>
            <span className="font-semibold text-white">
              {Math.min(currentPage * pageSize, filteredProcesses.length)}
            </span>
            <span>of</span>
            <span className="font-semibold text-white">{filteredProcesses.length}</span>
            <span>processes</span>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span>Per page:</span>
              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-white"
              >
                <option value={15}>15</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
              </select>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-1.5 rounded border border-gray-700 bg-gray-800 text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="px-2 font-mono">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="p-1.5 rounded border border-gray-700 bg-gray-800 text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Single Process Inspection Modal */}
      {selectedPid !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-gray-800 bg-[#0F172A] p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-gray-800">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  <Layers className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">
                    Process #{selectedPid}
                  </h3>
                  <p className="text-xs text-gray-400 font-mono">
                    {selectedProcess?.name ?? 'Telemetry Inspection'}
                  </p>
                </div>
              </div>
              <button
                onClick={closeProcessDetail}
                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {loadingModal ? (
              <div className="py-8 text-center text-xs text-cyan-400">
                Retrieving detailed process metrics...
              </div>
            ) : modalError ? (
              <div className="p-4 rounded-xl border border-rose-800/40 bg-rose-950/20 text-rose-300 text-xs">
                {modalError}
              </div>
            ) : selectedProcess ? (
              <div className="space-y-4 font-sans text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-gray-900 border border-gray-800">
                    <span className="text-[10px] text-gray-500 uppercase font-semibold">Status</span>
                    <p className="font-bold text-white capitalize mt-0.5">{selectedProcess.status}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-900 border border-gray-800">
                    <span className="text-[10px] text-gray-500 uppercase font-semibold">Username</span>
                    <p className="font-bold text-white mt-0.5">{selectedProcess.username ?? 'N/A'}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-900 border border-gray-800">
                    <span className="text-[10px] text-gray-500 uppercase font-semibold">CPU Utilization</span>
                    <p className="font-bold text-cyan-400 mt-0.5 font-mono">
                      {selectedProcess.cpu_percent !== null ? `${selectedProcess.cpu_percent.toFixed(1)}%` : '0.0%'}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-900 border border-gray-800">
                    <span className="text-[10px] text-gray-500 uppercase font-semibold">RAM Utilization</span>
                    <p className="font-bold text-purple-400 mt-0.5 font-mono">
                      {selectedProcess.memory_percent.toFixed(2)}%
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-900 border border-gray-800">
                    <span className="text-[10px] text-gray-500 uppercase font-semibold">Memory RSS (Resident)</span>
                    <p className="font-bold text-white mt-0.5 font-mono">{formatBytes(selectedProcess.memory_rss)}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-900 border border-gray-800">
                    <span className="text-[10px] text-gray-500 uppercase font-semibold">Memory VMS (Virtual)</span>
                    <p className="font-bold text-white mt-0.5 font-mono">{formatBytes(selectedProcess.memory_vms)}</p>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-gray-900 border border-gray-800 flex justify-between items-center">
                  <span className="text-gray-400">Active Execution Threads:</span>
                  <span className="font-mono font-bold text-white">{selectedProcess.num_threads}</span>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
