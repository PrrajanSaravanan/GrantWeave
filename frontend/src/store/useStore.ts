import { create } from 'zustand';
import { OrgProfile, Session, GrantResult, EvoLogEntry } from '../types';

interface AppState {
    // Org Profile
    orgProfile: OrgProfile | null;
    setOrgProfile: (profile: OrgProfile) => void;
    clearOrgProfile: () => void;

    // Active Session
    currentSession: Session | null;
    setCurrentSession: (session: Session) => void;

    // Real-time Data
    grants: GrantResult[];
    addGrant: (grant: GrantResult) => void;
    setGrants: (grants: GrantResult[]) => void;

    streamingUrls: { url: string; cellId?: string; portal?: string }[];
    addStreamingUrl: (data: { url: string; cellId?: string; portal?: string }) => void;

    evoLogs: EvoLogEntry[];
    addEvoLog: (log: EvoLogEntry) => void;

    // UI State
    isHunting: boolean;
    setIsHunting: (status: boolean) => void;
    huntPhase: string;
    setHuntPhase: (phase: string) => void;

    // Actions
    resetSessionData: () => void;
}

export const useStore = create<AppState>((set) => ({
    orgProfile: null,
    setOrgProfile: (profile) => set({ orgProfile: profile }),
    clearOrgProfile: () => set({ orgProfile: null }),

    currentSession: null,
    setCurrentSession: (session) => set({ currentSession: session }),

    grants: [],
    addGrant: (grant) => set((state) => ({ grants: [grant, ...state.grants] })),
    setGrants: (grants) => set({ grants }),

    streamingUrls: [],
    addStreamingUrl: (data) => set((state) => {
        if (state.streamingUrls.some(u => u.url === data.url)) return state;
        return { streamingUrls: [...state.streamingUrls, data] };
    }),

    evoLogs: [],
    addEvoLog: (log) => set((state) => ({ evoLogs: [log, ...state.evoLogs] })),

    isHunting: false,
    setIsHunting: (status) => set({ isHunting: status }),

    huntPhase: 'Idle',
    setHuntPhase: (phase) => set({ huntPhase: phase }),

    resetSessionData: () => set({
        currentSession: null,
        grants: [],
        streamingUrls: [],
        evoLogs: [],
        isHunting: false,
        huntPhase: 'Idle'
    }),
}));
