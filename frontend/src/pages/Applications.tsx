import React, { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import { apiClient } from '../api/client';
import { Session, GrantResult } from '../types';
import { Folder, Clock, CheckCircle2, XCircle, Search, ExternalLink } from 'lucide-react';
import toast from 'react-hot-toast';

const Applications = () => {
    const { currentSession, orgProfile } = useStore();
    const [sessions, setSessions] = useState<Session[]>([]);
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
    const [sessionGrants, setSessionGrants] = useState<GrantResult[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [search, setSearch] = useState('');

    // Load all sessions
    useEffect(() => {
        const load = async () => {
            try {
                const res = await apiClient.getSessions(50);
                // Sort descending by start time conceptually (DB already does it)
                setSessions(res.sessions);
                if (res.sessions.length > 0 && !selectedSessionId) {
                    setSelectedSessionId(res.sessions[0].id);
                }
            } catch (e: any) {
                toast.error("Failed to load sessions: " + e.message);
            } finally {
                setIsLoading(false);
            }
        };
        load();
    }, [currentSession]); // reload if current session changes

    // Load grants for selected session
    useEffect(() => {
        if (!selectedSessionId) {
            setSessionGrants([]);
            return;
        }
        const loadGrants = async () => {
            try {
                setIsLoading(true);
                const res = await apiClient.getGrants(selectedSessionId);
                setSessionGrants(res.grants);
            } catch (e) {
                // Handle silently
            } finally {
                setIsLoading(false);
            }
        };
        loadGrants();
    }, [selectedSessionId]);

    const filteredGrants = sessionGrants.filter(g =>
        g.title.toLowerCase().includes(search.toLowerCase()) ||
        (g.funder && g.funder.toLowerCase().includes(search.toLowerCase()))
    );

    const getStatusIcon = (status: string) => {
        if (status === 'running') return <Clock size={14} className="text-amber-400" />;
        if (status === 'completed') return <CheckCircle2 size={14} className="text-brand-400" />;
        if (status === 'failed') return <XCircle size={14} className="text-rose-400" />;
        return <Folder size={14} className="text-slate-400" />;
    };

    return (
        <div className="h-full flex p-6 gap-6 max-w-[1600px] mx-auto">

            {/* Sessions Sidebar */}
            <div className="w-80 flex flex-col gap-4">
                <h2 className="text-xl font-bold flex items-center gap-2">
                    <Folder size={24} className="text-brand-400" />
                    Hunt History
                </h2>

                <div className="glass-panel flex-1 overflow-y-auto p-2 space-y-2 border-white/5">
                    {sessions.map(s => (
                        <button
                            key={s.id}
                            onClick={() => setSelectedSessionId(s.id)}
                            className={`w-full text-left p-3 rounded-lg border transition-all ${selectedSessionId === s.id
                                    ? 'bg-brand-500/10 border-brand-500/30'
                                    : 'bg-surface-800/50 border-transparent hover:bg-surface-800'
                                }`}
                        >
                            <div className="flex justify-between items-start mb-1">
                                <span className="text-sm font-medium text-slate-200 truncate pr-2">
                                    {s.command || "Unknown Hunt"}
                                </span>
                            </div>
                            <div className="flex items-center justify-between text-xs text-slate-500">
                                <div className="flex items-center gap-1.5">
                                    {getStatusIcon(s.status)}
                                    <span className="capitalize">{s.status}</span>
                                </div>
                                <span>{s.grants_found} Found</span>
                            </div>
                            <div className="text-[10px] text-slate-600 mt-2 font-mono">
                                ID: {s.id.substring(0, 8)}...
                            </div>
                        </button>
                    ))}
                    {sessions.length === 0 && !isLoading && (
                        <div className="text-center text-slate-500 p-4 text-sm mt-10">
                            No previous hunts found.
                        </div>
                    )}
                </div>
            </div>

            {/* Main Grants Area */}
            <div className="flex-1 flex flex-col gap-4">
                <div className="flex justify-between items-end">
                    <div>
                        <h1 className="text-3xl font-bold mb-1">Grant Portfolio</h1>
                        <p className="text-slate-400 text-sm">Review, export, and auto-fill applications.</p>
                    </div>

                    <div className="relative w-72">
                        <Search className="absolute left-3 top-2.5 text-slate-400" size={18} />
                        <input
                            type="text"
                            placeholder="Search grants..."
                            className="input-field w-full pl-10 h-10"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                </div>

                <div className="glass-panel flex-1 overflow-auto border-white/5 p-4 relative">
                    {isLoading && (
                        <div className="absolute inset-0 bg-surface-900/50 backdrop-blur-sm z-10 flex items-center justify-center">
                            <div className="w-10 h-10 border-2 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
                        </div>
                    )}

                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                        {filteredGrants.map(grant => (
                            <div key={grant.id} className="bg-surface-800 border border-white/5 p-5 rounded-xl flex flex-col">
                                <div className="flex justify-between items-start mb-2">
                                    <h3 className="font-semibold text-lg text-slate-100 flex-1 pr-4 leading-tight">
                                        {grant.title}
                                    </h3>
                                    <div className={`px-2 py-1 rounded text-xs font-bold whitespace-nowrap ${grant.match_score >= 80 ? 'bg-brand-500/20 text-brand-300' :
                                            'bg-amber-500/20 text-amber-300'
                                        }`}>
                                        {grant.match_score}% Match
                                    </div>
                                </div>

                                <div className="text-sm text-slate-400 mb-4 h-10 line-clamp-2">
                                    {grant.description || 'No description provided.'}
                                </div>

                                <div className="mt-auto grid grid-cols-2 gap-4 text-sm mb-4">
                                    <div>
                                        <span className="block text-xs text-slate-500 mb-0.5">Funder</span>
                                        <span className="font-medium text-slate-300 truncate block">
                                            {grant.funder || 'Unknown'}
                                        </span>
                                    </div>
                                    <div>
                                        <span className="block text-xs text-slate-500 mb-0.5">Amount</span>
                                        <span className="font-medium text-green-400">{grant.amount || 'Variable'}</span>
                                    </div>
                                    <div>
                                        <span className="block text-xs text-slate-500 mb-0.5">Deadline</span>
                                        <span className="font-medium text-slate-300">{grant.deadline || 'Rolling'}</span>
                                    </div>
                                    <div>
                                        <span className="block text-xs text-slate-500 mb-0.5">Focus</span>
                                        <span className="font-medium text-slate-300">{grant.category || 'General'}</span>
                                    </div>
                                </div>

                                <div className="flex items-center gap-3 pt-4 border-t border-white/5">
                                    <button className="flex-1 btn-primary py-1.5 text-sm">
                                        Auto-Fill via EvoForge
                                    </button>
                                    {grant.url && (
                                        <a
                                            href={grant.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="btn-secondary px-3 py-1.5 flex items-center justify-center text-slate-400 hover:text-white"
                                            title="Open Grant Portal"
                                        >
                                            <ExternalLink size={16} />
                                        </a>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>

                    {!isLoading && filteredGrants.length === 0 && (
                        <div className="h-full flex flex-col items-center justify-center text-slate-500">
                            <Folder size={48} className="mb-4 opacity-50" />
                            <p>No grants found in this session.</p>
                        </div>
                    )}
                </div>
            </div>

        </div>
    );
};

export default Applications;
