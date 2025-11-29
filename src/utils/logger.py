import logging
import sys
from typing import Optional

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configura un logger profesional con formato estructurado.
    """
    logger = logging.getLogger(name)
    
    # Evitar duplicar handlers si se llama varias veces
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(level)

    # Formato: [HORA] [LEVEL] [MODULO] Mensaje
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Salida a Consola (Stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Logger global para la aplicación
app_logger = setup_logger("NeuroDesk")