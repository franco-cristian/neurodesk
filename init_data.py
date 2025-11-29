import pandas as pd
import uuid
import time
import os
import glob
from datetime import datetime
from tqdm import tqdm

# Importamos los servicios del núcleo
from src.services.search_engine import search_engine
from src.services.ocr_service import ocr_service
from src.services.ticket_store import ticket_store
from src.config import settings
from src.utils.logger import app_logger

# --- CONFIGURACIÓN DE INGESTA ---
CHUNK_SIZE = 500       # Tamaño del fragmento de texto (caracteres)
CHUNK_OVERLAP = 100    # Solapamiento para no perder contexto entre cortes
SUPPORTED_EXTENSIONS = ['*.txt', '*.pdf', '*.png', '*.jpg', '*.jpeg', '*.tiff']

def chunk_text_with_vectors(text: str, source_name: str, category: str) -> list:
    """
    Corta el texto en ventanas deslizantes y genera vectores (Embeddings) 
    para cada fragmento usando Azure OpenAI.
    """
    chunks = []
    text_len = len(text)
    start = 0
    
    app_logger.info(f"🧠 Vectorizando documento '{source_name}' ({text_len} caracteres)...")
    
    while start < text_len:
        # Definir ventana de corte
        end = start + CHUNK_SIZE
        
        # Ajuste inteligente: intentar no cortar palabras a la mitad
        if end < text_len:
            # Retroceder hasta encontrar un espacio si estamos a mitad de palabra
            while end > start and text[end] != ' ':
                end -= 1
            if end == start: # Si no hay espacios (ej: url larga), cortar forzado
                end = start + CHUNK_SIZE
        
        # Extraer contenido
        chunk_content = text[start:end].strip()
        
        # Ignorar fragmentos irrelevantes (vacíos o muy cortos)
        if len(chunk_content) > 30: 
            try:
                # 1. Generar Vector (Llamada a Azure OpenAI)
                vector = search_engine.generate_embedding(chunk_content)
                
                if vector:
                    # 2. Crear Documento para Indexar
                    chunks.append({
                        "id": str(uuid.uuid4()),
                        "content": chunk_content,
                        "contentVector": vector, # Vector de 1536 dimensiones
                        "category": category,
                        "source": source_name
                    })
            except Exception as e:
                app_logger.error(f"⚠️ Error vectorizando chunk: {e}")
        
        # Avanzar el cursor (Sliding Window con Overlap)
        start = end - CHUNK_OVERLAP
        
        # Evitar bucle infinito si el texto es muy corto
        if start >= text_len: break
    
    return chunks

def process_knowledge_base():
    """
    ETL RAG: Escanea src/data, aplica OCR, Chrunking y Vectorización.
    """
    print("\n--- 🧠 FASE 1: CONSTRUCCIÓN DE MEMORIA RAG (VECTORES + OCR) ---")
    
    # 1. Crear Índice en Azure AI Search
    search_engine.create_vector_index()
    time.sleep(2)
    
    # 2. Buscar archivos en la carpeta de datos
    data_path = str(settings.DATA_DIR)
    found_files = []
    for ext in SUPPORTED_EXTENSIONS:
        found_files.extend(glob.glob(os.path.join(data_path, ext)))
    
    if not found_files:
        app_logger.warning(f"⚠️ No se encontraron documentos en {data_path}")
        return

    app_logger.info(f"📂 Archivos detectados para ingesta: {len(found_files)}")
    
    total_chunks_uploaded = 0

    # 3. Procesar cada archivo
    for file_path in found_files:
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        
        # A. Extracción de Texto (OCR vs Texto Plano)
        raw_text = ""
        if file_ext in ['.txt', '.csv', '.md']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_text = f.read()
            except UnicodeDecodeError:
                app_logger.warning(f"⚠️ Error de encoding en {filename}, intentando latin-1")
                with open(file_path, 'r', encoding='latin-1') as f:
                    raw_text = f.read()
        else:
            # Es binario (PDF/Imagen) -> Usar OCR Service
            app_logger.info(f"👁️ Procesando OCR para: {filename}")
            raw_text = ocr_service.extract_text_from_file(file_path)

        if not raw_text or len(raw_text) < 10:
            app_logger.warning(f"⏩ Saltando {filename}: Sin contenido extraíble.")
            continue

        # B. Categorización Automática (Heurística simple para Demo)
        category = "General"
        lower_name = filename.lower()
        if "politic" in lower_name or "policy" in lower_name: category = "Políticas HR"
        elif "manual" in lower_name or "guia" in lower_name: category = "Manual Técnico"
        elif "seguridad" in lower_name: category = "Seguridad TI"

        # C. Chunking + Vectorización
        vector_docs = chunk_text_with_vectors(raw_text, filename, category)
        
        # D. Subida a la Nube (Batch)
        if vector_docs:
            search_engine.upload_documents(vector_docs)
            total_chunks_uploaded += len(vector_docs)
            print(f"   ✅ {filename}: {len(vector_docs)} vectores indexados.")
        else:
            app_logger.warning(f"   ⚠️ {filename}: No se generaron vectores válidos.")

    print(f"✨ Ingesta RAG Finalizada. Total vectores en memoria: {total_chunks_uploaded}")

def load_historical_tickets():
    """
    Carga el historial de tickets desde CSV a Cosmos DB.
    """
    print("\n--- 💾 FASE 2: CARGA DE HISTORIAL OPERATIVO (COSMOS DB) ---")
    
    csv_path = settings.TICKETS_DATA_PATH
    if not csv_path.exists():
        app_logger.error(f"❌ No se encontró el archivo de tickets: {csv_path}")
        return

    try:
        df = pd.read_csv(csv_path)
        tickets = df.to_dict('records')
        
        success_count = 0
        exists_count = 0
        
        # Usamos tqdm para mostrar barra de progreso
        print(f"🔄 Sincronizando {len(tickets)} tickets con la nube...")
        for ticket in tqdm(tickets, unit="ticket"):
            
            # Normalización de ID
            if 'ticket_id' in ticket:
                ticket['id'] = ticket['ticket_id']
            else:
                ticket['id'] = str(uuid.uuid4())
            
            # Timestamp
            if 'created_at' not in ticket:
                ticket['created_at'] = datetime.utcnow().isoformat()

            # Partition Key debe ser string
            if 'user_id' in ticket:
                ticket['user_id'] = str(ticket['user_id'])
            
            # Intentar crear
            if ticket_store.create_ticket(ticket):
                success_count += 1
            else:
                exists_count += 1
        
        print(f"📊 Resumen Tickets: {success_count} Nuevos | {exists_count} Ya Existían/Error")

    except Exception as e:
        app_logger.error(f"❌ Error crítico cargando tickets: {e}")

if __name__ == "__main__":
    print("""
    ===================================================
       NEURODESK: SYSTEM INITIALIZATION & DATA SEEDER
       Modo: REAL PRODUCTION (Azure AI + Cosmos DB)
    ===================================================
    """)
    
    # 1. Validar Entorno
    try:
        settings.validate()
        print("✅ Variables de entorno validadas.")
    except Exception as e:
        print(f"❌ {e}")
        exit(1)

    # 2. Ejecutar Pipelines
    process_knowledge_base()  # RAG
    load_historical_tickets() # DB
    
    print("\n🏁 Inicialización completada exitosamente.")
    print("👉 Ahora puedes iniciar el backend: uvicorn src.api.main:app --reload")