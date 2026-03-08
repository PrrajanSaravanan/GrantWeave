import React, { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import { apiClient } from '../api/client';
import { WrappedReport } from '../types';
import { Calendar, Target, Dna, Share2, Sparkles, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

const GrantWrapped = () => {
    const { orgProfile } = useStore();
    const [report, setReport] = useState<WrappedReport | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!orgProfile?.id) return;
        const fetchWrapped = async () => {
            try {
                setLoading(true);
                const data = await apiClient.getWrappedReport(orgProfile.id);
                setReport(data);
            } catch (e: any) {
                toast.error("Failed to generate Wrapped report: " + e.message);
            } finally {
                setLoading(false);
            }
        };
        fetchWrapped();
    }, [orgProfile]);

    if (loading) {
        return (
            <div className="w-full h-full min-h-[500px] flex flex-col items-center justify-center text-slate-400">
                <Loader2 size={48} className="animate-spin text-brand-500 mb-4" />
                <p>AetherForge is compiling your weekly metrics...</p>
            </div>
        );
    }

    if (!report) {
        return (
            <div className="w-full h-full min-h-[500px] flex items-center justify-center text-slate-500">
                <p>No wrapped data available yet. Run some hunts first!</p>
            </div>
        );
    }

    const { data } = report;

    return (
        <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in zoom-in-95 duration-700">
            {/* Header */}
            <div className="text-center space-y-4 mb-12 relative">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-brand-500/20 rounded-[100%] blur-[100px] pointer-events-none"></div>
                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 font-medium mb-4">
                    <Sparkles size={16} />
                    GrantWeave Wrapped — {report.week_of}
                </div>
                <h1 className="text-5xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-brand-200 to-white">
                    Your Week in Grants
                </h1>
                <p className="text-xl text-slate-400">
                    Here's what AetherForge and your web agents accomplished.
                </p>
            </div>

            {/* Main Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="glass-panel p-8 text-center bg-gradient-to-b from-surface-800 to-surface-900 border-t-2 border-t-brand-500 transform hover:-translate-y-1 transition-transform">
                    <Target size={32} className="mx-auto text-brand-400 mb-4" />
                    <div className="text-5xl font-black text-white mb-2">{report.grants_found}</div>
                    <div className="text-slate-400 font-medium uppercase tracking-wider text-sm">Target Grants Found</div>
                </div>

                <div className="glass-panel p-8 text-center bg-gradient-to-b from-surface-800 to-surface-900 border-t-2 border-t-violet-500 transform hover:-translate-y-1 transition-transform">
                    <Dna size={32} className="mx-auto text-violet-400 mb-4" />
                    <div className="text-5xl font-black text-white mb-2">{report.mutations_run}</div>
                    <div className="text-slate-400 font-medium uppercase tracking-wider text-sm">EvoForge Mutations</div>
                </div>

                <div className="glass-panel p-8 text-center bg-gradient-to-b from-surface-800 to-surface-900 border-t-2 border-t-cyan-500 transform hover:-translate-y-1 transition-transform">
                    <Calendar size={32} className="mx-auto text-cyan-400 mb-4" />
                    <div className="text-5xl font-black text-white mb-2">{data.portals_scanned}</div>
                    <div className="text-slate-400 font-medium uppercase tracking-wider text-sm">Portals Scanned</div>
                </div>
            </div>

            {/* Fun Facts & Best Match */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass-panel p-8 relative overflow-hidden">
                    <div className="absolute right-0 top-0 w-32 h-32 bg-amber-500/10 blur-[50px]"></div>
                    <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                        <Sparkles className="text-amber-400" /> Top Match of the Week
                    </h3>
                    <div className="bg-surface-950/50 p-6 rounded-xl border border-white/5">
                        <div className="text-2xl font-bold text-slate-100 mb-2">{report.best_match || 'No grants found yet'}</div>
                        {data.top_grants[0] && (
                            <div className="text-brand-400 font-medium">{data.top_grants[0].amount}</div>
                        )}
                    </div>
                </div>

                <div className="glass-panel p-8">
                    <h3 className="text-xl font-bold mb-6">AetherForge Insights</h3>
                    <ul className="space-y-4">
                        {data.fun_facts.map((fact, i) => (
                            <li key={i} className="flex gap-3 text-slate-300">
                                <div className="w-1.5 h-1.5 rounded-full bg-brand-500 mt-2 shrink-0"></div>
                                {fact}
                            </li>
                        ))}
                    </ul>
                </div>
            </div>

            {/* Share Button Placeholder */}
            <div className="flex justify-center pt-8 pb-12">
                <button
                    onClick={() => {
                        navigator.clipboard.writeText(window.location.href);
                        toast.success('Wrapped link copied to share!');
                    }}
                    className="btn-primary flex items-center gap-2 px-8 py-4 text-lg rounded-full"
                >
                    <Share2 size={20} />
                    Share Your Wrapped
                </button>
            </div>
        </div>
    );
};

export default GrantWrapped;
