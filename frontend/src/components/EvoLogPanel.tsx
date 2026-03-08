import React from 'react';
import { useStore } from '../store/useStore';
import { Dna, CheckCircle2, XCircle, Clock, ChevronRight } from 'lucide-react';
import { EvoLogEntry } from '../types';

const EvoLogPanel = () => {
    const { evoLogs, isHunting } = useStore();

    if (evoLogs.length === 0 && !isHunting) {
        return (
            <div className="glass-panel h-full flex flex-col items-center justify-center text-center p-6 border-white/5 opacity-60">
                <Dna size={32} className="text-slate-500 mb-3" />
                <h3 className="text-sm font-medium text-slate-300">EvoForge Idle</h3>
                <p className="text-xs text-slate-500 mt-1 max-w-[200px]">
                    Mutations will appear here if agents encounter failures and spawn improved variants.
                </p>
            </div>
        );
    }

    const getStatusIcon = (result: EvoLogEntry['result']) => {
        switch (result) {
            case 'success': return <CheckCircle2 size={16} className="text-green-500" />;
            case 'failure': return <XCircle size={16} className="text-rose-500" />;
            default: return <Clock size={16} className="text-amber-500 animate-pulse" />;
        }
    };

    const getScoreColor = (score: number) => {
        if (score >= 90) return 'text-violet-400 bg-violet-400/10 border-violet-400/20';
        if (score >= 70) return 'text-brand-400 bg-brand-400/10 border-brand-400/20';
        if (score >= 50) return 'text-green-400 bg-green-400/10 border-green-400/20';
        if (score > 0) return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
        return 'text-slate-400 bg-surface-800 border-white/10';
    };

    return (
        <div className="glass-panel h-full flex flex-col border-white/5 overflow-hidden">
            <div className="h-12 border-b border-white/5 flex items-center px-4 justify-between bg-surface-900/50 shrink-0">
                <div className="flex items-center gap-2 text-slate-200 font-medium text-sm">
                    <Dna size={16} className="text-brand-400" />
                    EvoForge Mutation Log
                </div>
                <div className="text-xs font-mono text-slate-500 bg-surface-950 px-2 py-1 rounded">
                    {evoLogs.length} Events
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3 relative">
                {/* Connection line behind items */}
                {evoLogs.length > 1 && (
                    <div className="absolute left-6 top-6 bottom-6 w-px bg-white/5 pointer-events-none"></div>
                )}

                {evoLogs.map((log, index) => (
                    <div key={log.id || index} className="relative z-10 flex gap-4 animate-in fade-in slide-in-from-right-4">
                        {/* Timeline dot/icon */}
                        <div className="w-5 h-5 mt-1 shrink-0 rounded-full bg-surface-900 border border-white/10 flex items-center justify-center">
                            {getStatusIcon(log.result)}
                        </div>

                        {/* Content card */}
                        <div className="flex-1 bg-surface-800/50 border border-white/5 rounded-lg p-3 hover:bg-surface-800 transition-colors">
                            <div className="flex justify-between items-start mb-2">
                                <span className="text-xs font-mono text-brand-400 border border-brand-500/20 bg-brand-500/10 px-1.5 py-0.5 rounded">
                                    {log.strategy}
                                </span>
                                {log.score > 0 && (
                                    <span className={`text-xs font-bold px-1.5 py-0.5 rounded border ${getScoreColor(log.score)}`}>
                                        Score: {log.score}
                                    </span>
                                )}
                            </div>

                            {/* Only show original -> mutated if data is present, otherwise simple text */}
                            {log.original_goal && log.mutated_goal ? (
                                <div className="text-xs space-y-2 mt-2">
                                    <div className="text-rose-400/80 line-through truncate" title={log.original_goal}>
                                        {log.original_goal}
                                    </div>
                                    <div className="flex items-center gap-2 text-green-400">
                                        <ChevronRight size={14} className="shrink-0" />
                                        <span className="truncate" title={log.mutated_goal}>{log.mutated_goal}</span>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-xs text-slate-400">
                                    Mutation applied and evaluated.
                                    {log.result === 'pending' && ' Awaiting agent result...'}
                                    {log.result === 'success' && ' Successfully routed around block.'}
                                    {log.result === 'failure' && ' Strategy failed to resolve layout change.'}
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {isHunting && evoLogs.length === 0 && (
                    <div className="text-center text-xs text-slate-500 mt-8 italic">
                        Monitoring agent health...
                    </div>
                )}
            </div>
        </div>
    );
};

export default EvoLogPanel;
