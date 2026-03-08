export interface OrgProfile {
    id: string;
    name: string;
    mission?: string;
    ein?: string;
    focus_areas: string[];
    location?: string;
    budget?: number;
    founded?: number;
    website?: string;
}

export interface Session {
    id: string;
    org_id?: string;
    command: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    started_at?: string;
    completed_at?: string;
    grants_found: number;
    share_token?: string;
}

export interface GrantResult {
    id: string;
    session_id: string;
    title: string;
    funder?: string;
    amount?: string;
    deadline?: string;
    url?: string;
    category?: string;
    match_score: number;
    description?: string;
    requirements?: string;
    status: 'found' | 'saved' | 'dismissed';
}

export interface EvoLogEntry {
    id: string;
    session_id: string;
    attempt: number;
    original_goal: string;
    mutated_goal: string;
    strategy: string;
    result: 'pending' | 'success' | 'failure';
    score: number;
    created_at?: string;
}

export interface WrappedReport {
    id: string;
    org_id: string;
    week_of: string;
    sessions_run: number;
    grants_found: number;
    best_match?: string;
    mutations_run: number;
    data: {
        recent_sessions: string[];
        category_breakdown: Record<string, number>;
        top_grants: Array<{ title: string; funder?: string; amount?: string }>;
        mutations_by_strategy: Record<string, number>;
        fun_facts: string[];
        portals_scanned: number;
        timeline: Array<{ date: string; grants: number }>;
    };
}

export interface SSEEvent {
    event: 'STARTED' | 'SCANNING' | 'MATCH_FOUND' | 'STREAMING_URL' |
    'EVO_MUTATION' | 'EVO_RESULT' | 'AKASHA_HIT' | 'RESUMED' |
    'COMPLETE' | 'ERROR';
    session_id: string;
    data?: any;
}
