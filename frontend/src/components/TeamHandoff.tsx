import React, { useEffect, useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { Share2, Copy, CheckCircle2, Users } from 'lucide-react';
import { useStore } from '../store/useStore';
import toast from 'react-hot-toast';

const TeamHandoff = () => {
    const { currentSession } = useStore();
    const [copied, setCopied] = useState(false);
    const [peerCount, setPeerCount] = useState(1); // Self

    useEffect(() => {
        if (!currentSession?.share_token) return;

        // Connect to WebSocket using current host (or proxy in dev)
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/team/${currentSession.id}`;

        // In dev, Vite proxies /ws to FastAPI 8000
        const ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.event === 'PEER_JOINED' || data.event === 'PEER_LEFT') {
                    setPeerCount(data.peers);
                    if (data.event === 'PEER_JOINED' && data.peers > 1) {
                        toast('A team member joined the session', { icon: '👋' });
                    }
                }
            } catch (err) {
                console.error('WebSocket msg error', err);
            }
        };

        return () => {
            ws.close();
        };
    }, [currentSession?.id, currentSession?.share_token]);

    if (!currentSession?.share_token) return null;

    const shareUrl = `${window.location.origin}/share/${currentSession.share_token}`;

    const handleCopy = () => {
        navigator.clipboard.writeText(shareUrl);
        setCopied(true);
        toast.success('Link copied to clipboard');
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="glass-panel p-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
                <div className="p-2 bg-brand-500/20 rounded-lg text-brand-400">
                    <Share2 size={24} />
                </div>
                <div>
                    <h3 className="font-semibold text-slate-200">Team Handoff</h3>
                    <p className="text-xs text-slate-400">Scan or share to view live progress</p>
                </div>
            </div>

            <div className="flex items-center gap-6">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                    <Users size={16} className={peerCount > 1 ? 'text-green-400' : ''} />
                    {peerCount} viewing
                </div>

                <button
                    onClick={handleCopy}
                    className="btn-secondary flex items-center gap-2 text-sm px-3 py-1.5"
                >
                    {copied ? <CheckCircle2 size={16} className="text-green-400" /> : <Copy size={16} />}
                    {copied ? 'Copied' : 'Copy Link'}
                </button>

                <div className="bg-white rounded-md p-1">
                    <QRCodeSVG value={shareUrl} size={48} />
                </div>
            </div>
        </div>
    );
};

export default TeamHandoff;
