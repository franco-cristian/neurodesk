import pandas as pd
import asyncio
import random
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config import settings

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.contents import ChatHistory

# --- CONFIGURACIÓN DE USUARIOS REALES (DEMO) ---
REAL_USERS_CONFIG = [
    {
        "email": "cristian_franko@ca.frre.utn.edu.ar",
        "name": "Cristian Franko (UTN)",
        "position": "Production Lead",
        "department": "Production",
        "scenario": "BURNOUT_CRITICO",  # Caso de Estrés
        "satisfaction": 0.2,
        "hours": 290,
        "projects": 8
    },
    {
        "email": "franc0_o@outlook.com",
        "name": "Franco O. (Dev)",
        "position": "Sr. Software Engineer",
        "department": "IT/IS",
        "scenario": "FALLA_TECNICA",    # Caso Técnico Puro
        "satisfaction": 0.8,
        "hours": 160,
        "projects": 2
    },
    {
        "email": "fabio-adrian-arias@hotmail.com.ar",
        "name": "Fabio Arias",
        "position": "Sales Manager",
        "department": "Sales",
        "scenario": "ACCESO_BLOQUEADO", # Caso de Identidad
        "satisfaction": 0.6,
        "hours": 170,
        "projects": 3
    },
    {
        "email": "cristian_franko@hotmail.com",
        "name": "Cristian F. (Admin)",
        "position": "Database Admin",
        "department": "IT/IS",
        "scenario": "NORMAL",           # Caso de Control
        "satisfaction": 0.9,
        "hours": 150,
        "projects": 1
    }
]

# Configuración de generación
NUM_AI_TICKETS = 30 # Cantidad de tickets de relleno generados por IA
MODEL_ID = "chat-gpt"

async def generate_ai_description(kernel, employee):
    """Usa Azure OpenAI para escribir una queja realista basada en el rol"""
    chat_service = kernel.get_service(MODEL_ID)
    
    category = random.choice(["Hardware", "Software", "Access", "Network"])
    
    prompt = f"""
    Eres un empleado corporativo real.
    Tu Rol: {employee['Position']}
    Departamento: {employee['Department']}
    Problema: Tienes un fallo de tipo {category}.
    
    Tarea: Escribe SOLAMENTE la descripción corta (1 o 2 frases) para un ticket de soporte.
    Estilo: Natural, a veces con faltas leves de ortografía, a veces urgente, a veces amable.
    Ejemplo: "Mi outlook no conecta y tengo reunión en 5 min!!"
    """
    
    history = ChatHistory()
    history.add_user_message(prompt)
    
    # Temperatura alta para variedad
    settings_ai = AzureChatPromptExecutionSettings(service_id=MODEL_ID, temperature=0.85, max_tokens=60)
    
    try:
        response = await chat_service.get_chat_message_content(history, settings_ai)
        return str(response).strip().replace('"', ''), category
    except Exception as e:
        print(f"⚠️ Error IA: {e}")
        return "Error desconocido en el sistema.", category

def setup_hr_data():
    """Prepara el archivo de empleados (HR) inyectando los usuarios reales"""
    print("🔄 1. Preparando Base de Datos de RRHH...")
    
    if not os.path.exists(settings.HR_DATA_PATH): # Intentamos leer el enriched o el raw
        # Si no existe enriched, buscamos el raw en el mismo dir
        raw_path = settings.DATA_DIR / "HRDataset_v14.csv"
        if not raw_path.exists():
            print(f"❌ ERROR: No encuentro {raw_path}")
            return [], []
        df = pd.read_csv(raw_path)
    else:
        df = pd.read_csv(settings.HR_DATA_PATH)

    records = df.to_dict('records')
    
    # Reemplazar los primeros N registros con nuestros usuarios reales
    for i, real_user in enumerate(REAL_USERS_CONFIG):
        # Sobrescribimos datos del registro existente
        records[i]['Employee_Name'] = real_user['name']
        records[i]['Email'] = real_user['email']
        records[i]['EmpID'] = 90000 + i  # IDs especiales
        records[i]['Position'] = real_user['position']
        records[i]['Department'] = real_user['department']
        records[i]['EmpSatisfaction'] = int(real_user['satisfaction'] * 5)
        records[i]['Average_Monthly_Hours'] = real_user['hours']
        records[i]['SpecialProjectsCount'] = real_user['projects']

    # Para el resto, generar emails falsos si no los tienen
    for i in range(len(REAL_USERS_CONFIG), len(records)):
        if 'Email' not in records[i] or pd.isna(records[i].get('Email')):
            name_parts = str(records[i]['Employee_Name']).split(',')
            if len(name_parts) >= 2:
                # Formato: apellido.nombre@neurodesk.ai
                email = f"{name_parts[0].strip().lower()}.{name_parts[1].strip().lower().split()[0]}@neurodesk.ai"
                records[i]['Email'] = email
            else:
                records[i]['Email'] = f"user{records[i]['EmpID']}@neurodesk.ai"

    # Guardar HR Enriched
    df_final = pd.DataFrame(records)
    df_final.to_csv(settings.HR_DATA_PATH, index=False)
    print(f"✅ HR Data guardado en {settings.HR_DATA_PATH}")
    
    return records

def generate_demo_tickets():
    """Genera los tickets FIJOS para los casos de uso de la Demo"""
    print("🎭 2. Generando Escenarios de Demo (Deterministas)...")
    tickets = []
    
    for i, user in enumerate(REAL_USERS_CONFIG):
        uid = str(90000 + i)
        
        # CASO 1: BURNOUT CRÍTICO (Cristian UTN) -> Historial de quejas
        if user['scenario'] == "BURNOUT_CRITICO":
            tickets.append({
                "ticket_id": "INC-BUR-001",
                "user_id": uid, "user_email": user['email'],
                "category": "Access", "subject": "Acceso fin de semana",
                "description": "Necesito permisos para entrar al servidor el domingo, no llego con la entrega.",
                "priority": "High", "status": "Closed",
                "created_at": (datetime.utcnow() - timedelta(days=2)).isoformat()
            })
            tickets.append({
                "ticket_id": "INC-BUR-002",
                "user_id": uid, "user_email": user['email'],
                "category": "Software", "subject": "Sistema lento",
                "description": "Todo va muy lento y estoy perdiendo tiempo valioso. ¡Necesito solución ya!",
                "priority": "Critical", "status": "Open",
                "created_at": (datetime.utcnow() - timedelta(hours=4)).isoformat()
            })

        # CASO 2: FALLA TÉCNICA (Franco) -> Problema específico
        elif user['scenario'] == "FALLA_TECNICA":
            tickets.append({
                "ticket_id": "INC-TEC-101",
                "user_id": uid, "user_email": user['email'],
                "category": "Network", "subject": "VPN Error 800",
                "description": "La VPN me desconecta cada vez que intento subir código al repo.",
                "priority": "Medium", "status": "Open",
                "created_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()
            })

        # CASO 3: ACCESO (Fabio) -> Password
        elif user['scenario'] == "ACCESO_BLOQUEADO":
            tickets.append({
                "ticket_id": "INC-ACC-202",
                "user_id": uid, "user_email": user['email'],
                "category": "Access", "subject": "Cuenta Bloqueada",
                "description": "Ingresé mal mi clave 3 veces y se bloqueó el usuario.",
                "priority": "High", "status": "Open",
                "created_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat()
            })
            
        # Cristian F (Normal) no tiene tickets recientes problemáticos

    return tickets

async def main():
    # 1. Configurar Kernel para IA
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(
        service_id=MODEL_ID,
        deployment_name=settings.AOAI_DEPLOYMENT,
        endpoint=settings.AOAI_ENDPOINT,
        api_key=settings.AOAI_KEY,
    ))

    # 2. Preparar Datos Maestros
    hr_records = setup_hr_data()
    if not hr_records: return

    # 3. Obtener Tickets de Demo
    all_tickets = generate_demo_tickets()

    # 4. Generar Relleno con IA
    print(f"🤖 3. Generando {NUM_AI_TICKETS} tickets de relleno con Azure OpenAI...")
    
    # Filtramos para no usar los usuarios de la demo en el relleno
    background_employees = hr_records[len(REAL_USERS_CONFIG):]
    
    for i in range(NUM_AI_TICKETS):
        emp = random.choice(background_employees)
        
        desc, cat = await generate_ai_description(kernel, emp)
        
        ticket = {
            "ticket_id": f"AI-{random.randint(10000, 99999)}",
            "user_id": str(emp['EmpID']),
            "user_email": emp['Email'],
            "category": cat,
            "subject": f"Incidencia de {cat}",
            "description": desc,
            "priority": random.choice(["Low", "Medium", "High"]),
            "status": random.choice(["Open", "Closed", "In Progress"]),
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat()
        }
        all_tickets.append(ticket)
        
        if (i+1) % 5 == 0:
            print(f"   ... {i+1} tickets generados.")

    # 5. Guardar todo
    df_tickets = pd.DataFrame(all_tickets)
    df_tickets.to_csv(settings.TICKETS_DATA_PATH, index=False)
    
    print("\n" + "="*50)
    print(f"✅ GENERACIÓN COMPLETADA")
    print(f"📂 Tickets guardados en: {settings.TICKETS_DATA_PATH}")
    print(f"📊 Total Tickets: {len(all_tickets)}")
    print(f"   - Escenarios Demo: {len(all_tickets) - NUM_AI_TICKETS}")
    print(f"   - Relleno IA: {NUM_AI_TICKETS}")
    print("="*50)
    print("👉 AHORA: Ejecuta 'python init_data.py' para subir esto a Cosmos DB.")

if __name__ == "__main__":
    asyncio.run(main())