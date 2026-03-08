import React, { useState } from 'react';
import { Upload, FileText, CheckCircle2, Building, Target, Loader2, ArrowRight } from 'lucide-react';
import { OrgProfile } from '../types';
import { apiClient } from '../api/client';
import toast from 'react-hot-toast';

interface Props {
    onComplete: (org: OrgProfile) => void;
}

const steps = ['Welcome', 'Upload', 'Verify', 'Complete'];

const OnboardingWizard: React.FC<Props> = ({ onComplete }) => {
    const [currentStep, setCurrentStep] = useState(0);
    const [isUploading, setIsUploading] = useState(false);
    const [profile, setProfile] = useState<Partial<OrgProfile>>({
        name: '', focus_areas: [],
    });

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (file.type !== 'application/pdf') {
            toast.error('Please upload a PDF file.');
            return;
        }

        setIsUploading(true);
        try {
            const res = await apiClient.onboardPdf(file);
            setProfile(res.org);
            toast.success('Profile extracted successfully!');
            setCurrentStep(2); // Auto-advance to verify step
        } catch (err: any) {
            toast.error('Failed to parse PDF: ' + err.message);
        } finally {
            setIsUploading(false);
        }
    };

    const submitManual = async () => {
        if (!profile.name || profile.focus_areas?.length === 0) {
            toast.error('Name and at least one Focus Area are required.');
            return;
        }

        setIsUploading(true);
        try {
            // Clean up string focus areas into array if needed
            const dataToSubmit = {
                ...profile,
                focus_areas: Array.isArray(profile.focus_areas)
                    ? profile.focus_areas
                    : (profile.focus_areas as string).split(',').map(s => s.trim()).filter(Boolean)
            };

            const res = await apiClient.onboardManual(dataToSubmit);
            setProfile(res.org);
            setCurrentStep(3); // Complete
        } catch (err: any) {
            toast.error('Failed to save profile: ' + err.message);
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="glass-panel p-8 max-w-2xl mx-auto w-full relative overflow-hidden">
            {/* Background glow */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-brand-500/20 rounded-full blur-[100px] pointer-events-none"></div>

            {/* Progress Bar */}
            <div className="flex gap-2 mb-10">
                {steps.map((label, i) => (
                    <div key={label} className="flex-1">
                        <div className={`h-1.5 rounded-full mb-2 transition-colors ${i <= currentStep ? 'bg-brand-500' : 'bg-surface-800'}`}></div>
                        <span className={`text-xs font-medium ${i <= currentStep ? 'text-brand-400' : 'text-slate-500'}`}>{label}</span>
                    </div>
                ))}
            </div>

            {/* STEP 0: Welcome */}
            {currentStep === 0 && (
                <div className="text-center py-6 animate-in fade-in slide-in-from-bottom-4">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-brand-500/10 mb-6 border border-brand-500/20">
                        <Rocket size={40} className="text-brand-400" />
                    </div>
                    <h1 className="text-3xl mb-4 font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400">
                        Welcome to GrantWeave
                    </h1>
                    <p className="text-slate-400 text-lg mb-8 max-w-md mx-auto">
                        AetherForge kernel needs to understand your organization to hunt effectively. Let's build your profile.
                    </p>
                    <button onClick={() => setCurrentStep(1)} className="btn-primary w-full max-w-sm flex items-center justify-center gap-2 mx-auto">
                        Get Started <ArrowRight size={18} />
                    </button>
                </div>
            )}

            {/* STEP 1: Upload or Manual */}
            {currentStep === 1 && (
                <div className="animate-in fade-in slide-in-from-right-8 duration-300">
                    <h2 className="text-2xl mb-2 font-bold">Profile Construction</h2>
                    <p className="text-slate-400 mb-8">Upload an annual report or 990 PDF, and AetherForge will extract your details automatically.</p>

                    <div className="grid md:grid-cols-2 gap-6">
                        {/* Upload Box */}
                        <div className="border-2 border-dashed border-white/10 hover:border-brand-500/50 hover:bg-brand-500/5 rounded-xl p-8 flex flex-col items-center justify-center text-center transition-all cursor-pointer relative group">
                            <input
                                type="file"
                                accept="application/pdf"
                                onChange={handleFileUpload}
                                disabled={isUploading}
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                            />
                            {isUploading ? (
                                <Loader2 className="animate-spin text-brand-500 mb-4" size={40} />
                            ) : (
                                <div className="p-4 bg-surface-800 rounded-full mb-4 group-hover:-translate-y-1 transition-transform">
                                    <Upload className="text-slate-300" size={28} />
                                </div>
                            )}
                            <h3 className="font-semibold text-lg text-slate-200 mb-1">
                                {isUploading ? 'Extracting Data...' : 'Upload PDF'}
                            </h3>
                            <p className="text-sm text-slate-500">Auto-fill via AI</p>
                        </div>

                        {/* Manual Box */}
                        <div
                            onClick={() => setCurrentStep(2)}
                            className="glass-panel p-8 flex flex-col items-center justify-center text-center hover:bg-surface-800/80 cursor-pointer transition-all group"
                        >
                            <div className="p-4 bg-surface-800 rounded-full mb-4 group-hover:-translate-y-1 transition-transform border border-white/5">
                                <FileText className="text-slate-300" size={28} />
                            </div>
                            <h3 className="font-semibold text-lg text-slate-200 mb-1">Enter Manually</h3>
                            <p className="text-sm text-slate-500">Fill out a simple form</p>
                        </div>
                    </div>
                </div>
            )}

            {/* STEP 2: Verify Form */}
            {currentStep === 2 && (
                <div className="animate-in fade-in slide-in-from-right-8 duration-300">
                    <h2 className="text-2xl mb-2 font-bold">Verify Profile</h2>
                    <p className="text-slate-400 mb-6">Review your organization details before initiating hunts.</p>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Organization Name *</label>
                            <div className="relative">
                                <Building className="absolute left-3 top-2.5 text-slate-500" size={18} />
                                <input
                                    type="text"
                                    value={profile.name}
                                    onChange={e => setProfile({ ...profile, name: e.target.value })}
                                    className="input-field w-full pl-10"
                                    placeholder="e.g. Bright Futures Foundation"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Primary Focus Areas *</label>
                            <div className="relative">
                                <Target className="absolute left-3 top-2.5 text-slate-500" size={18} />
                                <input
                                    type="text"
                                    value={Array.isArray(profile.focus_areas) ? profile.focus_areas.join(', ') : profile.focus_areas}
                                    onChange={e => setProfile({ ...profile, focus_areas: e.target.value })}
                                    className="input-field w-full pl-10"
                                    placeholder="e.g. education, youth, STEM (comma separated)"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Location</label>
                                <input
                                    type="text"
                                    value={profile.location || ''}
                                    onChange={e => setProfile({ ...profile, location: e.target.value })}
                                    className="input-field w-full"
                                    placeholder="City, State"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Annual Budget ($)</label>
                                <input
                                    type="number"
                                    value={profile.budget || ''}
                                    onChange={e => setProfile({ ...profile, budget: Number(e.target.value) })}
                                    className="input-field w-full"
                                    placeholder="e.g. 500000"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Mission Statement</label>
                            <textarea
                                value={profile.mission || ''}
                                onChange={e => setProfile({ ...profile, mission: e.target.value })}
                                className="input-field w-full h-24 resize-none"
                                placeholder="Briefly describe what your organization does..."
                            />
                        </div>
                    </div>

                    <div className="flex justify-between mt-8">
                        <button onClick={() => setCurrentStep(1)} className="btn-secondary">Back</button>
                        <button onClick={submitManual} disabled={isUploading} className="btn-primary flex items-center gap-2">
                            {isUploading ? <Loader2 size={18} className="animate-spin" /> : 'Save Profile'}
                        </button>
                    </div>
                </div>
            )}

            {/* STEP 3: Complete */}
            {currentStep === 3 && (
                <div className="text-center py-8 animate-in zoom-in-95 duration-500">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-500/10 mb-6 border border-green-500/20">
                        <CheckCircle2 size={40} className="text-green-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-100 mb-2">Systems Ready</h2>
                    <p className="text-slate-400 mb-8 max-w-sm mx-auto">
                        AetherForge kernel initialized with <strong>{profile.name}</strong> profile. Web agents are standing by.
                    </p>
                    <button
                        onClick={() => onComplete(profile as OrgProfile)}
                        className="btn-primary px-8 w-full max-w-sm"
                    >
                        Launch Dashboard
                    </button>
                </div>
            )}
        </div>
    );
};

export default OnboardingWizard;
