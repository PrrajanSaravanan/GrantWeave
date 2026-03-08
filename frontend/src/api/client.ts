import { OrgProfile, Session, GrantResult, EvoLogEntry, WrappedReport } from '../types';

const API_BASE = '/api';

export const apiClient = {
    // --- Onboarding ---
    async onboardManual(data: any): Promise<{ success: boolean; org: OrgProfile }> {
        const res = await fetch(`${API_BASE}/onboard`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    async onboardPdf(file: File): Promise<{ success: boolean; org: OrgProfile; extracted_text_snippet: string }> {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch(`${API_BASE}/onboard/pdf`, {
            method: 'POST',
            body: formData,
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    async getOrg(orgId: string): Promise<OrgProfile> {
        const res = await fetch(`${API_BASE}/orgs/${orgId}`);
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    // --- Sessions & Grants ---
    async getSessions(limit = 20): Promise<{ sessions: Session[] }> {
        const res = await fetch(`${API_BASE}/sessions?limit=${limit}`);
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    async getSession(sessionId: string): Promise<Session> {
        const res = await fetch(`${API_BASE}/sessions/${sessionId}`);
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    async getGrants(sessionId?: string): Promise<{ grants: GrantResult[]; total: number }> {
        const url = sessionId ? `${API_BASE}/grants?session_id=${sessionId}` : `${API_BASE}/grants`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    // --- EvoLog ---
    async getEvoLog(sessionId?: string): Promise<{ entries: EvoLogEntry[]; total: number }> {
        const url = sessionId ? `${API_BASE}/evo-log?session_id=${sessionId}` : `${API_BASE}/evo-log`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    // --- Team Handoff ---
    async resolveShareToken(token: string): Promise<Session> {
        const res = await fetch(`${API_BASE}/share/${token}`);
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    // --- Wrapped ---
    async getWrappedReport(orgId: string): Promise<WrappedReport> {
        const res = await fetch(`${API_BASE}/wrapped/${orgId}`);
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    // --- Export ---
    async exportGrants(sessionId: string, format: 'pdf' | 'csv'): Promise<Blob> {
        const res = await fetch(`${API_BASE}/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, format }),
        });
        if (!res.ok) throw new Error(await res.text());
        return res.blob();
    },
};
