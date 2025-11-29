import React from 'react';
import { motion } from 'framer-motion';
import {
  Terminal,
  Database,
  TrendingUp,
  ShieldAlert,
  ChevronRight,
  Lock
} from 'lucide-react';
import { useNeuroStore } from '../store/useNeuroStore';
import type { UserProfile } from '../store/useNeuroStore';

// Configuración de Roles
const DEMO_PERSONAS: (UserProfile & { icon: React.ElementType, color: string })[] = [
  {
    id: "90001",
    name: "Franco O.",
    role: "Ingeniero de Software",
    department: "IT",
    email: "franc0_o@outlook.com",
    icon: Terminal,
    color: "from-blue-500 to-cyan-400"
  },
  {
    id: "90000",
    name: "Cristian Franco",
    role: "Líder de Producción",
    department: "Operaciones",
    email: "cristian_franko@ca.frre.utn.edu.ar",
    icon: ShieldAlert,
    color: "from-orange-500 to-red-400"
  },
  {
    id: "90002",
    name: "Fabio Arias",
    role: "Desarrollador Frontend",
    department: "IT",
    email: "fabio-adrian-arias@hotmail.com.ar",
    icon: TrendingUp,
    color: "from-emerald-500 to-teal-400"
  },
  {
    id: "90003",
    name: "Cristian F. (Admin)",
    role: "Admin de Base de Datos",
    department: "Infraestructura",
    email: "cristian_franko@hotmail.com",
    icon: Database,
    color: "from-violet-500 to-purple-400"
  }
];

export const LoginScreen: React.FC = () => {
  const login = useNeuroStore((state) => state.login);

  const handleLogin = (user: UserProfile) => {
    login(user);
  };

  return (
    <div className="min-h-screen w-full bg-[#050505] flex relative overflow-hidden font-sans text-gray-100">

      {/* --- FONDO AMBIENTAL --- */}
      <div className="fixed inset-0 z-0">
        {/* Capa base negra */}
        <div className="absolute inset-0 bg-black z-0" />

        {/* Imagen con visibilidad */}
        <img
          src="/bg-neural.jpg"
          className="w-full h-full object-cover opacity-50 mix-blend-screen absolute inset-0 z-10 transition-opacity duration-1000"
          alt="Fondo Neural"
        />

        {/* Gradiente suave */}
        <div className="absolute inset-0 bg-gradient-to-r from-black/0 via-black/10 to-transparent z-20" />
      </div>

      {/* --- CONTENIDO PRINCIPAL --- */}
      <div className="relative z-10 w-full flex flex-col lg:flex-row h-screen">

        {/* IZQUIERDA: Branding */}
        <div className="hidden lg:flex flex-col justify-between w-[45%] p-12 lg:p-16 border-r border-white/10 bg-black/20 backdrop-blur-sm">
          <div>
            <div className="flex items-center gap-4 mb-8">
              <img
                src="/logo-shield.png"
                alt="Logo"
                className="w-16 h-16 object-contain drop-shadow-[0_0_15px_rgba(59,130,246,0.5)]"
                onError={(e) => e.currentTarget.style.display = 'none'}
              />
              <h1 className="text-3xl font-bold tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-200">
                NeuroDesk
              </h1>
            </div>

            <div className="h-1 w-24 bg-gradient-to-r from-blue-500 to-transparent rounded-full mb-10" />

            <h2 className="text-5xl lg:text-6xl font-extrabold leading-tight tracking-tight text-white mb-8">
              Sistema <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-400 to-purple-400">
                Inmunológico Organizacional
              </span>
            </h2>

            <p className="text-xl text-gray-300 max-w-lg leading-relaxed font-light border-l-4 border-blue-500/50 pl-6">
              Plataforma agéntica autónoma que fusiona la resolución técnica (IT) con el bienestar humano (HR) en tiempo real.
            </p>
          </div>

          <div className="flex items-center gap-3 text-xs text-neuro-400 font-mono tracking-wider opacity-80">
            <Lock className="w-4 h-4" />
            ACCESO SEGURO :: MICROSOFT :: AZURE AI
          </div>
        </div>

        {/* DERECHA: Formulario de Acceso */}
        <div className="w-full lg:w-[55%] flex items-center justify-center p-8 lg:p-24">
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="w-full max-w-md"
          >
            <div className="mb-10">
              <h3 className="text-3xl font-bold text-white mb-2">Verificación de Identidad</h3>
              <p className="text-gray-400">Selecciona un perfil para simular el contexto de la sesión.</p>
            </div>

            <div className="space-y-4">
              {DEMO_PERSONAS.map((persona, index) => {
                const Icon = persona.icon;
                return (
                  <motion.button
                    key={persona.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    onClick={() => handleLogin(persona)}
                    className="group w-full flex items-center p-4 rounded-xl border border-white/5 bg-neuro-800/40 hover:bg-neuro-800/80 hover:border-blue-500/50 hover:shadow-[0_0_20px_rgba(59,130,246,0.15)] transition-all duration-300"
                  >
                    {/* Icono del Rol */}
                    <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${persona.color} p-[1px] shadow-lg`}>
                      <div className="w-full h-full bg-neuro-900 rounded-[7px] flex items-center justify-center">
                        <Icon className="w-6 h-6 text-gray-200 group-hover:text-white transition-colors" />
                      </div>
                    </div>

                    {/* Información */}
                    <div className="ml-5 flex-1 text-left">
                      <div className="flex items-center justify-between">
                        <h4 className="text-lg font-semibold text-gray-100 group-hover:text-blue-300 transition-colors">
                          {persona.name}
                        </h4>
                      </div>
                      <p className="text-sm text-gray-500 mt-1 font-medium group-hover:text-gray-400">
                        {persona.role} <span className="mx-1 text-gray-700">|</span> {persona.department}
                      </p>
                    </div>

                    {/* Flecha */}
                    <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-blue-500/20 transition-colors">
                      <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-blue-400" />
                    </div>
                  </motion.button>
                );
              })}
            </div>

            <div className="mt-16 flex items-center justify-center gap-2 opacity-30">
              <span className="h-1 w-1 rounded-full bg-white"></span>
              <span className="text-[10px] uppercase tracking-[0.2em] text-white font-semibold">Powered by Microsoft Azure</span>
              <span className="h-1 w-1 rounded-full bg-white"></span>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};