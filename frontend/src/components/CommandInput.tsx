import React, { useState } from 'react';
import { Send, Sparkles, Loader2 } from 'lucide-react';
import { useStore } from '../store/useStore';
import { apiClient } from '../api/client';
import toast from 'react-hot-toast';

const SUGGESTIONS = [
    "Find STEM education grants in California for nonprofits",
    "Environmental conservation grants for climate initiatives",
    "Rural healthcare grants for free clinics serving uninsured adults",
    "Seed funding for AI technology startups in New York"
];

const CommandInput = () => {
    const [command, setCommand] = useState('');
    const [showSuggestions, setShowSuggestions] = useState(false);
    const {
        orgProfile,
        setCurrentSession,
        setIsHunting,
        setHuntPhase,
        resetSessionData,
        addStreamingUrl,
        addGrant,
        addEvoLog,
        isHunting
    } = useStore();

    const handleHunt = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!command.trim() || !orgProfile) return;

        resetSessionData();
        setIsHunting(true);
        setHuntPhase('Initializing AetherForge...');
        setShowSuggestions(false);

        try {
            // POST to start the SSE stream
            const res = await fetch('/api/hunt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ org_id: orgProfile.id, command })
            });

            if (!res.ok) throw new Error(await res.text());
            if (!res.body) throw new Error("No readable stream available");

            const sessionId = res.headers.get('X-Session-Id');
            const shareToken = res.headers.get('X-Share-Token');

            if (sessionId) {
                setCurrentSession({
                    id: sessionId,
                    org_id: orgProfile.id,
                    command,
                    status: 'running',
                    grants_found: 0,
                    share_token: shareToken || undefined
                });
            }

            // Read SSE stream
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop() || ''; // Keep the last incomplete chunk in the buffer

                for (const line of lines) {
                    if (line.trim().startsWith('data: ')) {
                        try {
                            const dataStr = line.replace('data: ', '').trim();
                            const eventInfo = JSON.parse(dataStr);
                            handleSSE(eventInfo);
                        } catch (err) {
                            console.error("Failed to parse SSE line:", line, err);
                        }
                    }
                }
            }
        } catch (err: any) {
            toast.error('Hunt failed: ' + err.message);
            setIsHunting(false);
            setHuntPhase('Error');
        }
    };

    const handleSSE = (info: any) => {
        switch (info.event) {
            case 'STARTED':
                setHuntPhase('Scanning Portals');
                break;
            case 'SCANNING':
                setHuntPhase(`Scanning ${info.portals?.length || 0} Portals...`);
                break;
            case 'STREAMING_URL':
                addStreamingUrl({ url: info.url, cellId: info.cell_id, portal: info.portal || info.strategy });
                break;
            case 'MATCH_FOUND':
                if (info.grant) addGrant(info.grant);
                break;
            case 'EVO_MUTATION':
                toast(`EvoForge analyzing failure (Attempt ${info.attempt})`, { icon: '🧬' });
                break;
            case 'EVO_RESULT':
                addEvoLog({
                    id: String(Date.now()),
                    session_id: info.session_id,
                    attempt: 0,
                    original_goal: '',
                    mutated_goal: '',
                    strategy: info.strategy,
                    score: info.score,
                    result: info.result
                });
                break;
            case 'AKASHA_HIT':
                toast.success(`Akasha Ledger: Reusing ${info.template}`);
                break;
            case 'COMPLETE':
                setIsHunting(false);
                setHuntPhase('Complete');
                toast.success(`Hunt Complete! Found ${info.grants_found} grants.`);
                // Refresh session to get completed_at from DB
                apiClient.getSession(info.session_id).then(setCurrentSession).catch(console.error);
                break;
            case 'ERROR':
                toast.error(`Agent Error: ${info.message}`);
                setIsHunting(false);
                setHuntPhase('Error');
                break;
        }
    };

    return (
        <div className="relative w-full z-20">
            <form onSubmit={handleHunt} className="relative group">
                <div className={`absolute inset-0 bg-brand-500/20 blur-xl rounded-2xl transition-opacity duration-500 ${isHunting ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}></div>
                <div className="relative glass-panel rounded-2xl p-2 flex items-center bg-surface-900/90 border-white/20">
                    <div className="pl-4 pr-2 text-brand-400">
                        {isHunting ? <Loader2 className="animate-spin" size={24} /> : <Sparkles size={24} />}
                    </div>
                    <input
                        type="text"
                        className="flex-1 bg-transparent border-none text-white placeholder:text-slate-500 h-12 outline-none text-lg px-2"
                        placeholder={isHunting ? 'AetherForge agents are hunting...' : 'Describe the grants you need...'}
                        value={command}
                        onChange={(e) => setCommand(e.target.value)}
                        onFocus={() => setShowSuggestions(true)}
                        onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                        disabled={isHunting}
                    />
                    <button
                        type="submit"
                        disabled={isHunting || !command.trim()}
                        className="h-12 w-12 flex items-center justify-center rounded-xl bg-brand-600 hover:bg-brand-500 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors mr-1 shrink-0 shadow-lg shadow-brand-500/30"
                    >
                        <Send size={20} />
                    </button>
                </div>
            </form>

            {/* Auto-suggest dropdown */}
            {showSuggestions && !isHunting && (
                <div className="absolute top-16 left-0 right-0 glass-panel rounded-xl py-2 mt-2 shadow-2xl z-30 animate-in fade-in slide-in-from-top-2">
                    {SUGGESTIONS.map((sug, i) => (
                        <button
                            key={i}
                            className="w-full text-left px-6 py-3 hover:bg-surface-800 text-slate-300 hover:text-white transition-colors flex items-center gap-3"
                            onMouseDown={(e) => {
                                e.preventDefault();
                                setCommand(sug);
                                setShowSuggestions(false);
                            }}
                        >
                            <SearchIcon className="text-slate-500 shrink-0" size={16} />
                            <span className="truncate">{sug}</span>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};

// Helper icon
const SearchIcon = ({ className, size }: { className?: string; size: number }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg>
);

export default CommandInput;
