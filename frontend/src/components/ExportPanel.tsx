import React, { useState } from 'react';
import { Download, FileText, FileSpreadsheet, Loader2 } from 'lucide-react';
import { useStore } from '../store/useStore';
import { apiClient } from '../api/client';
import toast from 'react-hot-toast';

const ExportPanel = () => {
    const { currentSession, grants } = useStore();
    const [exportingCsv, setExportingCsv] = useState(false);
    const [exportingPdf, setExportingPdf] = useState(false);

    // Auto-fill preview (first grant found)
    const previewGrant = grants[0];

    const handleExport = async (format: 'csv' | 'pdf') => {
        if (!currentSession?.id) return;

        const setLoader = format === 'csv' ? setExportingCsv : setExportingPdf;
        setLoader(true);

        try {
            const blob = await apiClient.exportGrants(currentSession.id, format);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `grantweave_export_${currentSession.id.substring(0, 8)}.${format}`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            toast.success(`${format.toUpperCase()} export complete`);
        } catch (err: any) {
            toast.error(`Export failed: ${err.message}`);
        } finally {
            setLoader(false);
        }
    };

    if (!currentSession || grants.length === 0) return null;

    return (
        <div className="glass-panel p-6">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                        <Download size={20} className="text-brand-400" />
                        Export Application Package
                    </h3>
                    <p className="text-sm text-slate-400 mt-1">
                        Pre-filled with AetherForge organization profile data
                    </p>
                </div>

                <div className="flex gap-3">
                    <button
                        onClick={() => handleExport('csv')}
                        disabled={exportingCsv || exportingPdf}
                        className="btn-secondary flex items-center gap-2"
                    >
                        {exportingCsv ? <Loader2 size={18} className="animate-spin" /> : <FileSpreadsheet size={18} />}
                        Export CSV tracking
                    </button>
                    <button
                        onClick={() => handleExport('pdf')}
                        disabled={exportingCsv || exportingPdf}
                        className="btn-primary flex items-center gap-2"
                    >
                        {exportingPdf ? <Loader2 size={18} className="animate-spin" /> : <FileText size={18} />}
                        Download Core PDFs
                    </button>
                </div>
            </div>

            {/* Auto-fill Preview */}
            <div className="bg-surface-950/50 rounded-lg p-4 border border-white/5 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-2 opacity-10 pointer-events-none">
                    <FileText size={64} />
                </div>

                <h4 className="text-sm font-semibold text-slate-300 mb-2 uppercase tracking-wider">
                    Auto-fill Preview
                </h4>

                {previewGrant ? (
                    <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
                        <div className="flex justify-between border-b border-white/5 py-1">
                            <span className="text-slate-500">Target Grant:</span>
                            <span className="text-slate-200 font-medium truncate max-w-[200px]">{previewGrant.title}</span>
                        </div>
                        <div className="flex justify-between border-b border-white/5 py-1">
                            <span className="text-slate-500">Deadline:</span>
                            <span className="text-slate-200">{previewGrant.deadline || 'Rolling'}</span>
                        </div>
                        <div className="flex justify-between border-b border-white/5 py-1">
                            <span className="text-slate-500">Applicant:</span>
                            <span className="text-slate-200 text-brand-300">GrantWeave Auto-inject</span>
                        </div>
                        <div className="flex justify-between border-b border-white/5 py-1">
                            <span className="text-slate-500">Est. Request:</span>
                            <span className="text-slate-200">{previewGrant.amount || 'TBD'}</span>
                        </div>
                    </div>
                ) : (
                    <p className="text-sm text-slate-500 italic">No grants available for preview.</p>
                )}
            </div>
        </div>
    );
};

export default ExportPanel;
