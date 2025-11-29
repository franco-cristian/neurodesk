/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        neuro: {
          900: '#0a0f1c', // Fondo principal (Casi negro azulado)
          800: '#111827', // Paneles
          700: '#1f2937', // Bordes
          500: '#3b82f6', // Primario
          400: '#60a5fa', // Acento
          cyan: '#06b6d4', // Neón para acciones de IA
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}