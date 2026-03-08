import React from 'react';
import { useStore } from '../store/useStore';
import { Maximize2, Terminal, AlertCircle } from 'lucide-react';

const LiveBrowserGrid = () => {
    const { streamingUrls, isHunting, huntPhase } = useStore();

    // Show an empty state or loading state if no URLs yet
    if (streamingUrls.length === 0) {
        return (
            <div className="w-full h-full glass-panel flex border border-white/5 bg-surface-900/50 items-center justify-center p-6 text-center">
                {isHunting ? (
                    <div className="flex flex-col items-center">
                        <div className="relative mb-4">
                            <div className="w-16 h-16 border-2 border-brand-500/30 rounded-full animate-spin border-t-brand-500"></div>
                            <div className="absolute inset-0 flex items-center justify-center">
                                <Terminal size={20} className="text-brand-400" />
                            </div>
                        </div>
                        <h3 className="text-lg font-medium text-slate-200 mb-1">{huntPhase}</h3>
                        <p className="text-sm text-slate-500 max-w-sm">
                            Weave Mesh is coordinating agents. Live browser views will appear here once scanning begins.
                        </p>
                    </div>
                ) : (
                    <div className="flex flex-col items-center opacity-50">
                        <Maximize2 size={32} className="text-slate-500 mb-3" />
                        <p className="text-sm font-medium text-slate-400">Live Agent Feeds</p>
                        <p className="text-xs text-slate-500 mt-1">Awaiting command</p>
                    </div>
                )}
            </div>
        );
    }

    // Determine grid layout based on number of active feeds
    const getGridClass = (count: number) => {
        if (count === 1) return 'grid-cols-1';
        if (count === 2) return 'grid-cols-2';
        if (count <= 4) return 'grid-cols-2 grid-rows-2';
        return 'grid-cols-3 grid-rows-2'; // Max 6 typically
    };

    return (
        <div className={`w-full h-full grid gap-4 ${getGridClass(streamingUrls.length)}`}>
            {streamingUrls.slice(0, 6).map((feed, i) => (
                <div key={i} className="glass-panel overflow-hidden border border-white/10 relative group flex flex-col bg-black">
                    {/* Header Bar */}
                    <div className="h-8 bg-surface-900 border-b border-white/10 flex items-center px-3 justify-between shrink-0">
                        <div className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse"></span>
                            <span className="text-xs font-mono text-slate-300 truncate max-w-[150px]">
                                {feed.portal || `Agent-${feed.cellId?.substring(0, 6) || i}`}
                            </span>
                        </div>
                        <div className="flex gap-1.5 opacity-50 hover:opacity-100 transition-opacity">
                            <div className="w-2.5 h-2.5 rounded-full bg-slate-600"></div>
                            <div className="w-2.5 h-2.5 rounded-full bg-slate-600"></div>
                            <div className="w-2.5 h-2.5 rounded-full bg-slate-600"></div>
                        </div>
                    </div>

                    {/* Main Iframe */}
                    <div className="flex-1 relative bg-surface-950">
                        {feed.url ? (
                            <iframe
                                src={feed.url}
                                className="absolute inset-0 w-full h-full border-none pointer-events-none"
                                title={`TinyFish Feed ${i}`}
                                sandbox="allow-scripts allow-same-origin"
                            />
                        ) : (
                            <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500">
                                <AlertCircle className="mb-2" size={24} />
                                <span className="text-xs">No stream URL</span>
                            </div>
                        )}

                        {/* Scanline effect overlay */}
                        <div className="absolute inset-0 bg-[linear-gradient(transparent_50%,rgba(0,0,0,0.1)_50%)] bg-[length:100%_4px] pointer-events-none opacity-20 hidden group-hover:block"></div>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default LiveBrowserGrid;
