import React, { useState } from 'react';
import axios from 'axios';
import { UploadCloud, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { useNeuroStore } from '../../store/useNeuroStore';

interface UploadWidgetProps {
  uploadUrl: string;
  expiresAt: string;
  onUploadComplete: () => void;
}

export const UploadWidget: React.FC<UploadWidgetProps> = ({ uploadUrl, expiresAt, onUploadComplete }) => {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const addLog = useNeuroStore(s => s.addAgentLog);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const uploadFile = async () => {
    if (!file) return;

    setStatus('uploading');
    addLog(`Iniciando carga de archivo: ${file.name} a Azure Blob Storage...`, 'info');

    try {
      // SUBIDA DIRECTA A AZURE (PUT)
      await axios.put(uploadUrl, file, {
        headers: {
          'x-ms-blob-type': 'BlockBlob',
          'Content-Type': file.type,
        },
      });

      setStatus('success');
      addLog(`✅ Archivo ${file.name} subido exitosamente.`, 'success');
      onUploadComplete();
    } catch (error) {
      console.error(error);
      setStatus('error');
      addLog(`❌ Error al subir archivo.`, 'error');
    }
  };

  if (status === 'success') {
    return (
      <div className="bg-emerald-900/20 border border-emerald-500/30 rounded-xl p-4 flex items-center gap-3 my-2">
        <CheckCircle className="w-6 h-6 text-emerald-400" />
        <div>
          <p className="text-sm font-medium text-emerald-200">Archivo subido correctamente</p>
          <p className="text-xs text-emerald-400/60">{file?.name}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-neuro-800/50 border border-neuro-500/30 rounded-xl p-4 my-2 max-w-sm animate-pulse-slow">
      <div className="flex items-center gap-2 mb-3">
        <UploadCloud className="w-5 h-5 text-neuro-400" />
        <span className="text-sm font-semibold text-gray-200">Solicitud de Evidencia</span>
      </div>
      
      <p className="text-xs text-gray-400 mb-3">
        El sistema requiere logs o capturas. El enlace seguro expira: <br/>
        <span className="font-mono text-neuro-cyan">{new Date(expiresAt).toLocaleTimeString()}</span>
      </p>

      <div className="flex gap-2">
        <input 
          type="file" 
          onChange={handleFileChange} 
          className="block w-full text-xs text-gray-400 file:mr-2 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-neuro-700 file:text-white hover:file:bg-neuro-600"
        />
        <button 
          onClick={uploadFile}
          disabled={!file || status === 'uploading'}
          className="bg-neuro-500 hover:bg-neuro-400 disabled:opacity-50 text-white rounded-lg p-2 transition-colors"
        >
          {status === 'uploading' ? <Loader2 className="w-4 h-4 animate-spin" /> : <UploadCloud className="w-4 h-4" />}
        </button>
      </div>
      
      {status === 'error' && (
        <div className="mt-2 flex items-center gap-1 text-red-400 text-xs">
          <AlertCircle className="w-3 h-3" /> Error en la subida. Intenta de nuevo.
        </div>
      )}
    </div>
  );
};