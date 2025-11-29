import React, { useEffect, useRef } from 'react';
import { useNeuroStore } from '../../store/useNeuroStore';
import { Cpu, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const LiveLogPanel: React.FC = () => {
  const logs = useNeuroStore((state) => state.agentLogs);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="h-full overflow-y-auto p-4 font-mono text-xs space-y-3 custom-scrollbar">
      {logs.length === 0 && (
        <div className="text-gray-600 text-center mt-10 italic">
          Esperando eventos del sistema...
        </div>
      )}

      <AnimatePresence>
        {logs.map((log) => (
          <motion.div
            key={log.id}
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex gap-3 items-start group"
          >
            <div className="mt-0.5">
              {log.type === 'thinking' && <Loader2 className="w-3 h-3 text-neuro-400 animate-spin" />}
              {log.type === 'success' && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
              {log.type === 'error' && <AlertCircle className="w-3 h-3 text-red-400" />}
              {log.type === 'info' && <Cpu className="w-3 h-3 text-gray-500" />}
            </div>
            
            <div className="flex-1">
              <div className="text-[10px] text-gray-600 mb-0.5">{log.timestamp}</div>
              <div className={`leading-relaxed ${
                log.type === 'error' ? 'text-red-300' : 
                log.type === 'success' ? 'text-emerald-300' : 
                log.type === 'thinking' ? 'text-neuro-300' : 'text-gray-400'
              }`}>
                {log.message}
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
      <div ref={bottomRef} />
    </div>
  );
};