# 🛡️ NeuroDesk: Organizational Immune System

<div align="center">
  <img src="neurodesk-frontend/public/logo-shield.png" alt="NeuroDesk Logo" width="120" />
  <br />
  <h1>NeuroDesk AI</h1>
  <p><strong>Resiliencia Técnica + Protección del Bienestar Humano</strong></p>
  
  ![Azure](https://img.shields.io/badge/Cloud-Microsoft%20Azure-0078D4?style=for-the-badge&logo=microsoft-azure)
  ![AI](https://img.shields.io/badge/AI-Semantic%20Kernel-bf04c9?style=for-the-badge)
  ![Python](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)
  ![React](https://img.shields.io/badge/Frontend-React%20Vite-61DAFB?style=for-the-badge&logo=react)
</div>

---

## 📖 Introducción

**El problema:** En el entorno corporativo actual, los equipos de TI y Recursos Humanos operan en silos. Cuando un sistema crítico falla, la presión recae sobre el empleado. El soporte técnico tradicional resuelve el ticket, pero ignora el costo humano. El resultado es un aumento silencioso del **Burnout**, rotación de personal y errores operativos graves.

**La solución:** **NeuroDesk** es el primer **Sistema Inmunológico Organizacional**. Es una plataforma agéntica impulsada por IA que fusiona la resolución técnica autónoma con la detección proactiva de saturación laboral.

No es solo un chatbot; es un orquestador que:
1.  **Escucha:** Procesa voz y texto con análisis de sentimiento en tiempo real.
2.  **Diagnostica:** Cruza datos de incidentes técnicos con métricas de carga laboral (HR).
3.  **Actúa:** Ejecuta automatizaciones reales en la infraestructura de Azure (Runbooks) o sugiere pausas operativas para proteger al usuario.

---

## 🏗️ Arquitectura del Sistema

NeuroDesk utiliza una arquitectura **Cloud-Native** sobre Azure, implementando el patrón de **Multi-Agent Orchestration** con Semantic Kernel.

![Arquitectura de NeuroDesk](docs/architecture_diagram.png)

### Flujo de Datos:
1.  **Ingesta Multimodal:** El usuario interactúa vía Voz (Azure Speech) o Texto desde el Frontend React.
2.  **Gateway de Seguridad:** FastAPI recibe la solicitud y la pasa por **Azure Content Safety** para filtrar toxicidad.
3.  **Análisis Emocional:** **Azure AI Language** determina el sentimiento (Enojo, Frustración, Calma) para ajustar el tono de la IA.
4.  **Orquestación (Cerebro):** **Microsoft Semantic Kernel** con **GPT-4o** analiza la intención y selecciona el Plugin adecuado.
5.  **Ejecución de Agentes:**
    *   **HR Agent:** Consulta métricas en **Blob Storage** y **Cosmos DB**.
    *   **Policy Agent (RAG):** Busca normativas en **Azure AI Search**.
    *   **IT Agent:** Dispara Runbooks reales en **Azure Automation**.
6.  **Auditoría:** Cada decisión se registra en un Ledger inmutable en **Cosmos DB**.

---

## ☁️ Servicios de Azure Utilizados

Este proyecto demuestra una integración profunda del ecosistema Azure:

| Servicio | Uso en NeuroDesk |
|----------|------------------|
| **Azure OpenAI Service** | Motor de razonamiento (GPT-4o) y generación de Embeddings (text-embedding-3-small). |
| **Azure AI Search** | Memoria a largo plazo (RAG) para búsqueda vectorial de políticas y manuales. |
| **Azure Cosmos DB** | Base de datos NoSQL para persistencia de tickets y Ledger de Auditoría (Logs). |
| **Azure Automation** | Ejecución de scripts PowerShell reales (Runbooks) para remediación técnica (reinicios, limpieza, etc.). |
| **Azure Speech Services** | Transcripción (STT) y Síntesis de voz (TTS) neuronal para accesibilidad. |
| **Azure AI Language** | Análisis de sentimiento para detectar frustración y modular la empatía del agente. |
| **Azure Content Safety** | Guardarraíles de IA Responsable para bloquear contenido dañino o ataques (Jailbreak). |
| **Azure Blob Storage** | Almacenamiento de datos maestros (HR) y evidencias de logs. |
| **Azure Logic Apps** | Orquestación de escalado humano (envío de alertas/emails a gerencia). |
| **Azure Document Intelligence** | OCR para extraer información de manuales en PDF/Imágenes durante la ingesta. |
| **Managed Identities** | Seguridad Zero-Trust para la comunicación entre servicios backend. |

---

## ✨ Características Clave

### 1. Detección de Riesgo "Human-in-the-Loop"
El sistema no solo ve "Error 500". Ve que el usuario "Frank" lleva 290 horas trabajadas este mes y tiene 3 tickets críticos hoy.
*   **Resultado:** En lugar de solo reiniciar el servidor, NeuroDesk sugiere aplicar la *Política de Desconexión*.

### 2. Automatización Real (No Simulada)
A diferencia de otras demos, NeuroDesk ejecuta **Runbooks de PowerShell reales** en Azure Automation:
*   `NeuroDesk-Self-Heal-Restart`: Reinicia Web Apps.
*   `NeuroDesk-Generate-Upload-Link`: Genera tokens SAS temporales para subida segura.
*   `NeuroDesk-Get-Activity-Logs`: Audita la suscripción en tiempo real.

### 3. IA Responsable y Ética
*   **Sanitización de Lenguaje:** El sistema tiene prohibido usar términos clínicos (ej. "depresión"), reemplazándolos por lenguaje operativo ("alta carga").
*   **Auditoría Completa:** Cada interacción queda registrada.
*   **Privacidad:** Los datos sensibles se manejan con IDs internos.

---

## 🚀 Instalación y Despliegue

### Prerrequisitos
*   Python 3.10+
*   Node.js 18+
*   Cuenta de Azure con suscripción activa.
*   Azure CLI (`az login`).

### 1. Configuración del Backend

```bash
# 1. Clonar el repositorio
git clone https://github.com/franco-cristian/neurodesk.git
cd neurodesk

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # o .\venv\Scripts\activate en Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
# Copia el archivo .env.example a .env y rellena tus credenciales de Azure
cp .env.example .env

# 5. Inicializar Datos (Carga HR, Vectores y Tickets a la Nube)
python init_data.py
```

### 2. Configuración del Frontend

```bash
cd neurodesk-frontend

# 1. Instalar dependencias
npm install

# 2. Iniciar servidor de desarrollo
npm run dev
```

### 3. Ejecución

1.  Inicia el Backend: `uvicorn src.api.main:app --reload`
2.  Abre el Frontend: `http://localhost:5173`

---

## 🧪 Guía de Demostración

El sistema incluye un modo de **Login Simulado** para demostrar diferentes perfiles sin depender de múltiples cuentas de Microsoft activas.

### Escenario A: Burnout Crítico
1.  Loguearse como **"Cristian Franko (UTN)"**.
2.  **Acción:** Usar el micrófono y decir: *"¡Odio este sistema, nada funciona y tengo mil cosas que entregar!"*.
3.  **Resultado:**
    *   Sentiment: Negativo 😡.
    *   Riesgo HR: Alto (detecta sobrecarga en CSV).
    *   **Respuesta:** Empática. Sugiere pausa y NO ejecuta acciones técnicas complejas para no estresar más.

### Escenario B: Falla Técnica Pura
1.  Loguearse como **"Franco O. (Dev)"**.
2.  **Acción:** Escribir: *"Todo está lento, necesito reiniciar el servicio web"*.
3.  **Resultado:**
    *   Riesgo HR: Bajo.
    *   **Acción:** Ejecuta `NeuroDesk-Self-Heal-Restart` en Azure.
    *   **Frontend:** Muestra spinner y confirma con ID de Job real.

### Escenario C: Auditoría y Logs
1.  Loguearse como **"Cristian F. (Admin)"**.
2.  **Acción:** Escribir: *"Necesito subir los logs del error"*.
3.  **Resultado:**
    *   Ejecuta `NeuroDesk-Generate-Upload-Link`.
    *   Devuelve un Widget visual para subir archivos reales a Blob Storage.

---

## 📂 Estructura del Proyecto

```text
neurodesk/
├── infra/                  # IaC con Bicep para desplegar recursos
├── neurodesk-frontend/     # SPA React + Vite + Tailwind
│   ├── src/
│   │   ├── components/     # Dashboard, Chat, Widgets
│   │   ├── store/          # Estado global (Zustand)
│   │   └── ...
├── src/                    # Backend Python FastAPI
│   ├── api/                # Endpoints (REST)
│   ├── data/               # Datasets semilla (HR, Políticas)
│   ├── models/             # Modelos Pydantic
│   ├── services/           # Lógica de Negocio
│   │   ├── plugins/        # Agentes Semánticos (HR, IT, Policy)
│   │   ├── chat_orchestrator.py  # Cerebro principal (Semantic Kernel)
│   │   ├── safety_guard.py       # Filtro de Contenidos
│   │   └── ...
│   └── utils/              # Loggers y helpers
├── init_data.py            # Script ETL (Carga inicial de datos)
└── requirements.txt        # Dependencias Python
```

---

## 🤝 IA Responsable y Seguridad

NeuroDesk ha sido diseñado siguiendo los principios de IA Responsable de Microsoft:

1.  **Transparencia:** La interfaz muestra en tiempo real qué "pensamiento" está teniendo la IA y qué herramienta está ejecutando (Panel "Live Intelligence").
2.  **Seguridad de Datos:** El backend utiliza `DefaultAzureCredential` para no manejar secretos en código. La autenticación de servicios es vía Managed Identity.
3.  **Control Humano:** El sistema incluye un mecanismo de escalado (`Logic App`) que se activa automáticamente ante situaciones de crisis o ambigüedad.

---

## 👥 Equipo

*   **Cristian Franko** - Arquitectura Cloud & Backend AI
*   **Fabio Arias** - Frontend & AI

---

> *Este proyecto fue desarrollado para la Microsoft Azure Hackathon 2025.*