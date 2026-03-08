import React, { useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import Applications from './pages/Applications';
import Wrapped from './pages/Wrapped';
import OnboardingWizard from './components/OnboardingWizard';
import { useStore } from './store/useStore';
import { apiClient } from './api/client';
import toast from 'react-hot-toast';

function App() {
    const { orgProfile, setOrgProfile } = useStore();
    const navigate = useNavigate();
    const location = useLocation();

    // On mount, auto-load demo org-001 if no profile exists, just for easier hackathon testing
    // In a real app, we'd require login/onboarding
    useEffect(() => {
        if (!orgProfile) {
            apiClient.getOrg('demo-org-001')
                .then(org => setOrgProfile(org))
                .catch(() => {
                    // If seed hasn't run or org doesn't exist, we'll show onboarding
                });
        }
    }, [orgProfile, setOrgProfile]);

    // If nowhere to route and no org, show onboarding overlay
    if (!orgProfile) {
        return (
            <div className="min-h-screen bg-surface-950 flex items-center justify-center p-4 bg-grid-pattern">
                <div className="max-w-4xl w-full">
                    <OnboardingWizard onComplete={(org) => {
                        setOrgProfile(org);
                        toast.success('Welcome to GrantWeave!');
                        navigate('/');
                    }} />
                </div>
            </div>
        );
    }

    return (
        <div className="flex h-screen bg-surface-950 overflow-hidden selection:bg-brand-500/30">
            <Sidebar />
            <div className="flex-1 flex flex-col min-w-0">
                <Header />
                <main className="flex-1 overflow-auto relative">
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/applications" element={<Applications />} />
                        <Route path="/wrapped" element={<Wrapped />} />
                    </Routes>
                </main>
            </div>
        </div>
    );
}

export default App;
