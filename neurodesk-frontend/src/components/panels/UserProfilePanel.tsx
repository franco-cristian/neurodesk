import React, { useState } from 'react';
import { useNeuroStore } from '../../store/useNeuroStore';
import { Activity, ShieldCheck, AlertTriangle } from 'lucide-react';

export const UserProfilePanel: React.FC = () => {
  const user = useNeuroStore((state) => state.currentUser);
  const riskLevel = useNeuroStore((state) => state.riskLevel);
  const [imgError, setImgError] = useState(false);

  const riskConfig = {
    Low: { color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', label: 'NORMAL', icon: ShieldCheck },
    Medium: { color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', label: 'ELEVADO', icon: Activity },
    High: { color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500/30', label: 'CRÍTICO', icon: AlertTriangle },
    Critical: { color: 'text-red-600', bg: 'bg-red-600/20', border: 'border-red-600/50', label: 'BURNOUT', icon: AlertTriangle }
  };

  const currentRisk = riskConfig[riskLevel] || riskConfig.Low;
  const RiskIcon = currentRisk.icon;

  if (!user) return null;

  const getInitials = (name: string) => {
    return name.split(' ').map(word => word[0]).join('').toUpperCase().substring(0, 2);
  };

  const showFallback = !user.avatarUrl || imgError;

  return (
    <div className="flex flex-col h-full p-3">
      {/* Header Perfil - Ultra compacto */}
      <div className="flex flex-col items-center mb-4">
        <div className="relative w-16 h-16 mb-2">
          <div className="absolute inset-0 rounded-full p-[1px] bg-gradient-to-tr from-neuro-500 to-purple-500">
            <div className="w-full h-full rounded-full bg-gray-800 flex items-center justify-center overflow-hidden">
              {user.avatarUrl && !imgError ? (
                <img 
                  src={user.avatarUrl} 
                  alt={user.name}
                  className="w-full h-full object-cover"
                  onError={() => setImgError(true)}
                />
              ) : null}
              
              {showFallback && (
                <div className="absolute inset-0 flex items-center justify-center rounded-full bg-gray-800">
                  <span className="text-lg font-bold text-white/80">
                    {getInitials(user.name)}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        <h2 className="text-base font-bold text-white text-center">{user.name}</h2>
        <p className="text-xs text-neuro-400 text-center mt-1">{user.role}</p>
        <div className="mt-2 px-2 py-1 bg-white/10 rounded-full text-[10px] text-gray-300">
          {user.department}
        </div>
      </div>

      <div className="h-px w-full bg-white/10 mb-4" />

      {/* Monitor de Bienestar - Ultra compacto */}
      <div className="flex-1">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-[9px] uppercase tracking-widest text-gray-400 font-bold">Monitor</h3>
          <div className="flex items-center gap-1">
            <span className="text-[9px] text-emerald-500 font-bold">LIVE</span>
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          </div>
        </div>

        <div className={`p-3 rounded-xl border ${currentRisk.border} ${currentRisk.bg}`}>
          <div className="flex justify-between items-center mb-2">
            <span className={`text-xs font-bold ${currentRisk.color}`}>ESTRÉS</span>
            <RiskIcon className={`w-4 h-4 ${currentRisk.color}`} />
          </div>
          
          <div className={`text-xl font-black ${currentRisk.color} mb-2 text-center`}>
            {currentRisk.label}
          </div>
          
          <div className="w-full bg-black/40 h-1.5 rounded-full overflow-hidden">
            <div 
              className={`h-full ${currentRisk.bg.replace('/10','/50')}`} 
              style={{ 
                width: riskLevel === 'Low' ? '25%' : 
                       riskLevel === 'Medium' ? '50%' : 
                       riskLevel === 'High' ? '75%' : '90%' 
              }} 
            />
          </div>
        </div>
      </div>
    </div>
  );
};