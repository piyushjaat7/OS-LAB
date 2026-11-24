import React, { useState } from 'react';
import { Save, RotateCcw, Sliders, ShieldAlert, Server } from 'lucide-react';
import { useMetrics } from '../context/MetricsContext';

export const SettingsPage: React.FC = () => {
  const { settings, updateSettings } = useMetrics();
  const [formData, setFormData] = useState(settings);
  const [savedMessage, setSavedMessage] = useState(false);

  const handleChange = (key: keyof typeof settings, val: number) => {
    setFormData((prev) => ({ ...prev, [key]: val }));
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    updateSettings(formData);
    setSavedMessage(true);
    setTimeout(() => setSavedMessage(false), 2500);
  };

  const handleReset = () => {
    const defaults = {
      cpuWarning: 75,
      cpuCritical: 90,
      memoryWarning: 80,
      memoryCritical: 95,
      diskWarning: 80,
      diskCritical: 90,
      chartHistoryLength: 30,
      streamInterval: 1.0,
    };
    setFormData(defaults);
    updateSettings(defaults);
    setSavedMessage(true);
    setTimeout(() => setSavedMessage(false), 2500);
  };

  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-gray-800">
        <div>
          <h2 className="text-base font-bold text-white">Dashboard & Alert Settings</h2>
          <p className="text-xs text-gray-400">Configure real-time monitoring thresholds and telemetry streaming</p>
        </div>
        {savedMessage && (
          <span className="text-xs font-semibold text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-3 py-1 rounded-full">
            Settings Saved Successfully
          </span>
        )}
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Resource Warning Thresholds */}
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md space-y-5">
          <div className="flex items-center gap-2.5 pb-3 border-b border-gray-800 text-white font-semibold text-sm">
            <ShieldAlert className="h-4 w-4 text-cyan-400" />
            <span>Resource Alert Thresholds (%)</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* CPU Thresholds */}
            <div className="space-y-3">
              <label className="text-xs font-semibold text-gray-300 block">CPU Load Thresholds</label>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <span className="text-[11px] text-amber-400 block mb-1">Warning (%)</span>
                  <input
                    type="number"
                    min={10}
                    max={99}
                    value={formData.cpuWarning}
                    onChange={(e) => handleChange('cpuWarning', Number(e.target.value))}
                    className="w-full bg-gray-800/80 border border-gray-700/60 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>
                <div>
                  <span className="text-[11px] text-rose-400 block mb-1">Critical (%)</span>
                  <input
                    type="number"
                    min={10}
                    max={100}
                    value={formData.cpuCritical}
                    onChange={(e) => handleChange('cpuCritical', Number(e.target.value))}
                    className="w-full bg-gray-800/80 border border-gray-700/60 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Memory Thresholds */}
            <div className="space-y-3">
              <label className="text-xs font-semibold text-gray-300 block">RAM Memory Thresholds</label>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <span className="text-[11px] text-amber-400 block mb-1">Warning (%)</span>
                  <input
                    type="number"
                    min={10}
                    max={99}
                    value={formData.memoryWarning}
                    onChange={(e) => handleChange('memoryWarning', Number(e.target.value))}
                    className="w-full bg-gray-800/80 border border-gray-700/60 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>
                <div>
                  <span className="text-[11px] text-rose-400 block mb-1">Critical (%)</span>
                  <input
                    type="number"
                    min={10}
                    max={100}
                    value={formData.memoryCritical}
                    onChange={(e) => handleChange('memoryCritical', Number(e.target.value))}
                    className="w-full bg-gray-800/80 border border-gray-700/60 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Disk Thresholds */}
            <div className="space-y-3">
              <label className="text-xs font-semibold text-gray-300 block">Disk Storage Thresholds</label>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <span className="text-[11px] text-amber-400 block mb-1">Warning (%)</span>
                  <input
                    type="number"
                    min={10}
                    max={99}
                    value={formData.diskWarning}
                    onChange={(e) => handleChange('diskWarning', Number(e.target.value))}
                    className="w-full bg-gray-800/80 border border-gray-700/60 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>
                <div>
                  <span className="text-[11px] text-rose-400 block mb-1">Critical (%)</span>
                  <input
                    type="number"
                    min={10}
                    max={100}
                    value={formData.diskCritical}
                    onChange={(e) => handleChange('diskCritical', Number(e.target.value))}
                    className="w-full bg-gray-800/80 border border-gray-700/60 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Telemetry Stream Settings */}
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md space-y-4">
          <div className="flex items-center gap-2.5 pb-3 border-b border-gray-800 text-white font-semibold text-sm">
            <Sliders className="h-4 w-4 text-cyan-400" />
            <span>Live Streaming Preferences</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="text-xs font-semibold text-gray-300 block mb-1">
                WebSocket Stream Sampling Rate
              </label>
              <select
                value={formData.streamInterval}
                onChange={(e) => handleChange('streamInterval', Number(e.target.value))}
                className="w-full bg-gray-800/80 border border-gray-700/60 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
              >
                <option value={0.5}>0.5 seconds (2 Hz, high frequency)</option>
                <option value={1.0}>1.0 second (1 Hz, standard default)</option>
                <option value={2.0}>2.0 seconds (0.5 Hz, balanced)</option>
                <option value={5.0}>5.0 seconds (0.2 Hz, low overhead)</option>
              </select>
              <p className="text-[11px] text-gray-400 mt-1">Controls how often FastAPI streams fresh metrics snapshots.</p>
            </div>

            <div>
              <label className="text-xs font-semibold text-gray-300 block mb-1">
                Live Chart Points Buffer
              </label>
              <select
                value={formData.chartHistoryLength}
                onChange={(e) => handleChange('chartHistoryLength', Number(e.target.value))}
                className="w-full bg-gray-800/80 border border-gray-700/60 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
              >
                <option value={20}>20 points (~20s)</option>
                <option value={30}>30 points (~30s, standard)</option>
                <option value={60}>60 points (~1 minute)</option>
              </select>
              <p className="text-[11px] text-gray-400 mt-1">Number of rolling samples retained in browser memory for charts.</p>
            </div>
          </div>
        </div>

        {/* Backend & Environment Metadata */}
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md space-y-3">
          <div className="flex items-center gap-2.5 pb-2 text-white font-semibold text-sm">
            <Server className="h-4 w-4 text-purple-400" />
            <span>Environment Connectivity</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
            <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-800">
              <span className="text-[10px] text-gray-500 uppercase block font-sans">REST Base URL</span>
              <span className="text-gray-300 break-all">{baseUrl}</span>
            </div>
            <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-800">
              <span className="text-[10px] text-gray-500 uppercase block font-sans">WebSocket URL</span>
              <span className="text-gray-300 break-all">
                {baseUrl.replace(/^http/, 'ws')}/api/v1/system/ws
              </span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold text-xs shadow-lg shadow-cyan-500/20 hover:from-cyan-400 hover:to-blue-500 transition-all active:scale-95"
          >
            <Save className="h-4 w-4" />
            <span>Save Preferences</span>
          </button>

          <button
            type="button"
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-gray-700 bg-gray-800/60 text-gray-300 hover:text-white hover:bg-gray-700/60 font-semibold text-xs transition-all active:scale-95"
          >
            <RotateCcw className="h-4 w-4" />
            <span>Reset Defaults</span>
          </button>
        </div>
      </form>
    </div>
  );
};
