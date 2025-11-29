import React from 'react';
import { motion } from 'framer-motion';
import { LogOut, LayoutGrid } from 'lucide-react';
import { useNeuroStore } from '../store/useNeuroStore';

interface DashboardProps {
  leftPanel: React.ReactNode;
  centerPanel: React.ReactNode;
  rightPanel: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardProps> = ({ leftPanel, centerPanel, rightPanel }) => {
  const logout = useNeuroStore((state) => state.logout);

  return (
    <div className="fixed inset-0 bg-slate-950 text-gray-100 flex">
      {/* Fondo Ambiental */}
      <div className="absolute inset-0 z-0 opacity-40">
        <div className="absolute top-[-20%] left-[-10%] w-[900px] h-[900px] bg-blue-900/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[900px] h-[900px] bg-purple-900/20 rounded-full blur-[120px]" />
      </div>

      {/* CONTENEDOR PRINCIPAL */}
      <div className="flex-1 flex relative z-10 m-2 gap-2">
        
        {/* COLUMNA 1: Perfil */}
        <motion.div 
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          className="w-[280px] hidden lg:flex flex-col"
        >
          <div className="flex-1 flex flex-col bg-slate-900/80 backdrop-blur-2xl border border-white/10 rounded-3xl">
            <div className="flex-1">
              {leftPanel}
            </div>
            <div className="p-3 border-t border-white/5 bg-black/20">
              <button 
                onClick={logout}
                className="flex items-center gap-3 text-xs font-medium text-gray-400 hover:text-white hover:bg-white/10 transition-all w-full px-3 py-2 rounded-xl"
              >
                <LogOut className="w-4 h-4" />
                Desconectar Sesión
              </button>
            </div>
          </div>
        </motion.div>

        {/* COLUMNA 2: Chat Central */}
        <motion.div 
          initial={{ y: 10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="flex-1 flex flex-col"
        >
          <div className="flex-1 bg-slate-900/90 backdrop-blur-3xl border border-white/10 rounded-3xl">
            {centerPanel}
          </div>
        </motion.div>

        {/* COLUMNA 3: Live Intelligence */}
        <motion.div 
          initial={{ x: 20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="w-[320px] hidden xl:flex flex-col"
        >
          <div className="flex-1 flex flex-col bg-slate-900/80 backdrop-blur-xl border border-white/10 rounded-3xl">
            <div className="p-3 border-b border-white/10 bg-white/5 flex items-center gap-2">
              <LayoutGrid className="w-4 h-4 text-neuro-400" />
              <span className="text-xs font-bold tracking-widest text-gray-300 uppercase">Live Intelligence</span>
            </div>
            <div className="flex-1">
              {rightPanel}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};