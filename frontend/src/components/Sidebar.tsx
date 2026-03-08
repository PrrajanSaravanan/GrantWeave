import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FolderKanban, BarChart3, Settings, Rocket, ExternalLink, Menu, X } from 'lucide-react';

const Sidebar = () => {
    const [isOpen, setIsOpen] = useState(false);

    const navItems = [
        { name: 'Dashboard', path: '/', icon: <LayoutDashboard size={20} /> },
        { name: 'Applications', path: '/applications', icon: <FolderKanban size={20} /> },
        { name: 'Wrapped', path: '/wrapped', icon: <BarChart3 size={20} /> },
    ];

    return (
        <>
            {/* Mobile toggle */}
            <button
                className="md:hidden fixed top-4 left-4 z-50 p-2 bg-surface-800 rounded-md text-slate-200"
                onClick={() => setIsOpen(!isOpen)}
            >
                {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>

            {/* Sidebar */}
            <aside className={`
        fixed md:static inset-y-0 left-0 z-40 w-64 bg-surface-900 border-r border-white/5 
        flex flex-col transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
                {/* Logo area */}
                <div className="h-16 flex items-center px-6 border-b border-white/5">
                    <div className="flex items-center gap-2 text-brand-400">
                        <Rocket size={24} />
                        <span className="text-xl font-bold tracking-tight text-white">GrantWeave</span>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-4 py-8 space-y-2">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.name}
                            to={item.path}
                            onClick={() => setIsOpen(false)}
                            className={({ isActive }) => `
                flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors
                ${isActive
                                    ? 'bg-brand-500/10 text-brand-400'
                                    : 'text-slate-400 hover:text-slate-200 hover:bg-surface-800'}
              `}
                        >
                            {item.icon}
                            {item.name}
                        </NavLink>
                    ))}
                </nav>

                {/* Bottom area */}
                <div className="p-4 border-t border-white/5">
                    <a
                        href="https://agent.tinyfish.ai/docs"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-slate-400 hover:text-slate-200 hover:bg-surface-800 rounded-lg transition-colors"
                    >
                        <Settings size={20} />
                        TinyFish API
                        <ExternalLink size={14} className="ml-auto opacity-50" />
                    </a>
                </div>
            </aside>

            {/* Mobile backdrop */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-30 md:hidden"
                    onClick={() => setIsOpen(false)}
                />
            )}
        </>
    );
};

export default Sidebar;
