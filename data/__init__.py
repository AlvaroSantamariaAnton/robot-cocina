# Paquete 'data' - expone funciones útiles de init_db para importaciones más robustas.
from .init_db import conectar, reinicio_fabrica, inicializar_bd

__all__ = ["conectar", "reinicio_fabrica", "inicializar_bd"]
