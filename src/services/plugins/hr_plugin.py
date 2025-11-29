from semantic_kernel.functions import kernel_function
from typing import Annotated
from src.services.data_analyst import data_analyst

class HRAgentPlugin:
    """
    Plugin especializado en consultar información de Capital Humano.
    No accede a archivos, consulta al servicio DataAnalyst.
    """

    @kernel_function(
        description="Obtiene métricas de carga de trabajo, satisfacción y proyectos de un empleado.",
        name="analyze_workload_metrics"
    )
    def analyze_workload_metrics(
        self, 
        user_identifier: Annotated[str, "El email corporativo o ID del empleado"]
    ) -> str:
        """
        Consulta el perfil del empleado en tiempo real cruzando datos de Blob Storage.
        """
        print(f"👥 [HR AGENT] Consultando métricas para: {user_identifier}")
        
        # Delegación estricta al servicio de datos
        metrics = data_analyst.get_employee_metrics(user_identifier)
        
        if "error" in metrics:
            if metrics["error"] == "HR Database Offline":
                return "ERROR DE SISTEMA: La base de datos de RRHH no está accesible en Azure Blob Storage."
            return f"NO ENCONTRADO: No existen registros activos para el usuario '{user_identifier}'."

        # Interpretación de Negocio (Business Logic) para el LLM
        # Convertimos los datos crudos en una narrativa útil para el Agente
        
        status_flag = "Estable"
        if metrics['satisfaction'] < 3.0 and metrics['projects'] > 5:
            status_flag = "RIESGO DE BURNOUT (Alta carga + Baja satisfacción)"
        elif metrics['monthly_hours'] > 220:
             status_flag = "SOBRECARGA HORARIA CRÍTICA"
        
        # Formato estructurado para fácil lectura del LLM
        return (
            f"--- PERFIL DE EMPLEADO: {metrics['name']} ---\n"
            f"Rol: {metrics['position']} ({metrics['department']})\n"
            f"Manager: {metrics['manager']}\n"
            f"Estado Operativo: {status_flag}\n"
            f"📊 Métricas Clave:\n"
            f"   - Satisfacción: {metrics['satisfaction']}/5.0\n"
            f"   - Proyectos Activos: {metrics['projects']}\n"
            f"   - Promedio Horas/Mes: {metrics['monthly_hours']}\n"
            f"   - Ausencias recientes: {metrics['absences']}\n"
            f"   - Última revisión: {metrics['last_review']}\n"
            "------------------------------------------------"
        )