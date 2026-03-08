import React from 'react';
import CommandInput from '../components/CommandInput';
import GrantMindMap from '../components/GrantMindMap';
import LiveBrowserGrid from '../components/LiveBrowserGrid';
import EvoLogPanel from '../components/EvoLogPanel';
import TeamHandoff from '../components/TeamHandoff';
import ExportPanel from '../components/ExportPanel';
import { useStore } from '../store/useStore';
import { Target, Layers, Cpu } from 'lucide-react';

const Dashboard = () => {
    const { isHunting, currentSession, grants } = useStore();

    return (
        <div className="h-full flex flex-col p-6 gap-6 relative max-w-[1600px] mx-auto">

            {/* Top Section: Command & Basic Stats */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 shrink-0">
                <div className="lg:col-span-3">
                    <CommandInput />
                </div>

                {/* Quick Stats Line */}
                <div className="hidden lg:flex items-center gap-4 bg-surface-900 border border-white/5 rounded-xl px-4 text-sm font-medium">
                    <div className="flex items-center gap-2 text-brand-400">
                        <Target size={16} />
                        <span>Found: {grants.length}</span>
                    </div>
                    <div className="w-px h-6 bg-white/10"></div>
                    <div className="flex items-center gap-2 text-cyan-400 text-opacity-80">
                        <Layers size={16} />
                        <span>Scraping</span>
                    </div>
                    <div className="w-px h-6 bg-white/10"></div>
                    <div className="flex items-center gap-2 text-violet-400 text-opacity-80">
                        <Cpu size={16} />
                        <span>AetherForge Active</span>
                    </div>
                </div>
            </div>

            {/* Main Grid: MindMap + BrowserGrid + EvoLog */}
            <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">

                {/* Left Col: MindMap & Handoff */}
                <div className="col-span-1 lg:col-span-3 flex flex-col gap-6">
                    <div className="flex-1 min-h-[300px]">
                        <GrantMindMap />
                    </div>
                    <div className="shrink-0">
                        <TeamHandoff />
                    </div>
                </div>

                {/* Center Col: Live Browser Extractor Grid */}
                <div className="col-span-1 lg:col-span-6 flex flex-col min-h-[400px]">
                    <LiveBrowserGrid />
                </div>

                {/* Right Col: EvoLog & Export */}
                <div className="col-span-1 lg:col-span-3 flex flex-col gap-6 min-h-[300px]">
                    <div className="flex-1 shrink-0 lg:flex-auto">
                        <EvoLogPanel />
                    </div>
                    {/* Show export only if hunt is done or has grants */}
                    {(grants.length > 0 && !isHunting) && (
                        <div className="shrink-0 animate-in fade-in slide-in-from-bottom-4">
                            <ExportPanel />
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
};

export default Dashboard;
