import { create } from 'zustand';

// Definición de tipos
export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: string;
  department: string;
  avatarUrl?: string;
}

export type RiskLevel = 'Low' | 'Medium' | 'High' | 'Critical';
export type Sentiment = 'Neutral' | 'Positive' | 'Negative';

interface AgentLog {
  id: string;
  message: string;
  timestamp: string;
  type: 'info' | 'success' | 'error' | 'thinking';
}

interface NeuroState {
  // Estado de Sesión
  currentUser: UserProfile | null;
  isAuthenticated: boolean;
  login: (user: UserProfile) => void;
  logout: () => void;

  // Estado del Dashboard (Live Intelligence)
  riskLevel: RiskLevel;
  sentiment: Sentiment;
  agentLogs: AgentLog[];
  
  // Acciones para actualizar el dashboard desde el chat
  setRiskLevel: (level: RiskLevel) => void;
  setSentiment: (sentiment: Sentiment) => void;
  addAgentLog: (message: string, type?: AgentLog['type']) => void;
  clearLogs: () => void;
}

export const useNeuroStore = create<NeuroState>((set) => ({
  currentUser: null,
  isAuthenticated: false,
  
  // Datos iniciales
  riskLevel: 'Low',
  sentiment: 'Neutral',
  agentLogs: [],

  login: (user) => set({ currentUser: user, isAuthenticated: true }),
  logout: () => set({ currentUser: null, isAuthenticated: false, agentLogs: [] }),

  setRiskLevel: (level) => set({ riskLevel: level }),
  setSentiment: (s) => set({ sentiment: s }),
  
  addAgentLog: (message, type = 'info') => set((state) => {
    // 1. Filtrar logs "colgados": Si el nuevo log es 'success' o 'error',
    // eliminamos cualquier log previo que sea de tipo 'thinking'.
    let cleanLogs = state.agentLogs;
    
    if (type === 'success' || type === 'error') {
      cleanLogs = state.agentLogs.filter(log => log.type !== 'thinking');
    }

    // 2. Agregar el nuevo log
    return {
      agentLogs: [
        ...cleanLogs,
        {
          id: Math.random().toString(36),
          message,
          timestamp: new Date().toLocaleTimeString(),
          type
        }
      ]
    };
  }),
  
  clearLogs: () => set({ agentLogs: [] })
}));