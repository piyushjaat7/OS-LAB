import React from 'react';
import {
  Activity,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Cpu,
  Database,
  HardDrive,
  History,
  Layers,
  Network,
  Settings,
  Sliders,
  Terminal,
} from 'lucide-react';

export type PageId =
  | 'overview'
  | 'cpu'
  | 'memory'
  | 'disk'
  | 'network'
  | 'processes'
  | 'analysis'
  | 'scheduling'
  | 'history'
  | 'settings';

interface SidebarProps {
  activePage: PageId;
  onPageChange: (page: PageId) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activePage,
  onPageChange,
  collapsed,
  onToggleCollapse,
}) => {
  const navItems = [
    { id: 'overview' as PageId, label: 'Overview', icon: Activity },
    { id: 'cpu' as PageId, label: 'CPU Monitoring', icon: Cpu },
    { id: 'memory' as PageId, label: 'Memory Monitoring', icon: Database },
    { id: 'disk' as PageId, label: 'Disk Storage', icon: HardDrive },
    { id: 'network' as PageId, label: 'Network I/O', icon: Network },
    { id: 'processes' as PageId, label: 'Processes', icon: Layers },
    { id: 'analysis' as PageId, label: 'Performance Analysis', icon: AlertTriangle },
    { id: 'scheduling' as PageId, label: 'CPU Scheduling', icon: Sliders },
    { id: 'history' as PageId, label: 'Historical Analytics', icon: History },
    { id: 'settings' as PageId, label: 'Settings', icon: Settings },
  ];

  return (
    <aside
      className={`fixed top-0 bottom-0 left-0 z-40 flex flex-col bg-[#0D1322]/90 backdrop-blur-xl border-r border-gray-800 transition-all duration-300 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-gray-800/80">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/20">
            <Terminal className="h-5 w-5" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-bold text-sm text-white tracking-wide truncate">
                OS Analyzer
              </span>
              <span className="text-[10px] uppercase font-semibold tracking-wider text-cyan-400">
                Capstone System
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1.5 custom-scrollbar">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onPageChange(item.id)}
              title={collapsed ? item.label : undefined}
              className={`w-full flex items-center gap-3.5 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group relative ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/10 text-cyan-300 border border-cyan-500/30 shadow-md shadow-cyan-950/30'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
              }`}
            >
              <Icon
                className={`h-5 w-5 shrink-0 transition-colors ${
                  isActive ? 'text-cyan-400' : 'text-gray-400 group-hover:text-gray-200'
                }`}
              />
              {!collapsed && <span className="truncate">{item.label}</span>}
              {isActive && (
                <span className="absolute right-2 h-1.5 w-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee]" />
              )}
            </button>
          );
        })}
      </nav>

      {/* Collapse Toggle Footer */}
      <div className="p-3 border-t border-gray-800/80">
        <button
          onClick={onToggleCollapse}
          className="w-full flex items-center justify-center gap-2 p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800/60 transition-colors text-xs font-medium"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4" />
              <span>Collapse Sidebar</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
};
