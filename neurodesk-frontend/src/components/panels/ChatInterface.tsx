import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import axios, { AxiosError } from 'axios';
import { Send, Mic, StopCircle, User, Bot, Paperclip, Volume2, VolumeX, Square } from 'lucide-react';
import { useNeuroStore } from '../../store/useNeuroStore';
import { UploadWidget } from '../widgets/UploadWidget';
import { AudioRecorder } from '../../utils/audioRecorder';

// 1. DEFINIR LA URL BASE DINÁMICA
// Si existe la variable de entorno, úsala. Si no, usa localhost como fallback.
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    uiComponent?: {
        type: string;
        payload: Record<string, unknown>;
    };
    audioBase64?: string;
    isStreaming?: boolean;
}

interface VoiceResponse {
    response: string;
    user_text: string;
    ai_audio_base64?: string;
    risk_level?: string;
    sentiment?: string;
    actions_taken?: string[];
    ui_component?: {
        type: string;
        payload: Record<string, unknown>;
    };
    error?: string;
}

export const ChatInterface: React.FC = () => {
    const { currentUser, setRiskLevel, addAgentLog } = useNeuroStore();
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState<Message[]>([
        { id: '0', role: 'assistant', content: `Hola ${currentUser?.name.split(' ')[0]}. Soy NeuroDesk. ¿En qué puedo ayudarte hoy?` }
    ]);
    const [isRecording, setIsRecording] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [isAudioMuted, setIsAudioMuted] = useState(false);
    const [currentlyPlayingAudio, setCurrentlyPlayingAudio] = useState<HTMLAudioElement | null>(null);
    const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);

    const recorderRef = useRef<AudioRecorder | null>(null);
    const bottomRef = useRef<HTMLDivElement>(null);
    const streamingIntervalRef = useRef<number | null>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        return () => {
            if (currentlyPlayingAudio) {
                currentlyPlayingAudio.pause();
                currentlyPlayingAudio.currentTime = 0;
            }
            if (streamingIntervalRef.current) {
                clearInterval(streamingIntervalRef.current);
            }
        };
    }, [currentlyPlayingAudio]);

    useEffect(() => {
        let timeoutId: number;
        
        if (isProcessing) {
            timeoutId = window.setTimeout(() => {
                if (isProcessing) {
                    console.warn("🕐 Timeout de procesamiento forzado");
                    setIsProcessing(false);
                    addAgentLog('Timeout: Procesamiento tomó demasiado tiempo', 'error');
                }
            }, 30000);
        }
        
        return () => {
            if (timeoutId) clearTimeout(timeoutId);
        };
    }, [isProcessing, addAgentLog]);

    const stopCurrentAudio = () => {
        if (currentlyPlayingAudio) {
            currentlyPlayingAudio.pause();
            currentlyPlayingAudio.currentTime = 0;
            setCurrentlyPlayingAudio(null);
        }
    };

    const toggleMute = () => {
        setIsAudioMuted(!isAudioMuted);
        stopCurrentAudio();
    };

    const playAudio = async (audioBase64: string) => {
        if (isAudioMuted) return;
        
        stopCurrentAudio();
        
        try {
            const audio = new Audio(`data:audio/wav;base64,${audioBase64}`);
            audio.volume = 0.7;
            
            audio.onended = () => {
                setCurrentlyPlayingAudio(null);
            };
            
            setCurrentlyPlayingAudio(audio);
            await audio.play();
        } catch (error) {
            console.warn("Error reproduciendo audio:", error);
            setCurrentlyPlayingAudio(null);
        }
    };

    // Función optimizada para efecto de escritura más rápido
    const streamMessage = (messageId: string, fullContent: string, audioBase64?: string) => {
        setStreamingMessageId(messageId);
        
        let currentIndex = 0;
        const speed = 2; // Velocidad aumentada significativamente (2ms por carácter)
        
        streamingIntervalRef.current = window.setInterval(() => {
            if (currentIndex <= fullContent.length) {
                setMessages(prev => prev.map(msg => 
                    msg.id === messageId 
                        ? { ...msg, content: fullContent.substring(0, currentIndex) }
                        : msg
                ));
                currentIndex++;
                
                // Scroll automático durante el streaming
                const messageElement = document.getElementById(`message-${messageId}`);
                if (messageElement) {
                    messageElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            } else {
                if (streamingIntervalRef.current) {
                    clearInterval(streamingIntervalRef.current);
                    streamingIntervalRef.current = null;
                }
                setStreamingMessageId(null);
                setMessages(prev => prev.map(msg => 
                    msg.id === messageId 
                        ? { ...msg, isStreaming: false }
                        : msg
                ));
                
                // Reproducir audio inmediatamente después de terminar el texto
                if (audioBase64 && !isAudioMuted) {
                    setTimeout(() => {
                        playAudio(audioBase64);
                    }, 100);
                }
            }
        }, speed);
    };

    const isValidRiskLevel = (level: string): level is 'Low' | 'Medium' | 'High' | 'Critical' => {
        return ['Low', 'Medium', 'High', 'Critical'].includes(level);
    };

    const sendMessage = async (text: string) => {
        if (!text.trim() || isProcessing) return;

        const userMsg: Message = { 
            id: `user-${Date.now()}`, 
            role: 'user', 
            content: text 
        };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsProcessing(true);

        addAgentLog(`Analizando solicitud: "${text.substring(0, 20)}..."`, 'info');
        addAgentLog('Consultando políticas y métricas de usuario...', 'thinking');

        try {
            // 2. USAR LA VARIABLE AQUÍ
            const response = await axios.post(`${API_URL}/chat`, {
                user_id: currentUser?.id || 'unknown',
                message: text,
                conversation_id: `session-${currentUser?.id}`
            });

            const data = response.data;

            if (data.risk_level && isValidRiskLevel(data.risk_level)) {
                setRiskLevel(data.risk_level);
            }

            if (data.actions_taken) {
                data.actions_taken.forEach((action: string) => {
                    addAgentLog(`Acción ejecutada: ${action}`, 'success');
                });
            }

            const aiMsg: Message = {
                id: `assistant-${Date.now()}`,
                role: 'assistant',
                content: '',
                uiComponent: data.ui_component,
                isStreaming: true
            };
            
            setMessages(prev => [...prev, aiMsg]);
            
            // Iniciar efecto de escritura inmediatamente
            streamMessage(aiMsg.id, data.response);

        } catch (error) {
            console.error("API Error:", error);
            addAgentLog('Error de conexión con el núcleo.', 'error');
            setMessages(prev => [...prev, { 
                id: `error-${Date.now()}`, 
                role: 'assistant', 
                content: '⚠️ Error de conexión con el servidor.' 
            }]);
        } finally {
            setIsProcessing(false);
        }
    };

    const startRecording = async () => {
        if (isProcessing) return;
        
        try {
            const recorder = new AudioRecorder();
            await recorder.start();
            recorderRef.current = recorder;
            setIsRecording(true);
        } catch (err) {
            console.error("Error microfono:", err);
            addAgentLog('No se pudo acceder al micrófono. Verifica permisos.', 'error');
        }
    };

    const stopRecording = async () => {
        if (recorderRef.current && isRecording) {
            setIsRecording(false);
            
            try {
                const wavBlob = await recorderRef.current.stop();
                await sendAudio(wavBlob);
            } catch (e) {
                console.error("Error deteniendo grabación:", e);
            }
            
            recorderRef.current = null;
        }
    };

    const sendAudio = async (audioBlob: Blob) => {
        if (isProcessing) return;
        
        setIsProcessing(true);
        addAgentLog('Procesando audio...', 'thinking');

        const formData = new FormData();
        formData.append('file', audioBlob, 'voice_input.wav');
        formData.append('user_id', currentUser?.id || 'unknown');
        formData.append('conversation_id', `session-${currentUser?.id}`);

        try {
            // 3. Y TAMBIÉN AQUÍ
            const response = await axios.post<VoiceResponse>(`${API_URL}/chat/voice`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                timeout: 30000
            });

            const data = response.data;

            // Agregar mensaje de usuario primero
            const userMsg: Message = {
                id: `user-voice-${Date.now()}`,
                role: 'user', 
                content: `🎤 ${data.user_text}`
            };
            
            setMessages(prev => [...prev, userMsg]);

            // Luego crear y agregar mensaje del asistente
            const aiMsg: Message = {
                id: `assistant-voice-${Date.now()}`,
                role: 'assistant',
                content: '',
                uiComponent: data.ui_component,
                audioBase64: data.ai_audio_base64,
                isStreaming: true
            };
            
            setMessages(prev => [...prev, aiMsg]);
            
            // Iniciar efecto de escritura inmediatamente con el audio
            streamMessage(aiMsg.id, data.response, data.ai_audio_base64);

            if (data.risk_level && isValidRiskLevel(data.risk_level)) {
                setRiskLevel(data.risk_level);
            }

            addAgentLog('Audio procesado correctamente', 'success');

        } catch (error: unknown) {
            console.error("Voice Error:", error);
            
            let errorMsg = 'Error desconocido';
            if (error instanceof AxiosError) {
                errorMsg = error.response?.data?.error || error.message || 'Error de conexión';
            } else if (error instanceof Error) {
                errorMsg = error.message;
            }
            
            addAgentLog(`Error procesando audio: ${errorMsg}`, 'error');
            
            setMessages(prev => [...prev, { 
                id: `error-voice-${Date.now()}`, 
                role: 'assistant', 
                content: '⚠️ Error al procesar el audio. Por favor intenta de nuevo.' 
            }]);
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="flex flex-col h-screen">
            {/* Barra de controles de audio */}
            <div className="shrink-0 p-2 bg-[#0a0a0a]/80 border-b border-white/5 flex justify-between items-center">
                <div className="text-xs text-gray-400">
                    NeuroDesk AI - Modo Voz {isAudioMuted ? '🔇' : '🔊'}
                    {streamingMessageId && ' | ✍️ Escribiendo...'}
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={toggleMute}
                        className={`p-2 rounded-lg transition-colors ${
                            isAudioMuted 
                                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30' 
                                : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                        }`}
                        title={isAudioMuted ? 'Activar audio' : 'Silenciar audio'}
                    >
                        {isAudioMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                    </button>
                    
                    <button
                        onClick={stopCurrentAudio}
                        disabled={!currentlyPlayingAudio}
                        className="p-2 rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        title="Detener audio actual"
                    >
                        <Square className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Contenedor principal con altura fija */}
            <div className="flex-1 flex flex-col min-h-0">
                
                {/* Área de mensajes CON SCROLL */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6 min-h-0">
                    {messages.map((msg) => (
                        <div 
                            key={msg.id} 
                            id={`message-${msg.id}`}
                            className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                        >
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-blue-600' : 'bg-neuro-500'}`}>
                                {msg.role === 'user' ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-white" />}
                            </div>

                            <div className={`max-w-[80%] rounded-2xl p-4 text-sm leading-relaxed shadow-lg ${msg.role === 'user'
                                    ? 'bg-blue-600/20 border border-blue-500/30 text-blue-100 rounded-tr-none'
                                    : 'bg-[#1a1f2e] border border-white/5 text-gray-200 rounded-tl-none'
                                }`}>
                                <div className="markdown-content">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {msg.content}
                                    </ReactMarkdown>
                                </div>

                                {/* Indicador de escritura */}
                                {msg.isStreaming && (
                                    <div className="flex gap-1 mt-2">
                                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                    </div>
                                )}

                                {msg.role === 'assistant' && msg.audioBase64 && !msg.isStreaming && (
                                    <div className="mt-3 flex gap-2 items-center">
                                        <button
                                            onClick={() => playAudio(msg.audioBase64!)}
                                            disabled={currentlyPlayingAudio !== null}
                                            className="text-xs bg-green-500/20 text-green-400 px-3 py-1 rounded-lg hover:bg-green-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
                                        >
                                            <Volume2 className="w-3 h-3" />
                                            Reproducir
                                        </button>
                                        <span className="text-xs text-gray-500">
                                            {isAudioMuted && '(audio silenciado)'}
                                        </span>
                                    </div>
                                )}

                                {msg.uiComponent && msg.uiComponent.type === 'upload_widget' && (
                                    <div className="mt-4">
                                        <UploadWidget
                                            uploadUrl={msg.uiComponent.payload.upload_url as string}
                                            expiresAt={msg.uiComponent.payload.expires_at as string}
                                            onUploadComplete={() => addAgentLog('Archivo recibido y analizado por seguridad.', 'success')}
                                        />
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}

                    {isProcessing && !streamingMessageId && (
                        <div className="flex gap-4">
                            <div className="w-8 h-8 rounded-lg bg-neuro-500 flex items-center justify-center animate-pulse">
                                <Bot className="w-5 h-5 text-white" />
                            </div>
                            <div className="bg-[#1a1f2e] rounded-2xl p-4 flex gap-1 items-center">
                                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                            </div>
                        </div>
                    )}
                    <div ref={bottomRef} />
                </div>

                {/* Input area - FIJA EN LA PARTE INFERIOR */}
                <div className="shrink-0 p-4 bg-[#0a0a0a]/50 border-t border-white/5 backdrop-blur-md">
                    <div className="flex items-end gap-3 max-w-4xl mx-auto">
                        <button 
                            className="p-3 rounded-xl bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            disabled={isProcessing || !!streamingMessageId}
                        >
                            <Paperclip className="w-5 h-5" />
                        </button>

                        <div className="flex-1 bg-[#1a1a1a] rounded-xl border border-white/10 focus-within:border-blue-500/50 transition-colors flex items-center p-2">
                            <textarea
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        sendMessage(input);
                                    }
                                }}
                                placeholder={
                                    isProcessing || streamingMessageId 
                                    ? "NeuroDesk está respondiendo..." 
                                    : "Escribe tu problema o consulta..."
                                }
                                className="w-full bg-transparent border-none focus:ring-0 text-white text-sm resize-none h-10 max-h-32 py-2 px-2 outline-none disabled:opacity-50"
                                rows={1}
                                disabled={isProcessing || !!streamingMessageId}
                            />
                        </div>

                        <button
                            onMouseDown={startRecording}
                            onMouseUp={stopRecording}
                            onMouseLeave={stopRecording}
                            disabled={isProcessing || !!streamingMessageId}
                            className={`p-3 rounded-xl transition-all duration-200 shadow-lg ${
                                isRecording
                                    ? 'bg-red-500 text-white scale-110 shadow-red-500/30'
                                    : (isProcessing || streamingMessageId)
                                    ? 'bg-white/5 text-gray-400 opacity-50 cursor-not-allowed'
                                    : 'bg-white/5 text-gray-400 hover:text-white hover:bg-white/10'
                            }`}
                        >
                            {isRecording ? <StopCircle className="w-6 h-6 animate-pulse" /> : <Mic className="w-6 h-6" />}
                        </button>

                        <button
                            onClick={() => sendMessage(input)}
                            disabled={!input.trim() || isProcessing || !!streamingMessageId}
                            className="p-3 rounded-xl bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors shadow-lg shadow-blue-900/20"
                        >
                            <Send className="w-5 h-5" />
                        </button>
                    </div>
                    <div className="text-center mt-2 text-[10px] text-gray-600">
                        NeuroDesk puede cometer errores. Verifica la información sensible.
                        {(isProcessing || streamingMessageId) && " ⏳ Procesando..."}
                    </div>
                </div>
            </div>
        </div>
    );
};