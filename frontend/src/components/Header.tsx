import React from 'react';
import { Bell, Search, User } from 'lucide-react';
import { useStore } from '../store/useStore';

const Header = () => {
    const { orgProfile } = useStore();

    return (
        <header className="h-16 bg-surface-900 border-b border-white/5 flex items-center justify-between px-6 z-10">
            {/* Search / Breadcrumbs area */}
            <div className="flex-1 md:flex-none md:w-96 flex items-center gap-3 ml-12 md:ml-0">
                <div className="relative w-full hidden sm:block">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Search size={16} className="text-slate-500" />
                    </div>
                    <input
                        type="text"
                        className="input-field w-full pl-10 h-9 text-sm"
                        placeholder="Search grants or sessions..."
                    />
                </div>
            </div>

            {/* Right side tools */}
            <div className="flex items-center gap-4">
                <button className="relative p-2 text-slate-400 hover:text-slate-200 transition-colors">
                    <Bell size={20} />
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-brand-500 rounded-full animate-pulse-slow"></span>
                </button>

                <div className="h-8 w-px bg-white/10 mx-2"></div>

                <div className="flex items-center gap-3">
                    <div className="hidden md:flex flex-col items-end">
                        <span className="text-sm font-medium text-slate-200">
                            {orgProfile?.name || 'Organization'}
                        </span>
                        <span className="text-xs text-brand-400">
                            AetherForge Active
                        </span>
                    </div>
                    <div className="h-9 w-9 rounded-full bg-surface-700 border border-white/10 flex items-center justify-center text-slate-300">
                        <User size={18} />
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
